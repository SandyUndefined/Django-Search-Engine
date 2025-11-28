import os
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core.cache import cache
from django.test import Client, SimpleTestCase, override_settings

from SearchEngine import search, views

TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'searchengine-test-cache',
    }
}
STATIC_ROOT_FOR_TESTS = os.path.join(settings.BASE_DIR, 'static')


@override_settings(
    CACHES=TEST_CACHES,
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies',
    STATIC_ROOT=STATIC_ROOT_FOR_TESTS,
)
class ResultsViewTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def test_get_redirects_home(self):
        response = self.client.get('/results/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/')

    def test_empty_query_redirects_home(self):
        response = self.client.post('/results/', {'search': '   '})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/')

    def test_returns_cached_results_when_present(self):
        cached_context = {
            'errors': {},
            'query': 'test',
            'site_filter': '',
            'exclude_terms': [],
            'content_filter': '',
            'time_filter': '',
            'safe_mode': True,
            'providers': ['google'],
            'provider_results': [
                {
                    'key': 'google',
                    'label': 'Google',
                    'results': [('https://example.com', 'Example')],
                    'error': None,
                }
            ],
            'fused_results': [
                {
                    'url': 'https://example.com',
                    'title': 'Example',
                    'providers': ['Google'],
                    'snippet': 'Example snippet',
                    'domain': 'example.com',
                    'provider_count': 1,
                    'providers_list': ['Google'],
                }
            ],
            'analytics': [
                {'key': 'google', 'label': 'Google', 'result_count': 1, 'duration_ms': 1.0, 'error': False}
            ],
            'fused_sort': 'consensus',
        }
        provider_keys = [key for key, _, _ in views.SEARCH_PROVIDERS]
        cache_key = views._build_cache_key('test -adult -nsfw', provider_keys)
        cache.set(cache_key, cached_context, 30)

        response = self.client.get('/results/', {'search': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Example')

    def test_provider_error_does_not_break_page(self):
        def failing_provider(_query):
            raise RuntimeError("boom")

        with patch('SearchEngine.views.SEARCH_PROVIDERS', (('google', 'Google', failing_provider),)):
            response = self.client.post('/results/', {'search': 'demo'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Temporarily unable to fetch results')

    def test_provider_selection_respected(self):
        with patch(
            'SearchEngine.views.SEARCH_PROVIDERS',
            (
                ('google', 'Google', lambda q: (['a'], ['Google Title'])),
                ('bing', 'Bing', lambda q: (['b'], ['Bing Title'])),
            ),
        ):
            response = self.client.post('/results/', {'search': 'demo', 'providers': ['bing']})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bing Title')
        self.assertNotContains(response, 'Google Title')


@override_settings(
    CACHES=TEST_CACHES,
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies',
    STATIC_ROOT=STATIC_ROOT_FOR_TESTS,
)
class ScraperParsingTests(SimpleTestCase):
    def _mock_response(self, html):
        response = MagicMock()
        response.text = html
        response.raise_for_status.return_value = None
        return response

    @patch('SearchEngine.search.requests.get')
    def test_google_parser_handles_missing_elements(self, mock_get):
        mock_get.return_value = self._mock_response(
            "<div class='yuRUbf'><div>no anchor</div></div>"
        )
        links, titles = search.google("demo")
        self.assertEqual(links, [])
        self.assertEqual(titles, [])

    @patch('SearchEngine.search.requests.get')
    def test_duckduckgo_parser_skips_missing_anchor(self, mock_get):
        mock_get.return_value = self._mock_response(
            "<div class='result__body'><div class='snippet'>no link</div></div>"
        )
        links, titles = search.duck("demo")
        self.assertEqual(links, [])
        self.assertEqual(titles, [])

    @patch('SearchEngine.search.requests.get')
    def test_bing_parser_extracts_link(self, mock_get):
        mock_get.return_value = self._mock_response(
            "<li class='b_algo'><a href='https://example.com'>Example Title</a></li>"
        )
        links, titles = search.bing("demo")
        self.assertEqual(links, ["https://example.com"])
        self.assertEqual(titles, ["Example Title"])
