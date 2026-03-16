#!/usr/bin/env python3
"""
Web Agent - Agentic web search tool.

Search the web, visit top results, and gather information like a human would.
This tool combines search + scraping to provide comprehensive results.
"""
import argparse
import json
import logging
import os
import sys

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .search import search_with_fallback, SearchError
from .scrape import WebPageFetcher, FetchError


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_env():
    """Load environment variables from .env file."""
    # Go up 3 levels: web/ -> tools/ -> phantomclaw/ -> .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    if key.strip() and val.strip():
                        os.environ[key.strip()] = val.strip().strip("'\"")


def synthesize_with_ai(content: list, query: str) -> str:
    """
    Synthesize gathered content using AI API.

    Args:
        content: List of ScrapedContent objects
        query: Original search query

    Returns:
        Synthesized summary string
    """
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        logger.warning("No AI API key found, skipping synthesis")
        return None

    # Build context from scraped content
    context_parts = []
    for item in content:
        if item.text and not item.error:
            context_parts.append(f"Source: {item.title}\n{item.text[:1500]}")

    if not context_parts:
        return None

    context = "\n\n---\n\n".join(context_parts[:3])  # Limit to top 3

    # Simple synthesis prompt
    prompt = f"""Based on the following search results for "{query}", provide a concise summary that answers the question:

{context}

Summary:"""

    # Use OpenAI API
    if os.environ.get("OPENAI_API_KEY"):
        return synthesize_openai(api_key, prompt)
    elif os.environ.get("MINIMAX_API_KEY"):
        return synthesize_minimax(api_key, prompt)

    return None


def synthesize_openai(api_key: str, prompt: str) -> str:
    """Synthesize using OpenAI API."""
    try:
        import urllib.request
        import urllib.parse

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.7
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]

    except Exception as e:
        logger.warning(f"OpenAI synthesis failed: {e}")
        return None


def synthesize_minimax(api_key: str, prompt: str) -> str:
    """Synthesize using Minimax API."""
    try:
        import urllib.request
        import urllib.parse

        url = "https://api.minimax.chat/v1/text/chatcompletion_pro"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "MiniMax-M2.5",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.7
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]

    except Exception as e:
        logger.warning(f"Minimax synthesis failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Agentic web search - search, visit, and gather information"
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--num-results", "-n", type=int, default=5,
        help="Number of search results to fetch (default: 5)"
    )
    parser.add_argument(
        "--visit", "-v", type=int, default=3,
        help="Number of results to visit/fetch (default: 3)"
    )
    parser.add_argument(
        "--synthesize", "-s", action="store_true",
        help="Attempt AI synthesis of results"
    )
    parser.add_argument(
        "--format", "-f", choices=["json", "text"], default="json",
        help="Output format (default: json)"
    )

    args = parser.parse_args()

    # Load environment
    load_env()

    result = {
        "query": args.query,
        "status": "success",
        "search_results": [],
        "visited": [],
        "summary": None
    }

    # Step 1: Search
    try:
        logger.info(f"Searching for: {args.query}")
        search_results, provider = search_with_fallback(args.query, args.num_results)
        result["search_provider"] = provider

        result["search_results"] = [
            {"title": r.title, "url": r.url, "snippet": r.snippet}
            for r in search_results
        ]
        logger.info(f"Found {len(search_results)} results using {provider}")

    except SearchError as e:
        result["status"] = "search_failed"
        result["error"] = str(e)
        print(json.dumps(result))
        sys.exit(1)

    # Step 2: Visit top results
    fetcher = WebPageFetcher()
    visited_count = 0

    for search_result in result["search_results"][:args.visit]:
        url = search_result["url"]
        logger.info(f"Visiting: {url}")

        try:
            content = fetcher.fetch(url)
            result["visited"].append({
                "title": content.title or search_result["title"],
                "url": url,
                "text": content.text[:2000] if content.text else "",
                "error": content.error
            })
            visited_count += 1

        except FetchError as e:
            result["visited"].append({
                "title": search_result["title"],
                "url": url,
                "text": "",
                "error": str(e)
            })

    result["visited_count"] = visited_count

    # Step 3: Synthesize (optional)
    if args.synthesize:
        logger.info("Attempting AI synthesis...")
        summary = synthesize_with_ai(result["visited"], args.query)
        if summary:
            result["summary"] = summary

    # Output
    if args.format == "text":
        print(f"Query: {args.query}")
        print(f"\nSearch Results ({result.get('search_provider', 'unknown')}):")
        for i, r in enumerate(result["search_results"], 1):
            print(f"  {i}. {r['title']}")
            print(f"     {r['url']}")

        if result["summary"]:
            print(f"\n--- Summary ---\n{result['summary']}")
        else:
            print(f"\n--- Visited Content ---")
            for v in result["visited"]:
                print(f"\n[{v['title']}]")
                print(v["text"][:500] + "..." if len(v["text"]) > 500 else v["text"])
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()