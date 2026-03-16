"""SEARXNG search provider implementation."""
import os
import urllib.request
import urllib.parse
import json
import html
from typing import List

from .base import AbstractSearchProvider, SearchResult, ProviderUnavailableError


def _sanitize_text(text: str) -> str:
    """Decode HTML entities and strip dangerous content."""
    import re
    # First unescape HTML entities (&lt; → <, etc.)
    text = html.unescape(text)
    # Remove any residual script/style tags that might slip through
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # Strip all remaining HTML tags (b, i, span, etc.)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


class SearxngProvider(AbstractSearchProvider):
    """Search provider using SEARXNG (user's self-hosted metasearch)."""

    def __init__(self):
        super().__init__()
        self.base_url = os.environ.get("SEARXNG_URL", "http://192.168.1.201:8080")

    @property
    def name(self) -> str:
        return "searxng"

    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Search using SEARXNG API.

        Args:
            query: Search query string
            num_results: Maximum results to return

        Returns:
            List of SearchResult objects

        Raises:
            ProviderUnavailableError: If SEARXNG is unreachable
        """
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "format": "json",
            "engines": "google,bing,duckduckgo",  # Use reputable engines
            "language": "en",
            "safesearch": "1"  # Safe search on
        }

        full_url = f"{url}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(full_url)
            req.add_header("User-Agent", "Mozilla/5.0 (compatible; Phantomclaw/1.0)")
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))

            results = []
            for item in data.get("results", [])[:num_results]:
                results.append(SearchResult(
                    title=_sanitize_text(item.get("title", "")),
                    url=item.get("url", ""),
                    snippet=_sanitize_text(item.get("content", ""))[:200]
                ))

            return results

        except Exception as e:
            raise ProviderUnavailableError(f"SEARXNG unavailable: {e}")