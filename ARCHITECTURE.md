# Architecture

> **WAT = Workflows · Agents · Tools**
> Probabilistic AI handles reasoning. Deterministic code handles execution.

This document describes the WAT framework structure and conventions used by Phantomclaw.

## Directory Layout

```
phantomclaw/
├── README.md           # Project overview
├── ARCHITECTURE.md     # This file - technical framework documentation
├── AGENTS.md           # Agent operating instructions
├── .env.example        # Environment variables template
├── opencode.json       # OpenCode configuration
├── tools/              # Python scripts for deterministic execution
│   ├── web/            # Web search and scraping
│   ├── tldr/           # TLDR newsletter fetching
│   ├── lobster/        # Movie/TV streaming
│   └── telegram/        # Telegram bridge
├── workflows/          # Markdown SOPs
└── tmp/                # Temporary processing files
```

## The Three Layers

### Layer 1: Workflows (The Instructions)
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

### Layer 2: Agents (The Decision-Maker)
- Intelligent coordination layer using AI models
- Reads relevant workflows, runs tools in correct sequence, handles failures gracefully
- Connects intent to execution without trying to do everything directly

### Layer 3: Tools (The Execution)
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations
- Credentials and API keys stored in `.env`
- Consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## Tool Organization

Tools are organized by capability:

| Path | Purpose |
|------|---------|
| `tools/telegram/` | Telegram bot bridge |
| `tools/tldr/` | TLDR newsletter fetching and digest |
| `tools/lobster/` | Movie/TV streaming search |
| `tools/web/` | Web search and scraping |
| `tools/repo/` | Repository monitoring |

### Backward Compatibility

Flat tool paths are preserved as shims for backward compatibility:

| Legacy Path | New Location |
|-------------|--------------|
| `tools/telegram_opencode_bridge.py` | `tools/telegram/bridge.py` |
| `tools/repo_sentinel.py` | `tools/repo/sentinel.py` |

## Conventions

### Tools
- Standalone Python scripts in capability folders
- Run with `--help` to see args
- Output JSON for structured data
- Exit 0 on success, non-zero on failure

### Workflows
- Markdown SOPs in `workflows/`
- Each workflow defines objective, inputs, tools, outputs, edge cases

### Environment Variables
- All credentials in `.env` (never committed)
- See `.env.example` for required variables

## The Self-Improvement Loop

Every failure → fix the tool → verify → update the workflow. The system gets stronger with each iteration.
