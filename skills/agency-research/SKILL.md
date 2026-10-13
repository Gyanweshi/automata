---
name: agency-research
description: Research competitors, social trends, audience sentiment, and current brand context when the user asks for agency research, competitor analysis, platform research, or research-backed content recommendations.
---

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
   agency-research --brand <brand-slug> --workspace ./workspace [--platforms <list>] [--post-count 20] [--scraper playwright|cdp|apify|browser-act] [--playwright-post-dwell-seconds 1.5] [--browser-act-proxy-region US] [--browser-act-mode stealth|session] [--browser-act-session-name instagram-main] [--instagram-login-mode auto|manual] [--parallel --max-workers 4]
   ```

   The CLI's hardcoded default is `cdp` (drives a logged-in Chrome DevTools session via the in-repo `agents/automata_core/ig-research` tool — see `scripts/open-instagram-session.ps1 -Mode cdp`), but `playwright` is the recommended choice for Instagram: it is the only scraper that reads the real caption, like count, comment count, and date off each post's `og:description` meta tag (CDP only gets engagement counts, no captions). No Apify token needed for either. On a one-time first run, do `--instagram-login-mode manual` to open a visible browser and log in once — it's saved to `~/.agency/ig_session.json` and reused after that. If captions/likes come back empty on a slow connection, raise `--playwright-post-dwell-seconds` (default 1.5s) to give each post page more time to settle before reading it.

   Use `browser-act` for stealth/session extraction, or `apify` for managed scraping (requires `APIFY_API_TOKEN`) — neither is needed for normal Instagram research.

   If Instagram rendered pages hit a login wall, do not keep retrying public extraction. Ask the user to complete the one-time login helper, then rerun with the matching scraper:

   ```powershell
   .\scripts\run-agent.ps1 research -Brand <brand-slug> -Scraper playwright -InstagramLoginMode manual -Platforms ig
   .\scripts\open-instagram-session.ps1 -Mode cdp -CdpPort 9222 -WaitForEnter
   .\scripts\run-agent.ps1 research -Brand <brand-slug> -Scraper cdp -Platforms ig
   ```

   Use `--parallel --max-workers 4` when the brand has multiple independent sources or competitors to research. Add `--notebooklm` to feed the markdown report into a NotebookLM notebook for AI synthesis. Use `--dry-run` first if the user just wants to verify config.

5. **Read and synthesize results**: After the CLI writes machine-readable JSON to workspace and a Markdown draft to the vault, read the latest data with:
   ```bash
   agency-research --brand <brand-slug> --latest --format json
   ```
   Then synthesize a concise research brief covering:
   - Top competitor insights (followers, engagement rate, content types)
   - Top trending hashtags with trend direction
   - Key content themes
   - Audience sentiment breakdown
   - Recommendations for the brand based on findings

   Every research run must also emit an `evidence_readiness` object in the JSON and
   Markdown synthesis. Use the canonical contract in
   [references/evidence-readiness.md](references/evidence-readiness.md) to gate
   strategy and creative work. Use `blocked` when a missing or unreliable input could
   materially change the audience, problem, proposition, differentiation, offer, or
   claim; `provisional` when ideation requires explicit hypotheses; and `ready` when
   the next decision is adequately supported. Link claims to evidence IDs and dates.

6. **Output**: The raw JSON (including `evidence_readiness`) is in
   `workspace/<brand-slug>/research/`. The Markdown report is in
   `$OBSIDIAN_VAULT_PATH/Brands/<brand-slug>/Drafts/Research/` with `status: draft`.
   Mention both paths and surface blockers before suggesting ideation or execution.

## Platform Notes

- **Instagram**: use `playwright` — local browser-based scraping that captures real captions/likes/comments via `og:description`, one-time manual login. `cdp` (CLI default) works off a user-logged-in Chrome profile via `scripts/open-instagram-session.ps1` but only gets engagement counts, no captions. `browser-act` for stealth/session extraction or `apify` for managed scraping are available but unnecessary for normal use.
- **LinkedIn** (Apify): requires `APIFY_API_TOKEN` env var. If missing, skip with a note.
- **Facebook** (Graph API + Apify): owned pages need `FB_PAGE_ACCESS_TOKEN`; competitor pages need `APIFY_API_TOKEN`.

## Standalone Use

This agent can be used without any other agents. It only needs a brand config and API credentials.

## Hybrid vault finalization

Normal research runs write the human-readable report to the vault with `status: draft`;
raw JSON and extraction artifacts stay in `workspace/`. Do not update brand Memory merely
because scraping or synthesis finished. When the user approves/finalizes the result, or
requested a final vault deliverable from the start, use
`--commit-vault --commit-reason "<approval or request>"` to write the report as final and
make one concise Memory update. Never update Memory during ongoing research or revision.

## MCP Integrations

Agent-scoped MCP configuration is stored in `mcp/agents/research.json`. Use these MCPs when deeper live research is needed:

- **Playwright** - browser automation for public pages, screenshots, form flows, and page extraction.
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
