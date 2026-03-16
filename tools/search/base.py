"""Search provider base classes and interfaces."""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str


class AbstractSearchProvider(ABC):
    """Abstract base class for search providers."""

    def __init__(self):
        self.timeout = int(os.environ.get("SEARCH_TIMEOUT", "10"))

    @abstractmethod
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Perform a search query and return results.

        Args:
            query: The search query string
            num_results: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name for logging/debugging."""
        pass


class SearchError(Exception):
    """Base exception for search-related errors."""
    pass


class ProviderUnavailableError(SearchError):
    """Raised when the search provider is unavailable."""
    pass