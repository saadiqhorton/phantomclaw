#!/usr/bin/env python3
"""
TLDR Digest Notifier — sends a formatted digest message to a Telegram chat.
This is NOT the bridge bot. It fires one sendMessage call and exits.
Used exclusively by the daily_tldr_digest.py pipeline.
"""
import os
import sys
import asyncio

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from telegram import Bot
from telegram.constants import ParseMode


async def send_message(text: str, parse_mode: str = "HTML"):
    """Send a single message to the configured Telegram chat."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID not set in .env", file=sys.stderr)
        sys.exit(1)

    bot = Bot(token=token)

    # Telegram caps messages at 4096 chars. Split if necessary.
    chunks = []
    while len(text) > 4096:
        # Try to split at a newline before the limit
        split_idx = text.rfind("\n", 0, 4096)
        if split_idx == -1:
            split_idx = 4096
        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip("\n")
    chunks.append(text)

    for chunk in chunks:
        if chunk.strip():
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=chunk,
                    parse_mode=ParseMode.HTML if parse_mode == "HTML" else ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            except Exception as e:
                # If HTML parsing fails, fall back to plain text
                print(f"⚠️ HTML send failed ({e}), falling back to plain text", file=sys.stderr)
                await bot.send_message(
                    chat_id=chat_id,
                    text=chunk,
                    disable_web_page_preview=True
                )

    print(f"✅ Sent {len(chunks)} message(s) to Telegram chat {chat_id}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tldr_digest_notifier.py \"message text\"")
        sys.exit(1)

    message = sys.argv[1]
    asyncio.run(send_message(message))


if __name__ == "__main__":
    main()
