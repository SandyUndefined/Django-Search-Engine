import logging
import time
from urllib.parse import urlencode, urlparse

from django.core.cache import cache
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect

from SearchEngine.search import bing, duck, ecosia, givewater, google, yahoo

logger = logging.getLogger(__name__)

SEARCH_PROVIDERS = (
    ("google", "Google", google),
    ("yahoo", "Yahoo", yahoo),
    ("duck", "DuckDuckGo", duck),
    ("ecosia", "Ecosia", ecosia),
    ("bing", "Bing", bing),
    ("givewater", "GiveWater", givewater),
)
THROTTLE_SECONDS = 2
RECENT_QUERY_LIMIT = 5
SAVED_QUERY_LIMIT = 8
SNIPPET_FETCH_LIMIT = 8
SNIPPET_TIMEOUT = 3
SNIPPET_CACHE_TTL = 60 * 60
CONTENT_FILTERS = {'articles': '', 'videos': ' video', 'docs': ' filetype:pdf'}
TIME_FILTERS = {'24h': ' past 24 hours', 'week': ' past week', 'month': ' past month'}


def _normalize_excludes(raw_exclude):
    if not raw_exclude:
        return []
    parts = [part.strip() for part in raw_exclude.replace("\n", ",").split(",")]
    return [p for p in parts if p]


def _build_cache_key(query, provider_keys):
    provider_fragment = ",".join(sorted(provider_keys)) or "all"
    safe_query = query.lower().replace(" ", "_")
    return f"search-results:{safe_query}:{provider_fragment}"


def _get_recent_queries(request):
    return request.session.get('recent_queries', [])


def _store_recent_query(request, query):
    recent = _get_recent_queries(request)
    if query in recent:
        recent.remove(query)
    recent.insert(0, query)
    request.session['recent_queries'] = recent[:RECENT_QUERY_LIMIT]


def _get_saved_searches(request):
    return request.session.get('saved_searches', [])


def _store_saved_search(request, search_entry):
    saved = _get_saved_searches(request)
    saved = [item for item in saved if item.get('search') != search_entry.get('search')]
    saved.insert(0, search_entry)
    request.session['saved_searches'] = saved[:SAVED_QUERY_LIMIT]


def _ensure_context_defaults(context):
    defaults = {
        'errors': {},
        'providers': [],
        'provider_results': [],
        'fused_results': [],
        'analytics': [],
        'analytics_map': {},
        'site_filter': '',
        'exclude_terms': [],
        'effective_query': context.get('query', ''),
        'fused_sort': 'consensus',
        'content_filter': '',
        'time_filter': '',
        'safe_mode': True,
    }
    for key, val in defaults.items():
        context.setdefault(key, val)
    return context


def _get_domain(url):
    try:
        return urlparse(url).netloc
    except Exception:
        return ''


def _fetch_snippet(url):
    cache_key = f"snippet:{url}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "accept-language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, timeout=SNIPPET_TIMEOUT, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            snippet = meta_desc["content"].strip()
        else:
            para = soup.find("p")
            snippet = para.get_text(strip=True) if para else ""
    except Exception:
        snippet = ""
    cache.set(cache_key, snippet, SNIPPET_CACHE_TTL)
    return snippet


def homepage(request):
    recent_queries = _get_recent_queries(request)
    provider_options = [{'key': key, 'label': label} for key, label, _ in SEARCH_PROVIDERS]
    return render(
        request,
        'home.html',
        {
            'recent_queries': recent_queries,
            'provider_options': provider_options,
            'saved_searches': _get_saved_searches(request),
        },
    )


def results(request):
    data = request.POST if request.method == "POST" else request.GET

    raw_query = data.get('search', '')
    query = raw_query.strip()
    if query == '':
        return redirect('Home')

    providers_param = data.getlist('providers')
    if not providers_param and data.get('providers'):
        providers_param = [p.strip() for p in data.get('providers').split(',') if p.strip()]
    requested_providers = providers_param or [key for key, _, _ in SEARCH_PROVIDERS]
    active_providers = [
        (key, label, fn)
        for key, label, fn in SEARCH_PROVIDERS
        if key in requested_providers
    ]
    if not active_providers:
        active_providers = list(SEARCH_PROVIDERS)
    provider_keys = [key for key, _, _ in active_providers]

    site_filter = data.get('site', '').strip()
    exclude_terms = _normalize_excludes(data.get('exclude', ''))
    content_filter = data.get('content', '')
    time_filter = data.get('time', '')
    safe_mode = data.get('safe', 'on') != 'off'
    fused_sort = data.get('fused_sort', 'consensus')
    query_parts = [query]
    if site_filter:
        query_parts.append(f"site:{site_filter}")
    if content_filter in CONTENT_FILTERS and CONTENT_FILTERS[content_filter]:
        query_parts.append(CONTENT_FILTERS[content_filter])
    if time_filter in TIME_FILTERS and TIME_FILTERS[time_filter]:
        query_parts.append(TIME_FILTERS[time_filter])
    if exclude_terms:
        query_parts.extend([f"-{term}" for term in exclude_terms])
    if safe_mode:
        query_parts.append("-adult -nsfw")
    effective_query = " ".join(query_parts).strip()

    cache_key = _build_cache_key(effective_query, provider_keys)
    throttle_key = f"search-throttle:{request.META.get('REMOTE_ADDR', 'anonymous')}"
    cached_results = cache.get(cache_key)
    if cache.get(throttle_key):
        if cached_results:
            return render(request, 'results.html', _ensure_context_defaults(cached_results))
        return redirect('Home')
    if cached_results:
        return render(request, 'results.html', _ensure_context_defaults(cached_results))
    cache.set(throttle_key, True, THROTTLE_SECONDS)

    context = {
        'errors': {},
        'query': query,
        'effective_query': effective_query,
        'providers': provider_keys,
        'provider_results': [],
        'site_filter': site_filter,
        'exclude_terms': exclude_terms,
        'analytics': [],
        'fused_results': [],
        'fused_sort': fused_sort,
        'content_filter': content_filter,
        'time_filter': time_filter,
        'safe_mode': safe_mode,
    }

    for key, label, provider in active_providers:
        start = time.perf_counter()
        try:
            links, text = provider(effective_query)
            results = list(zip(links, text))
            context['provider_results'].append(
                {'key': key, 'label': label, 'results': results, 'error': None}
            )
            context['analytics'].append(
                {
                    'key': key,
                    'label': label,
                    'result_count': len(results),
                    'duration_ms': round((time.perf_counter() - start) * 1000, 1),
                    'error': False,
                }
            )
        except Exception:
            logger.exception("Provider %s failed for query=%s", key, query)
            context['errors'][key] = "Temporarily unable to fetch results for this provider."
            context['provider_results'].append(
                {'key': key, 'label': label, 'results': [], 'error': context['errors'][key]}
            )
            context['analytics'].append(
                {
                    'key': key,
                    'label': label,
                    'result_count': 0,
                    'duration_ms': round((time.perf_counter() - start) * 1000, 1),
                    'error': True,
                }
            )

    context['analytics_map'] = {stat['key']: stat for stat in context['analytics']}
    for provider in context['provider_results']:
        provider['stat'] = context['analytics_map'].get(provider['key'])

    fused = {}
    for result in context['provider_results']:
        for link, title in result['results']:
            normalized = link.rstrip('/').lower()
            if normalized not in fused:
                fused[normalized] = {
                    'url': link,
                    'title': title,
                    'providers': set(),
                    'snippet': '',
                    'domain': _get_domain(link),
                }
            fused[normalized]['providers'].add(result['label'])
    fused_results = list(fused.values())
    fused_results.sort(key=lambda item: len(item['providers']), reverse=True)
    for item in fused_results[:SNIPPET_FETCH_LIMIT]:
        item['snippet'] = _fetch_snippet(item['url'])
    for item in fused_results:
        item['provider_count'] = len(item['providers'])
        item['providers_list'] = sorted(item['providers'])
    if fused_sort == 'domain':
        fused_results.sort(key=lambda item: (item['domain'] or '', item['title'] or ''))
    elif fused_sort == 'title':
        fused_results.sort(key=lambda item: (item['title'] or '', item['domain'] or ''))
    else:
        fused_results.sort(key=lambda item: (-item['provider_count'], item['domain'] or '', item['title'] or ''))
    context['fused_results'] = fused_results

    _store_recent_query(request, query)
    cache.set(cache_key, context, 45)
    return render(request, 'results.html', context)


def save_search(request):
    if request.method != "POST":
        return redirect('Home')
    query = request.POST.get('search', '').strip()
    if not query:
        return redirect('Home')
    site_filter = request.POST.get('site', '').strip()
    exclude_terms = _normalize_excludes(request.POST.get('exclude', ''))
    providers = request.POST.getlist('providers') or [
        p for p in (request.POST.get('providers_csv', '')).split(',') if p
    ]
    if not providers:
        providers = [key for key, _, _ in SEARCH_PROVIDERS]

    entry = {
        'search': query,
        'site': site_filter,
        'exclude': ",".join(exclude_terms),
        'providers': providers,
    }
    _store_saved_search(request, entry)

    params = [('search', query)]
    if site_filter:
        params.append(('site', site_filter))
    if exclude_terms:
        params.append(('exclude', ",".join(exclude_terms)))
    for p in providers:
        params.append(('providers', p))

    return HttpResponseRedirect(f"/results/?{urlencode(params, doseq=True)}")
