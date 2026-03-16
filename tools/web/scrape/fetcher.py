"""Web page fetcher - download and extract content from web pages."""
import os
import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

# Will be imported lazily to provide clear error if not installed
BeautifulSoup = None
requests = None

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Raised when page fetch fails."""
    pass


class ContentExtractionError(Exception):
    """Raised when content extraction fails."""
    pass


@dataclass
class ScrapedContent:
    """Represents extracted content from a web page."""
    url: str
    title: str
    text: str
    error: Optional[str] = None


def _validate_url(url: str) -> None:
    """
    Validate URL scheme to prevent dangerous URLs.

    Args:
        url: The URL to validate

    Raises:
        FetchError: If URL scheme is not http or https
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise FetchError(f"Unsupported URL scheme: {parsed.scheme}. Only http and https are allowed.")
    if not parsed.netloc:
        raise FetchError("Invalid URL: missing network location (domain).")


class WebPageFetcher:
    """Fetches web pages and extracts main content."""

    def __init__(self, timeout: int = 15, max_content_length: int = 8000):
        self.timeout = timeout
        self.max_content_length = max_content_length

    def fetch(self, url: str) -> ScrapedContent:
        """
        Fetch a URL and extract main content.

        Args:
            url: The URL to fetch

        Returns:
            ScrapedContent object with extracted text

        Raises:
            FetchError: If the request fails
        """
        # Validate URL before making request
        try:
            _validate_url(url)
        except FetchError as e:
            return ScrapedContent(url=url, title="", text="", error=str(e))
        global BeautifulSoup, requests

        if requests is None:
            try:
                import requests as _requests
                requests = _requests
            except ImportError:
                raise FetchError("requests library not installed. Run: pip install requests beautifulsoup4")

        if BeautifulSoup is None:
            try:
                from bs4 import BeautifulSoup as _BeautifulSoup
                BeautifulSoup = _BeautifulSoup
            except ImportError:
                raise FetchError("beautifulsoup4 not installed. Run: pip install beautifulsoup4")

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                allow_redirects=True
            )

            if response.status_code == 403:
                return ScrapedContent(
                    url=url,
                    title="",
                    text="",
                    error="Access forbidden (403). Site may block automated requests."
                )

            if response.status_code == 429:
                return ScrapedContent(
                    url=url,
                    title="",
                    text="",
                    error="Rate limited (429). Too many requests."
                )

            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string or ""

            # Remove unwanted elements
            for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                tag.decompose()

            # Try to find main content areas
            main_content = (
                soup.find("main") or
                soup.find("article") or
                soup.find("div", class_=lambda x: x and ("content" in x.lower() or "article" in x.lower())) or
                soup.find("body")
            )

            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

            # Clean up whitespace
            text = "\n".join(line.strip() for line in text.split("\n") if line.strip())

            # Truncate if too long
            if len(text) > self.max_content_length:
                text = text[: self.max_content_length] + "\n\n[... content truncated ...]"

            return ScrapedContent(
                url=url,
                title=title,
                text=text
            )

        except requests.Timeout:
            return ScrapedContent(
                url=url,
                title="",
                text="",
                error=f"Request timed out after {self.timeout}s"
            )

        except requests.RequestException as e:
            return ScrapedContent(
                url=url,
                title="",
                text="",
                error=f"Request failed: {e}"
            )

        except Exception as e:
            return ScrapedContent(
                url=url,
                title="",
                text="",
                error=f"Unexpected error: {e}"
            )