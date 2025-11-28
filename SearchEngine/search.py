import logging

import requests
from bs4 import BeautifulSoup
from requests import RequestException

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
BASE_HEADERS = {
    "user-agent": USER_AGENT,
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 6


def _get_soup(url, headers=None, allow_blocked=False):
    """Fetch a URL and return a BeautifulSoup parser."""
    merged_headers = BASE_HEADERS.copy()
    if headers:
        merged_headers.update(headers)
    response = requests.get(url, headers=merged_headers, timeout=REQUEST_TIMEOUT)
    if response.status_code == 403 and allow_blocked:
        logger.info("Request blocked with 403 for url=%s; returning empty", url)
        return None
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def google(query):
    links = []
    text = []
    try:
        soup = _get_soup(f"https://www.google.com/search?q={query}")
    except RequestException as exc:
        logger.warning("Google search failed: %s", exc)
        return links, text

    for result in soup.find_all("div", class_="yuRUbf"):
        anchor = result.find("a")
        heading = result.find("h3")
        if not anchor or not heading:
            continue
        href = anchor.get("href")
        title = heading.get_text(strip=True)
        if href and title:
            links.append(href)
            text.append(title)
    return links, text


def yahoo(query):
    links = []
    text = []
    url = f"https://search.yahoo.com/search?q={query}&n=10"
    try:
        soup = _get_soup(url)
    except RequestException as exc:
        logger.warning("Yahoo search failed: %s", exc)
        return links, text

    for link in soup.find_all(attrs={"class": "ac-algo fz-l ac-21th lh-24"}):
        href = link.get("href")
        title = link.get_text(strip=True)
        if href and title:
            links.append(href)
            text.append(title)
    return links, text


def duck(query):
    links = []
    text = []
    try:
        soup = _get_soup(f"https://duckduckgo.com/html/?q={query}")
    except RequestException as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
        return links, text

    # DuckDuckGo markup changes frequently; tolerate missing nodes.
    for result in soup.find_all("div", attrs={"class": "result__body"}):
        anchor = result.find("a", attrs={"class": "result__a"})
        if not anchor:
            continue
        href = anchor.get("href")
        title = anchor.get_text(strip=True)
        if href and title:
            links.append(href)
            text.append(title)
    return links, text


def ecosia(query):
    links = []
    text = []
    try:
        soup = _get_soup(f"https://www.ecosia.org/search?q={query}", allow_blocked=True)
    except RequestException as exc:
        logger.warning("Ecosia search failed: %s", exc)
        return links, text
    if soup is None:
        return links, text

    for heading in soup.find_all("h2", attrs={"class": "result-firstline-title"}):
        anchor = heading.find("a", attrs={"class": "js-result-title"})
        if not anchor:
            continue
        href = anchor.get("href")
        title = anchor.get_text(strip=True)
        if href and title:
            links.append(href)
            text.append(title)
    return links, text


def bing(query):
    try:
        soup = _get_soup(f"https://www.bing.com/search?q={query}")
    except RequestException as exc:
        logger.warning("Bing search failed: %s", exc)
        return [], []

    results = []
    texts = []
    for item in soup.find_all("li", {"class": "b_algo"}):
        anchor = item.find("a")
        if not anchor:
            continue
        href = anchor.get("href")
        title = anchor.get_text(strip=True)
        if href and title:
            results.append(href)
            texts.append(title)

    return results, texts


def givewater(query):
    try:
        soup = _get_soup(
            f"https://search.givewater.com/serp?q={query}",
            headers={"referer": "https://search.givewater.com/"},
            allow_blocked=True,
        )
    except RequestException as exc:
        logger.warning("GiveWater search failed: %s", exc)
        return [], []
    if soup is None:
        return [], []

    results = []
    texts = []

    for item in soup.find_all("div", {"class": "web-bing__result"}):
        anchor = item.find("a")
        if not anchor:
            continue
        href = anchor.get("href")
        title = anchor.get_text(strip=True)
        if href and title:
            results.append(href)
            texts.append(title)

    return results, texts
