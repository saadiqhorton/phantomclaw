# Tools

Python scripts that handle deterministic execution. Each script should:

- Accept clearly named CLI args or read from `.env`
- Print structured output (JSON preferred) so the agent can parse results
- Exit with code `0` on success, non-zero on failure
- Be independently testable (`python tools/my_tool.py --help`)

## Structure

Tools are organized into subpackages by domain:

| Package | Purpose |
|---|---|
| `tools/web/` | Web search and scraping (agent.py, search/, scrape/) |
| `tools/tldr/` | TLDR newsletter fetching and digest |
| `tools/lobster/` | Movie/TV streaming search |
| `tools/*.py` | Standalone utilities (repo_sentinel, bridge, etc.) |

## Conventions

| Convention | Detail |
|---|---|
| Credentials | Read from `.env` via `python-dotenv` |
| Output | `print(json.dumps({...}))` for structured data |
| Errors | `sys.exit(1)` with a descriptive message to stderr |
| Naming | `verb_noun.py` — e.g. `scrape_website.py`, `export_sheet.py` |
| Packages | Use `tools/domain/` for related tools with internal modules |
