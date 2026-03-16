# Tools

Python scripts that handle deterministic execution. Each script should:

- Accept clearly named CLI args or read from `.env`
- Print structured output (JSON preferred) so the agent can parse results
- Exit with code `0` on success, non-zero on failure
- Be independently testable (`python tools/my_tool.py --help`)

## Structure

Tools are organized into subpackages by domain:

| Package | Purpose | Entry Point |
|---|---|---|
| `tools/telegram/` | Telegram bot bridge | `bridge.py` |
| `tools/tldr/` | TLDR newsletter fetching and digest | `daily_tldr_digest.py` |
| `tools/lobster/` | Movie/TV streaming search | `lobster_stream.py` |
| `tools/web/` | Web search and scraping | `agent.py`, `search/`, `scrape/` |
| `tools/repo/` | Repository monitoring | `sentinel.py` |

## Backward Compatibility

Legacy flat paths are preserved as shims for backward compatibility:

| Legacy Path | New Location |
|---|---|
| `tools/telegram_opencode_bridge.py` | `tools/telegram/bridge.py` |
| `tools/repo_sentinel.py` | `tools/repo/sentinel.py` |

## Conventions

| Convention | Detail |
|---|---|
| Credentials | Read from `.env` via `python-dotenv` |
| Output | `print(json.dumps({...}))` for structured data |
| Errors | `sys.exit(1)` with a descriptive message to stderr |
| Naming | `verb_noun.py` — e.g. `scrape_website.py`, `export_sheet.py` |
| Packages | Use `tools/domain/` for related tools with internal modules |
