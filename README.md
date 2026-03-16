# Phantomclaw

> **The Agentic OS for Information and Utility.**

Phantomclaw is an advanced suite of tools designed to bridge the gap between complex workflows and seamless user interaction. Built on the **WAT Framework**, it empowers users with automated intelligence and rich media capabilities through a unified, multi-modal interface.

## Core Features

### Daily TLDR Digest
Never miss a beat in AI and Tech. Phantomclaw automatically:
- Fetches the latest TLDR newsletters.
- Filters and summarizes content specifically for AI/Coding interests.
- Delivers a clean, formatted digest to your Telegram at 8:00 AM ET.

### Lobster Stream
Your personal entertainment hub.
- Search and stream movies and TV shows directly.
- Interactive selection of seasons and episodes.
- High-quality direct streaming links integration.

### Telegram-OpenCode Bridge
A powerful, multi-modal gateway to your workspace.
- **Voice Support**: Transcribe and process audio commands via Groq (Whisper).
- **Vision Support**: Analyze images and video frames using local Ollama (Qwen) models.
- **Web Search**: Search the web with AI synthesis - just send a query (not /search command)
- **Command Control**: Handle `/watch`, `/trending`, and file uploads seamlessly.

### Web Search
Search the web and get synthesized results with sources.
- Combines search (SEARXNG/DuckDuckGo) with content scraping
- AI-powered synthesis using OpenAI or Minimax
- Clean output without raw HTML/JSON artifacts

### Repo Sentinel
Monitor your repositories for new commits and activity.
- Get notified via Telegram when repositories have new commits
- Track multiple repositories

## Quickstart

1. Copy `.env.example` → `.env` and fill in your credentials
2. Browse `workflows/` to find the SOP for your task
3. Run the appropriate tool

## Directory Layout

```
phantomclaw/
├── README.md           # Project overview (this file)
├── ARCHITECTURE.md     # WAT framework structure and conventions
├── AGENTS.md           # Agent operating instructions
├── .env.example        # Environment variables template
├── opencode.json       # OpenCode configuration
├── tools/              # Python scripts for deterministic execution
├── workflows/         # Markdown SOPs (standard operating procedures)
└── tmp/                # Temporary processing files (ephemeral)
```

## Tech Stack

- **AI Models**: OpenAI, Minimax, Ollama, Groq
- **Telegram**: python-telegram-bot for bot integration
- **Search**: SEARXNG, DuckDuckGo
- **Email**: gws (Gmail workaround)

---

*Phantomclaw: Automating your digital life, one workflow at a time.*
