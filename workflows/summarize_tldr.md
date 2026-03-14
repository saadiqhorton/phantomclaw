---
description: fetches, filters, and delivers daily TLDR newsletters (AI, Infosec, IT, Dev, DevOps, Regular) to Telegram
---

# Summarize TLDR Newsletters

This workflow fetches the latest TLDR newsletters from Gmail using `gws`, filters for AI/coding-relevant content, and sends a formatted digest to Telegram.

## Automated Schedule
- **Cron job** runs daily at **8:00 AM** (system timezone)
- Installed via `bash tools/setup_cron.sh`
- Logs to `.tmp/tldr_cron.log`

## Prerequisites
- `gws` installed and authenticated (`gws auth login`)
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` set in `.env`

## Manual Run
To trigger the digest manually at any time:
```bash
python3 tools/daily_tldr_digest.py
```

## Pipeline Flow
1. `tools/fetch_tldr_emails.py` — fetches the latest email from each newsletter type via `gws`
2. `tools/daily_tldr_digest.py` — parses HTML, extracts articles with links, filters for AI/coding keywords, formats a rich digest
3. `tools/tldr_digest_notifier.py` — sends the formatted digest to Telegram

## AI/Coding Filter Keywords
The digest only includes articles matching keywords like: AI, Claude, OpenAI, Cursor, Copilot, Gemini, LLM, GitHub, Python, Docker, etc. The full keyword list is configurable at the top of `tools/daily_tldr_digest.py`.

## Error Handling
- If `gws` fails due to auth errors, re-run `gws auth login`
- If no emails match, a "no items found" message is sent to Telegram
- Cron output logs to `.tmp/tldr_cron.log` for debugging
