# WAT Framework

> [!NOTE]
> For a high-level overview of the projects built on this framework (like TLDR Digest and Lobster Stream), see [README.md](README.md).

> **WAT = Workflows · Agents · Tools**
> Probabilistic AI handles reasoning. Deterministic code handles execution.

## Directory Layout

```
README.md          # Project overview (Phantomclaw)
WAT_FRAMEWORK.md   # Technical framework documentation (This file)
.tmp/              # Temporary processing files — ephemeral
tools/             # Python scripts for deterministic execution
workflows/         # Markdown SOPs (standard operating procedures)
_agents/           # Agent config and agent-facing workflows
.env               # API keys (never committed — see .env.example)
CLAUDE.md          # Agent instructions
```

## Quickstart

1. Copy `.env.example` → `.env` and fill in your credentials
2. Browse `workflows/` to find the SOP for your task
3. Ask the agent to run it

## Conventions

- **Tools** are standalone Python scripts (`tools/verb_noun.py`). Run them with `--help` to see args.
- **Workflows** are Markdown SOPs (`workflows/verb_noun.md`). The agent reads these before executing.
- **`.tmp/`** is ephemeral. Don't store anything you care about there.
- **Deliverables** go to cloud services (Google Sheets, Slides, etc.) — not local files.

## The Self-Improvement Loop

Every failure → fix the tool → verify → update the workflow. The system gets stronger with each iteration.
