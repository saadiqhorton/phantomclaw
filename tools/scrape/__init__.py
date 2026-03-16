"""Web scraping utilities - fetch and extract content from web pages."""
from .fetcher import WebPageFetcher, FetchError, ContentExtractionError

__all__ = [
    "WebPageFetcher",
    "FetchError",
    "ContentExtractionError",
]