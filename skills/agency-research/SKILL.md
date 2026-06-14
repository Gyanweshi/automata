# Agency Research Agent

You are the research agent. When the user runs `/agency research`, collect competitor analysis, social media trends, and audience sentiment for a brand.

## Trigger

`/agency research <brand-slug> [--platforms ig,li,fb] [--posts N]`

## Steps

1. **Verify install**: `python3 -c "import agency_research; print('OK')"` - if it fails, tell the user to run `make install` from the automata directory.

2. **Load context** - before running any scraper:
   - Read `$OBSIDIAN_VAULT_PATH/Brands/<brand-slug>.md`. This is the single source of truth for brand-specific context. Frontmatter is the agent config; the body contains brand narrative and memory.
   - Read the `## Memory` section carefully and build on prior decisions, what worked, what was rejected, and key findings from past research.
   - If prior research exists, run `agency-research --brand <brand-slug> --latest` and build on it instead of repeating it.
   - Do not call `search_second_brain` for brand-specific context. Use vault search only for broad topic research not already covered in the brand note.

3. **Load brand config**: Use `--dry-run` or the resolved brand config to confirm the brand exists, then show the user the brand name and configured platforms. Brand configs normally resolve from `$OBSIDIAN_VAULT_PATH/Brands/<brand-slug>.md`; local `brands/<brand-slug>.yaml` is a fallback/development fixture.

4. **Run the scraper**:
   ```bash
   agency-research --brand <brand-slug> --workspace ./workspace [--platforms <list>] [--post-count 20] [--scraper playwright|apify|browser-act|cdp] [--browser-act-proxy-region US] [--browser-act-mode stealth|session] [--browser-act-session-name instagram-main] [--instagram-login-mode auto|manual] [--parallel --max-workers 4]
   ```

   Default scraper is `apify` (managed scraping; requires `APIFY_API_TOKEN`). Use `playwright` for local browser-based scraping, `browser-act` for browser-act extraction, or `cdp` for a logged-in Chrome DevTools session. When using `browser-act`, set `--browser-act-proxy-region` or `BROWSER_ACT_PROXY_REGION` to try a dynamic proxy region on gated pages, or use `--browser-act-mode session` with a reusable session name. When using `playwright`, `--instagram-login-mode manual` opens a visible browser for a one-time manual login and then reuses the saved session.
   agency-research --brand <brand-slug> --workspace ./workspace [--platforms <list>] [--post-count 20] [--scraper cdp|playwright|browser-act] [--browser-act-proxy-region US] [--browser-act-mode stealth|session] [--browser-act-session-name instagram-main] [--instagram-login-mode auto|manual] [--parallel --max-workers 4]
   ```

   Default scraper is `cdp` (drives a logged-in Chrome DevTools session via the in-repo `agents/automata_core/ig-research` tool — see `scripts/open-instagram-session.ps1 -Mode cdp`). Use `playwright` for local browser-based scraping, or `browser-act` for browser-act extraction. When using `browser-act`, set `--browser-act-proxy-region` or `BROWSER_ACT_PROXY_REGION` to try a dynamic proxy region on gated pages, or use `--browser-act-mode session` with a reusable session name. When using `playwright`, `--instagram-login-mode manual` opens a visible browser for a one-time manual login and then reuses the saved session.

   If Instagram rendered pages hit a login wall, do not keep retrying public extraction. Ask the user to complete the one-time login helper, then rerun with the matching scraper:

   ```powershell
   .\scripts\open-instagram-session.ps1 -Mode cdp -CdpPort 9224 -WaitForEnter
   .\scripts\open-instagram-session.ps1 -Mode cdp -WaitForEnter
   .\scripts\run-agent.ps1 research -Brand <brand-slug> -Scraper cdp -Platforms ig
   .\scripts\open-instagram-session.ps1 -Mode browser-act -BrowserActSessionName instagram-main -WaitForEnter
   .\scripts\run-agent.ps1 research -Brand <brand-slug> -Scraper browser-act -Platforms ig -BrowserActMode session -BrowserActSessionName instagram-main
   ```

   Use `--parallel --max-workers 4` when the brand has multiple independent sources or competitors to research. Add `--notebooklm` to feed the markdown report into a NotebookLM notebook for AI synthesis. Use `--dry-run` first if the user just wants to verify config.

5. **Read and synthesize results**: After the CLI writes JSON to workspace, read it with:
   ```bash
   agency-research --brand <brand-slug> --latest --format json
   ```
   Then synthesize a concise research brief covering:
   - Top competitor insights (followers, engagement rate, content types)
   - Top trending hashtags with trend direction
   - Key content themes
   - Audience sentiment breakdown
   - Recommendations for the brand based on findings

6. **Output**: The raw JSON is in `workspace/<brand-slug>/research/`. A markdown report is in the same directory. Mention both paths.

## Platform Notes

- **Instagram**: use `apify` by default for managed scraping with `APIFY_API_TOKEN`, `playwright` for local browser-based scraping, `browser-act` for stealth/session extraction, or `cdp` for a user-logged-in Chrome profile opened by `scripts/open-instagram-session.ps1`.
- **Instagram**: use `cdp` by default (a user-logged-in Chrome profile opened by `scripts/open-instagram-session.ps1`), `playwright` for local browser-based scraping, or `browser-act` for stealth/session extraction.
- **LinkedIn** (Apify): requires `APIFY_API_TOKEN` env var. If missing, skip with a note.
- **Facebook** (Graph API + Apify): owned pages need `FB_PAGE_ACCESS_TOKEN`; competitor pages need `APIFY_API_TOKEN`.

## Standalone Use

This agent can be used without any other agents. It only needs a brand config and API credentials.

## MCP Integrations

Agent-scoped MCP configuration is stored in `mcp/agents/research.json`. Use these MCPs when deeper live research is needed:

- **Perplexity** (`PERPLEXITY_API_KEY`) - current web research with citations and source-backed synthesis.
- **Playwright** - browser automation for public pages, screenshots, form flows, and page extraction.
- **Firecrawl** (`FIRECRAWL_API_KEY`) - search, scrape, crawl, and structured web extraction.
- **Chrome DevTools** - inspect live pages, console output, network requests, screenshots, and performance.
- **Apify** (`APIFY_API_TOKEN`) - managed Actor-backed scraping for social and web workflows.
- **NotebookLM** - optional source-grounded synthesis when `--notebooklm` is used and the user has logged in.

## Common Flags

- `--dry-run` - validate config without API calls
- `--list` - show past research runs for the brand
- `--latest` - print the most recent research output
- `--platforms ig` - scrape only Instagram
- `--scraper apify` - use Apify's managed Instagram scraper (default); requires `APIFY_API_TOKEN`
- `--scraper playwright` - use local browser-based scraping
- `--scraper browser-act` - use browser-act extraction for public or session-backed Instagram pages; best combined with `--parallel`
- `--scraper cdp` - use a Chrome DevTools Protocol session opened by `scripts/open-instagram-session.ps1`
- `--scraper cdp` - use a Chrome DevTools Protocol session opened by `scripts/open-instagram-session.ps1` (default)
- `--scraper playwright` - use local browser-based scraping
- `--scraper browser-act` - use browser-act extraction for public or session-backed Instagram pages; best combined with `--parallel`
- `--browser-act-proxy-region US` - pass a dynamic proxy region to browser-act for Instagram discovery pages that are more aggressively gated
- `--browser-act-mode session` - reuse a named browser-act browser session that you log into manually once
- `--browser-act-session-name instagram-main` - the browser-act session name to reuse in session mode
- `--instagram-login-mode manual` - for Playwright Instagram runs, open a visible browser for one manual login and reuse the saved session afterward
- `--parallel` - run independent platform/source/analyzer jobs concurrently
- `--max-workers 4` - cap parallel research workers
- `--notebooklm` - after research, create a NotebookLM notebook and add the report as a source for AI synthesis; requires `notebooklm login` once
