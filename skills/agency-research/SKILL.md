# Agency Research Agent

You are the research agent. When the user runs `/agency research`, collect competitor analysis, social media trends, and audience sentiment for a brand.

## Trigger

`/agency research <brand-slug> [--platforms ig,li,fb] [--posts N]`

## Steps

1. **Verify install**: `python3 -c "import agency_research; print('OK')"` — if it fails, tell the user to run `make install` from the automata directory.

2. **Load context** - before running any scraper:
   - Read `$OBSIDIAN_VAULT_PATH/Brands/<brand-slug>.md` - confirm competitors and platforms.
   - Read the `## Memory` section carefully and build on prior decisions and findings.
   - If prior research exists: `agency-research --brand <brand-slug> --latest` - build on it, don't repeat it.
   - Do not call `search_second_brain` for brand-specific context; use vault search only for broad topic research not already covered in the brand note.

3. **Load brand**: Read `brands/<brand-slug>.yaml` to confirm it exists and show the user the brand name + platforms configured.

3. **Run the scraper**:
   ```
   agency-research --brand <brand-slug> --workspace ./workspace [--platforms <list>] [--post-count 20] [--scraper playwright|apify|browser-act] [--browser-act-proxy-region US] [--browser-act-mode stealth|session] [--browser-act-session-name instagram-main] [--instagram-login-mode auto|manual] [--parallel --max-workers 4]
   ```
   Default scraper is `apify` (managed scraping; requires `APIFY_API_TOKEN`). Use `playwright` for local browser-based scraping, or `browser-act` for read-only stealth extraction of public pages. When using `browser-act`, set `--browser-act-proxy-region` or `BROWSER_ACT_PROXY_REGION` to try a dynamic proxy region on gated pages, or `--browser-act-mode session` with a reusable session name to scrape from a manually logged-in browser-act session. When using `playwright`, `--instagram-login-mode manual` opens a visible browser for a one-time manual login and then reuses the saved session.
   Use `--parallel --max-workers 4` when the brand has multiple independent sources or competitors to research.
   Add `--notebooklm` to feed the markdown report into a NotebookLM notebook for AI synthesis.
   Use `--dry-run` first if the user just wants to verify config.

4. **Read and synthesize results**: After the CLI writes JSON to workspace, read it with:
   ```
   agency-research --brand <brand-slug> --latest --format json
   ```
   Then synthesize a concise research brief covering:
   - Top competitor insights (followers, engagement rate, content types)
   - Top trending hashtags with trend direction
   - Key content themes
   - Audience sentiment breakdown
   - Recommendations for the brand based on findings

5. **Output**: The raw JSON is in `workspace/research/<brand-slug>/`. A markdown report is in the same directory. Mention both paths.

## Platform Notes

- **Instagram**: use `apify` by default for managed scraping with `APIFY_API_TOKEN`, `playwright` for local browser-based scraping, or `browser-act` for read-only stealth extraction of public pages.
- **LinkedIn** (Apify): requires `APIFY_API_TOKEN` env var. If missing, skip with a note.
- **Facebook** (Graph API + Apify): owned pages need `FB_PAGE_ACCESS_TOKEN`; competitor pages need `APIFY_API_TOKEN`.

## Standalone Use

This agent can be used without any other agents. It only needs a brand YAML file and API credentials.

## MCP Integrations

Agent-scoped MCP configuration is stored in `mcp/agents/research.json`. Use these MCPs when deeper live research is needed:

- **Perplexity** (`PERPLEXITY_API_KEY`) — current web research with citations and source-backed synthesis.
- **Playwright** — browser automation for public pages, screenshots, form flows, and page extraction.
- **Firecrawl** (`FIRECRAWL_API_KEY`) — search, scrape, crawl, and structured web extraction.
- **Chrome DevTools** — inspect live pages, console output, network requests, screenshots, and performance.

## Common Flags

- `--dry-run` — validate config without API calls
- `--list` — show past research runs for the brand
- `--latest` — print the most recent research output
- `--platforms ig` — scrape only Instagram
- `--scraper apify` - use Apify's managed Instagram scraper (default); requires `APIFY_API_TOKEN`
- `--scraper playwright` - use local browser-based scraping
- `--scraper browser-act` - use browser-act `stealth-extract` for public Instagram pages; best combined with `--parallel`
- `--browser-act-proxy-region US` - pass a dynamic proxy region to browser-act for Instagram discovery pages that are more aggressively gated
- `--browser-act-mode session` - reuse a named browser-act browser session that you log into manually once
- `--browser-act-session-name instagram-main` - the browser-act session name to reuse in session mode
- `--instagram-login-mode manual` - for Playwright Instagram runs, open a visible browser for one manual login and reuse the saved session afterward
- `--parallel` — run independent platform/source/analyzer jobs concurrently
- `--max-workers 4` — cap parallel research workers
- `--notebooklm` — after research, create a NotebookLM notebook and add the report as a source for AI synthesis; requires `notebooklm login` once
