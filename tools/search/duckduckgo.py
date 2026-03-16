"""DuckDuckGo search provider (fallback)."""
import os
import urllib.request
import urllib.parse
import html
import re
from typing import List

from .base import AbstractSearchProvider, SearchResult, ProviderUnavailableError


def _sanitize_text(text: str) -> str:
    """Additional sanitization for DuckDuckGo results."""
    # Extra safety: remove any remaining script tags that get_text might miss
    text = html.unescape(text)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # Strip all remaining HTML tags (b, i, span, etc.)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

# Lazy import for BeautifulSoup to provide clear error if not installed
BeautifulSoup = None


def _get_beautifulsoup():
    """Lazy load BeautifulSoup."""
    global BeautifulSoup
    if BeautifulSoup is None:
        try:
            from bs4 import BeautifulSoup as _BeautifulSoup
            BeautifulSoup = _BeautifulSoup
        except ImportError:
            raise ProviderUnavailableError("beautifulsoup4 not installed. Run: pip install beautifulsoup4")
    return BeautifulSoup


class DuckDuckGoProvider(AbstractSearchProvider):
    """Fallback search provider using DuckDuckGo HTML."""

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return "duckduckgo"

    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Search using DuckDuckGo HTML interface.

        Args:
            query: Search query string
            num_results: Maximum results to return

        Returns:
            List of SearchResult objects

        Raises:
            ProviderUnavailableError: If DuckDuckGo is unreachable
        """
        url = "https://html.duckduckgo.com/html/"
        data = urllib.parse.urlencode({"q": query}).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=data)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            req.add_header("Accept", "text/html")

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                html = response.read().decode("utf-8")

            return self._parse_results(html, num_results)

        except Exception as e:
            raise ProviderUnavailableError(f"DuckDuckGo unavailable: {e}")

    def _parse_results(self, html: str, num_results: int) -> List[SearchResult]:
        """Parse DuckDuckGo HTML results using BeautifulSoup."""
        results = []
        BS = _get_beautifulsoup()
        soup = BS(html, "html.parser")

        # Find all result elements - look for result__a links inside result containers
        result_links = soup.find_all("a", class_="result__a")

        for link in result_links:
            url = link.get("href", "")
            title = link.get_text(strip=True)

            # Skip internal/redirect URLs
            if "uddg=" in url:
                continue

            if not url or not title:
                continue

            # Find adjacent snippet - look for result__snippet in the same parent
            # Use class-based lookup since result element may be div, not a tag
            parent = link.find_parent(class_=lambda x: x and "result" in x)
            snippet = ""
            if parent:
                snippet_elem = parent.find("a", class_="result__snippet")
                if snippet_elem:
                    snippet = snippet_elem.get_text(strip=True)

            results.append(SearchResult(
                title=_sanitize_text(title),
                url=url,
                snippet=_sanitize_text(snippet)[:200] if snippet else ""
            ))

            if len(results) >= num_results:
                break

        return results