# Phantomclaw

> **The Agentic OS for Information and Utility.**

Phantomclaw is an advanced suite of tools designed to bridge the gap between complex workflows and seamless user interaction. Built on the **WAT Framework**, it empowers users with automated intelligence and rich media capabilities through a unified, multi-modal interface.

## Core Features

### 🧠 Intelligence: Daily TLDR Digest
Never miss a beat in AI and Tech. Phantomclaw automatically:
- Fetches the latest TLDR newsletters.
- Filters and summarizes content specifically for AI/Coding interests.
- Delivers a clean, formatted digest to your Telegram at 8:00 AM ET.
- *Managed via: `tools/daily_tldr_digest.py` and `tools/fetch_tldr_emails.py`*

### 🎬 Media: Lobster Stream
Your personal entertainment hub.
- Search and stream movies and TV shows directly.
- Interactive selection of seasons and episodes.
- High-quality direct streaming links integration.
- *Managed via: `tools/lobster_stream.py`*

### 🏗️ Interface: Telegram-OpenCode Bridge
A powerful, multi-modal gateway to your workspace.
- **Voice Support**: Transcribe and process audio commands via **Groq (Whisper)**.
- **Vision Support**: Analyze images and video frames using local **Ollama (Qwen)** models.
- **Persistent Sessions**: Maintain coding context across interactions.
- **Command Control**: Handle `/watch`, `/trending`, and file uploads seamlessly.
- *Managed via: `tools/telegram_opencode_bridge.py`*

## Directory Layout

```
README.md          # Project overview (This file)
WAT_FRAMEWORK.md   # Technical framework documentation
tools/             # Core functionality (TLDR, Lobster, Telegram)
workflows/         # Step-by-step agent instructions
_agents/           # Agent-specific configurations
```

## Architecture

Phantomclaw leverages the **WAT (Workflows, Agents, Tools)** architecture:
- **Workflows**: Standardized SOPs in `workflows/`.
- **Agents**: Intelligent coordination using models like Minimax.
- **Tools**: Deterministic Python scripts in `tools/`.

---
*Phantomclaw: Automating your digital life, one workflow at a time.*

> [!TIP]
> For technical details on the underlying **WAT Framework** (Workflows, Agents, Tools), see [WAT_FRAMEWORK.md](WAT_FRAMEWORK.md).
