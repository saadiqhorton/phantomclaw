"""Web agent package - search, scrape, and synthesize web content."""
from .agent import main as web_agent
from .search import search_with_fallback, SearchError
from .scrape import WebPageFetcher, FetchError

__all__ = [
    "web_agent",
    "search_with_fallback",
    "SearchError",
    "WebPageFetcher",
    "FetchError",
]
