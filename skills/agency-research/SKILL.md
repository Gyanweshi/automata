# Agency Research Agent

You are the research agent. When the user runs `/agency research`, collect competitor analysis, social media trends, and audience sentiment for a brand.

## Trigger

`/agency research <brand-slug> [--platforms ig,li,fb] [--posts N]`

## Steps

1. **Verify install**: `python3 -c "import agency_research; print('OK')"` — if it fails, tell the user to run `make install` from the automata directory.

2. **Load brand**: Read `brands/<brand-slug>.yaml` to confirm it exists and show the user the brand name + platforms configured.

3. **Run the scraper**:
   ```
   agency-research --brand <brand-slug> --workspace ./workspace [--platforms <list>] [--post-count 20]
   ```
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

- **Instagram** (instaloader): works for all public profiles. Rate limit ~200 req/hr.
- **LinkedIn** (Apify): requires `APIFY_API_TOKEN` env var. If missing, skip with a note.
- **Facebook** (Graph API + Apify): owned pages need `FB_PAGE_ACCESS_TOKEN`; competitor pages need `APIFY_API_TOKEN`.

## Standalone Use

This agent can be used without any other agents. It only needs a brand YAML file and API credentials.

## Common Flags

- `--dry-run` — validate config without API calls
- `--list` — show past research runs for the brand
- `--latest` — print the most recent research output
- `--platforms ig` — scrape only Instagram
