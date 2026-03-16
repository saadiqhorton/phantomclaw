---
description: How to use the Lobster Telegram Streaming Bot integration
---

# Lobster Telegram Streaming

This workflow describes the Lobster integration in the Telegram OpenCode Bridge (`tools/telegram/bridge.py`). The bot now has native, interactive search and streaming capabilities.

## Setup & Requirements

- The logic is implemented purely in Python via `tools/lobster/lobster_stream.py`. No bash dependencies or shell scripts are required.
- Requires `requests` package.
- The bot extracts Adaptive Streaming (`.m3u8`) links directly to the Telegram chat.
- **Persistent Sessions**: Search and selection results are stored in `/tmp/lobster_sessions.json`, meaning your progress survives bot restarts.

## Available Commands

- `/watch <query>` - Search for a movie or TV show.
- `/trending` - Get currently trending movies and TV shows.
- `/recent_movies` - Get recently released movies.
- `/recent_tv` - Get recently released TV shows.

## How to use

1. Send a command like `/watch breaking bad` to the bot.
2. The bot will return an inline keyboard with search results.
3. Tap a result:
   - **For Movies**, the bot immediately extracts the `.m3u8` streaming URL and provides a link to watch.
   - **For TV Shows**, the bot provides season buttons. Select a season, then select an episode to get the streaming link.
4. Tap the returned link to open your native player or Telegram's internal browser.

## Troubleshooting

- **Decryption API Errors**: The streams are provided by `flixhq.to` and decrypted via external APIs. If the first fails, a fallback is automatically used. If both fail, it will report an extraction error. Wait and try again later.
- **Link Expired**: Embed URLs and `m3u8` links are often session-based or tokenized. If a link expires, just query the bot again to get a fresh link.
