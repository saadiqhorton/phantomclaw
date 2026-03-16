# Workflows

Markdown SOPs that define how to accomplish a specific objective. Each workflow should include:

1. **Objective** — what this workflow achieves
2. **Inputs** — what's needed before starting
3. **Steps** — precise sequence of actions (tools to call, decisions to make)
4. **Outputs** — what a successful run produces
5. **Edge Cases** — known failure modes and how to handle them

## Conventions

| Convention | Detail |
|---|---|
| Naming | `verb_noun.md` — e.g. `scrape_website.md`, `update_sheet.md` |
| Tool refs | Reference tools by path: `tools/web/agent.py` or `tools/tldr/daily_tldr_digest.py` |
| Evolution | Update existing workflows when you learn better methods |
| Ownership | Don't overwrite workflows without user approval |
