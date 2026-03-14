#!/usr/bin/env python3
"""
Daily TLDR Digest — fetches all TLDR newsletters, filters for AI/coding-relevant
items, preserves formatting, and sends the digest to Telegram.

Designed to be called by cron at 8:00 AM daily.
"""
import os
import sys
import json
import re
import subprocess
import asyncio
from html.parser import HTMLParser
from datetime import datetime

# Add project root to path so we can import the notifier
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except ImportError:
    pass

from tldr_digest_notifier import send_message

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

# Newsletter types to fetch
NEWSLETTER_TYPES = ["ai", "dev", "devops", "infosec", "it", "regular"]

# Keywords to filter for (case-insensitive). An article matches if ANY keyword
# appears in its headline or blurb text.
AI_CODING_KEYWORDS = [
    # AI / ML
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "transformer", "llm", "large language model",
    "generative ai", "gen ai", "foundation model",
    # Companies & Products
    "openai", "gpt", "gpt-4", "gpt-5", "chatgpt", "o1", "o3",
    "claude", "anthropic", "sonnet", "opus", "haiku",
    "gemini", "google deepmind", "deepmind",
    "cursor", "windsurf", "copilot", "github copilot",
    "deepseek", "mistral", "llama", "meta ai",
    "perplexity", "midjourney", "stable diffusion", "dall-e",
    "hugging face", "huggingface",
    # Coding / Dev Tools
    "coding", "developer", "programming", "software engineer",
    "api", "sdk", "open source", "github", "gitlab",
    "python", "javascript", "typescript", "rust", "golang",
    "vscode", "vs code", "ide", "devtools",
    "docker", "kubernetes", "ci/cd", "terraform",
    # AI Agents / Infra
    "agent", "ai agent", "agentic", "rag", "retrieval augmented",
    "fine-tuning", "fine tuning", "prompt engineering",
    "vector database", "embedding", "inference",
    "mcp", "model context protocol",
]

# Compile a single regex for fast matching
_kw_pattern = re.compile(
    r'\b(' + '|'.join(re.escape(kw) for kw in AI_CODING_KEYWORDS) + r')\b',
    re.IGNORECASE
)


# ──────────────────────────────────────────────────────────────────────────────
# HTML → ARTICLE EXTRACTION
# ──────────────────────────────────────────────────────────────────────────────

class TLDRHTMLParser(HTMLParser):
    """
    Parses TLDR newsletter HTML and extracts article blocks.
    TLDR newsletters follow a fairly consistent structure:
    - Headlines are bold/linked text
    - Blurbs follow underneath
    - Sections are separated by horizontal rules or headers
    Captures links so they can be included in the digest output.
    """
    def __init__(self):
        super().__init__()
        self.articles = []
        self.current_text = []
        self.in_link = False
        self.current_href = ""
        self.raw_text_blocks = []  # list of (text, link_or_None)

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a" and "href" in attrs_dict:
            href = attrs_dict["href"]
            # Skip tracking pixels, unsubscribe links, and anchors
            if not href.startswith("#") and "unsubscribe" not in href.lower():
                self.in_link = True
                self.current_href = href

    def handle_endtag(self, tag):
        if tag == "a":
            self.in_link = False
            self.current_href = ""

    def handle_data(self, data):
        text = data.strip()
        if text:
            link = self.current_href if self.in_link else None
            self.raw_text_blocks.append((text, link))


def extract_articles_from_html(html_body: str) -> list[dict]:
    """
    Extract articles from TLDR newsletter HTML.
    Returns a list of dicts with 'headline', 'blurb', and 'link' keys.
    """
    parser = TLDRHTMLParser()
    try:
        parser.feed(html_body)
    except Exception:
        pass

    # raw_text_blocks is now list of (text, link_or_None)
    blocks = parser.raw_text_blocks
    articles = []
    i = 0

    # Skip boilerplate header blocks
    skip_phrases = [
        "view online", "sign up", "advertise", "together with",
        "unsubscribe", "update your preferences", "privacy policy",
        "manage preferences", "confirm signup"
    ]

    while i < len(blocks):
        text, link = blocks[i]
        text = text.strip()

        # Skip very short or boilerplate blocks
        if len(text) < 5 or any(sp in text.lower() for sp in skip_phrases):
            i += 1
            continue

        # Heuristic: a headline is typically a short-ish block (< 150 chars)
        # followed by a longer blurb block
        if len(text) < 150 and i + 1 < len(blocks):
            next_text, next_link = blocks[i + 1]
            next_text = next_text.strip()
            # If the next block looks like a blurb (longer text)
            if len(next_text) > 30:
                # Use the link from the headline block if it has one
                article_link = link or next_link
                articles.append({
                    "headline": text,
                    "blurb": next_text,
                    "link": article_link
                })
                i += 2
                continue

        # If it's a standalone longer block, treat it as both headline and blurb
        if len(text) > 50:
            period_idx = text.find(". ")
            if period_idx > 10 and period_idx < 120:
                articles.append({
                    "headline": text[:period_idx],
                    "blurb": text[period_idx + 2:],
                    "link": link
                })
            else:
                articles.append({
                    "headline": text[:80] + ("..." if len(text) > 80 else ""),
                    "blurb": text,
                    "link": link
                })

        i += 1

    return articles


def extract_articles_from_text(text_body: str) -> list[dict]:
    """Fallback: extract articles from plain text body."""
    # Also try to grab URLs from the text
    url_pattern = re.compile(r'https?://\S+')
    articles = []
    lines = [l.strip() for l in text_body.split("\n") if l.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]
        if len(line) < 5:
            i += 1
            continue

        if len(line) < 150 and i + 1 < len(lines) and len(lines[i + 1]) > 30:
            # Check for a URL in the headline or blurb
            combined = line + " " + lines[i + 1]
            url_match = url_pattern.search(combined)
            articles.append({
                "headline": line,
                "blurb": lines[i + 1],
                "link": url_match.group(0) if url_match else None
            })
            i += 2
        else:
            i += 1

    return articles


# ──────────────────────────────────────────────────────────────────────────────
# FILTERING
# ──────────────────────────────────────────────────────────────────────────────

def is_relevant(article: dict) -> bool:
    """Check if an article matches any AI/coding keyword."""
    combined = f"{article.get('headline', '')} {article.get('blurb', '')}"
    return bool(_kw_pattern.search(combined))


# ──────────────────────────────────────────────────────────────────────────────
# FORMATTING
# ──────────────────────────────────────────────────────────────────────────────

def format_digest(all_articles: dict[str, list[dict]]) -> str:
    """
    Format the filtered articles into a Telegram-friendly HTML message.
    Preserves the newsletter feel with bold headlines and blurbs.
    """
    today = datetime.now().strftime("%A, %B %d %Y")
    lines = [f"📰 <b>TLDR Daily Digest — {today}</b>"]
    lines.append("━" * 30)
    lines.append("")

    total_items = 0

    for newsletter_type, articles in all_articles.items():
        if not articles:
            continue

        emoji_map = {
            "ai": "🤖", "dev": "💻", "devops": "⚙️",
            "infosec": "🔒", "it": "🖥️", "regular": "📬"
        }
        emoji = emoji_map.get(newsletter_type, "📰")
        section_name = newsletter_type.upper() if newsletter_type != "regular" else "TLDR"

        lines.append(f"{emoji} <b>TLDR {section_name}</b>")
        lines.append("")

        for article in articles:
            headline = article["headline"]
            blurb = article["blurb"]
            link = article.get("link")

            # Escape HTML entities in the text
            headline = headline.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            blurb = blurb.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            # Include link as clickable text if available
            if link:
                lines.append(f'  <b>▸ <a href="{link}">{headline}</a></b>')
            else:
                lines.append(f"  <b>▸ {headline}</b>")
            lines.append(f"  {blurb}")
            lines.append("")
            total_items += 1

        lines.append("")

    if total_items == 0:
        lines.append("No AI/coding-relevant items found in today's newsletters.")
        lines.append("Check back tomorrow! 🙂")

    lines.append("━" * 30)
    lines.append(f"📊 <i>{total_items} items matched your AI/coding filter</i>")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────────────────────────────────────

def fetch_newsletter(newsletter_type: str) -> list[dict]:
    """Fetch the latest newsletter using the existing fetch tool."""
    output_path = os.path.join(PROJECT_ROOT, ".tmp", f"tldr_{newsletter_type}.json")

    cmd = [
        sys.executable,
        os.path.join(SCRIPT_DIR, "fetch_tldr_emails.py"),
        newsletter_type,
        "--limit", "1",
        "--output", output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"⚠️ fetch_tldr_emails.py failed for {newsletter_type}: {result.stderr}")
            return []
    except subprocess.TimeoutExpired:
        print(f"⚠️ Timeout fetching {newsletter_type}")
        return []

    if not os.path.exists(output_path):
        return []

    try:
        with open(output_path, "r") as f:
            emails = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

    all_articles = []
    for email in emails:
        body = email.get("body_text", "")
        if "<html" in body.lower() or "<table" in body.lower():
            articles = extract_articles_from_html(body)
        else:
            articles = extract_articles_from_text(body)
        all_articles.extend(articles)

    return all_articles


def main():
    print(f"🚀 TLDR Daily Digest — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Ensure .tmp exists
    os.makedirs(os.path.join(PROJECT_ROOT, ".tmp"), exist_ok=True)

    all_filtered = {}

    for ntype in NEWSLETTER_TYPES:
        print(f"📥 Fetching {ntype}...")
        articles = fetch_newsletter(ntype)
        print(f"   Found {len(articles)} articles total")

        relevant = [a for a in articles if is_relevant(a)]
        print(f"   ✅ {len(relevant)} matched AI/coding filter")

        if relevant:
            all_filtered[ntype] = relevant

    # Format the digest
    digest_text = format_digest(all_filtered)

    # Save a copy locally
    digest_path = os.path.join(PROJECT_ROOT, ".tmp", "tldr_digest_latest.txt")
    with open(digest_path, "w") as f:
        f.write(digest_text)
    print(f"\n💾 Saved digest to {digest_path}")

    # Send to Telegram
    print("📤 Sending to Telegram...")
    asyncio.run(send_message(digest_text, parse_mode="HTML"))
    print("✅ Done!")


if __name__ == "__main__":
    main()
