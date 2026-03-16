"""Search provider module - abstraction layer for web search."""
from .base import AbstractSearchProvider, SearchResult, SearchError, ProviderUnavailableError
from .searxng import SearxngProvider
from .duckduckgo import DuckDuckGoProvider

# Provider registry - order matters (primary first, then fallbacks)
PROVIDERS = [
    SearxngProvider,
    DuckDuckGoProvider,
]


def get_search_provider(name: str = None) -> AbstractSearchProvider:
    """
    Get a search provider by name, or return the first available one.

    Args:
        name: Optional provider name ("searxng" or "duckduckgo")

    Returns:
        SearchProvider instance

    Raises:
        ValueError: If provider name is unknown
    """
    if name:
        provider_map = {
            "searxng": SearxngProvider,
            "duckduckgo": DuckDuckGoProvider,
        }
        if name not in provider_map:
            raise ValueError(f"Unknown provider: {name}. Available: {list(provider_map.keys())}")
        return provider_map[name]()

    # Return first available provider
    for provider_class in PROVIDERS:
        try:
            provider = provider_class()
            # Quick availability check
            return provider
        except ProviderUnavailableError:
            continue

    raise SearchError("No search providers available")


def search_with_fallback(query: str, num_results: int = 10) -> tuple[list[SearchResult], str]:
    """
    Search with automatic fallback between providers.

    Args:
        query: Search query
        num_results: Maximum results

    Returns:
        Tuple of (results, provider_name_used)
    """
    last_error = None

    for provider_class in PROVIDERS:
        try:
            provider = provider_class()
            results = provider.search(query, num_results)
            return results, provider.name
        except ProviderUnavailableError as e:
            last_error = e
            continue

    raise SearchError(f"All providers failed. Last error: {last_error}")


__all__ = [
    "AbstractSearchProvider",
    "SearchResult",
    "SearchError",
    "ProviderUnavailableError",
    "SearxngProvider",
    "DuckDuckGoProvider",
    "get_search_provider",
    "search_with_fallback",
    "PROVIDERS",
]