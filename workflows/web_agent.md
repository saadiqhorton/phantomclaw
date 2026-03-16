# Web Agent Workflow

**Objective**: Search the web and gather information from multiple sources like a human would. Combines search + scraping to provide comprehensive, synthesized results.

## Inputs
- `query`: The search query string
- `num_results` (optional): Number of search results to retrieve (default: 5)
- `visit` (optional): Number of results to visit/fetch (default: 3)
- `synthesize` (optional): Whether to attempt AI synthesis (default: false)

## Steps
1. Run `python tools/web/agent.py "<query>"` with optional flags:
   - `-n <num>` for number of search results
   - `-v <num>` for number of pages to visit
   - `-s` to enable AI synthesis
   - `-f text` for human-readable output

2. The tool first queries SEARXNG (primary) or DuckDuckGo (fallback)

3. The tool fetches content from the top results using web scraping

4. If `--synthesize` is enabled, the tool uses OPENAI_API_KEY or MINIMAX_API_KEY to synthesize a summary

## Outputs
- **JSON**: Contains `query`, `search_results`, `visited` (with extracted content), and optionally `summary`
- **Text**: Human-readable format with summary or visited content

## Configuration
Add to `.env`:
```
SEARXNG_URL=http://192.168.1.201:8080
OPENAI_API_KEY=your_key  # optional, for synthesis
# or
MINIMAX_API_KEY=your_key
```

## Dependencies
```bash
pip install requests beautifulsoup4
```

## Edge Cases
- **SEARXNG unavailable**: Automatically falls back to DuckDuckGo HTML
- **Page fetch fails**: Records error in results, continues with remaining pages
- **AI synthesis fails**: Continues without synthesis, returns raw scraped content
- **No API key**: Synthesis is skipped, returns raw data for agent to process