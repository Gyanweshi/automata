# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## First action for every task

Read and follow `AGENTS.md`, especially **First Action — Discover Skills and Agents**.
Check matching skills and existing specialists before planning or execution, even
when no slash command is used. Follow required references, preserve project
decisions, and use the applicable workflow without waiting for the user to name it.
This applies across all domains and on every fresh session or material scope change.

## Output Location — Hybrid Vault Policy

Human-readable research, brand work, briefs, scripts, and project notes go directly to the Obsidian vault at `D:\Brainiac2`. Active notes use `status: draft`; approval changes them to `status: final`. Canonical brand Memory remains approval-gated.

| What | Where in vault |
|------|---------------|
| Research (LinkedIn, competitor, market) | `D:\Brainiac2\Research\<topic>\` |
| Brand work (copy, storyboards, content) | `D:\Brainiac2\Brands\<slug>\` |
| Agent pipeline Markdown drafts | `D:\Brainiac2\Brands\<slug>\Drafts\<type>\` |
| Agent pipeline JSON outputs | `D:\automata\workspace\` (temporary inter-agent data) |
| Games / side projects | `D:\Brainiac2\Games\<name>\` |
| Spreadsheets / exports | `D:\Brainiac2\Research\<topic>\` |

Use `D:\automata\workspace\` for machine-readable JSON, browser dumps, logs, screenshots, cookies, browser profiles, masks, previews, generated variants, and other disposable or high-volume intermediates. Do not leave human-readable knowledge drafts or deliverables in the repo.

## Commands

```bash
# First-time setup
bash scripts/bootstrap.sh       # Install Python/Node deps, create .venv
make install                    # Install all packages in editable mode
make install-skills             # Register repo skills for Codex and Claude

# Trigger agents interactively
python run.py                   # Interactive launcher — asks brand, action, topic

# Trigger agents directly
make research BRAND=my-client
make storyboard BRAND=my-client TYPE=carousel TOPIC="5 tips"
make content BRAND=my-client TYPE=carousel TOPIC="5 tips"
make pipeline BRAND=my-client TYPE=carousel TOPIC="5 tips"
make week BRAND=my-client       # Full weekly content calendar
make dry-run BRAND=my-client    # Validate config, zero API calls

# Tests
make test                       # pytest packages/*/tests -v
make vault-index                # Rebuild the chunked vault search index now
make install-vault-index        # Schedule the nightly rebuild (02:30)
make vault-search Q="..."       # Search the vault index from the shell
make rag-eval                   # Score retrieval: legacy whole-note index vs v2
.venv/bin/python -m pytest packages/agency-common/tests/test_brand_loader.py -v

# Utilities
make status                     # Show installed package versions
make clean                      # Clear workspace/ outputs
```

Windows PowerShell equivalents are in `scripts/*.ps1` (see AGENTS.md).

## Architecture

Four pip-installable packages, each a standalone CLI agent:

```
packages/agency-common/     # Shared Pydantic models, config, workspace I/O, brand loading
packages/agency-research/   # Competitor scraping, trend/sentiment analysis
packages/agency-storyboard/ # Scene building, visual direction, AI image-gen prompts
packages/agency-content/    # Multi-platform social copy generation
```

**Data flow**: Brand YAML → agent CLI → JSON written to `workspace/{brand}/{agent}/{timestamp}.json`. Downstream agents call `workspace.read_latest(agent, brand)` to consume upstream outputs. Agents are decoupled — they share state through the filesystem only, no direct cross-package imports.

## HTML → PPTX export

`tools/pdf_utils/html_to_pptx.js` is the **only** HTML-slide-deck-to-pptx tool — it is generic (`--input`, `--output`, `--scale`, `--format`, `--quality` flags), has no hardcoded brand names, usernames, or absolute paths, and uses Playwright's bundled Chromium. If a conversion produces a bad-looking deck, fix this script's selector/wait/scale args — do not write a new brand-specific export script. Defaults are `--scale 1.5 --format jpeg --quality 90`, which keeps output decks in the low tens of MB; raising scale to 2 or format to png will blow up file size (a prior version produced a 76MB pptx from full PNG screenshots at 2x scale) without a visible quality gain for screen/projector use.

**Key files in `agency-common`**:
- `models.py` — Pydantic schemas: `BrandProfile`, `ResearchOutput`, `StoryboardOutput`, `ContentOutput`
- `workspace.py` — `WorkspaceManager`: reads/writes inter-agent JSON
- `brand_loader.py` — loads and validates brand YAML against `BrandProfile`
- `config.py` — `AgencyConfig` reads API keys from environment
- `harness_runner.py` — `HarnessRunner`: model-call → tool-call → observation loop for autonomous runs
- `autonomous_cli.py` — entry point for `agency-autonomous`, takes `--agent` and `--task` string

**Two ways to run agents**:
1. **CLI mode** (`make research` etc.) — fires immediately, all args required upfront, no interaction
2. **Autonomous mode** (`agency-autonomous --agent research --task "..."`) — runs an LLM agentic loop (default 5 iterations), calls `search_second_brain` as a tool, logs session to Obsidian

## Brand Configs

Brand profiles live in the **Obsidian vault** at `$OBSIDIAN_VAULT_PATH/Brands/<slug>.md` - not committed to the repo. The frontmatter is the structured config; the markdown body contains brand narrative and the `## Memory` section. The loader searches in this order: explicit `--brands-dir` arg, `AGENCY_BRANDS_DIR` env var, vault `Brands/` folder, then local `brands/` directory.

Use `brands/_template.yaml` as the schema reference for frontmatter. When onboarding a new brand, write the `.md` brand note to the vault and create workspace directories (`workspace/<slug>/research/`, `workspace/<slug>/storyboards/`, `workspace/<slug>/content/`). Local YAML files are development fixtures only.

**Obsidian linking rules** — only wikilink things that have actual notes:
- Other managed brands → `[[Brands/slug|Name]]`
- Session notes → `[[Agent_Sessions/Session_...|view session]]`
- Competitor handles, Instagram pages, external accounts → plain external links `[@handle](https://instagram.com/handle)`
- Never wikilink handles, hashtags, or external accounts — Obsidian creates empty stubs
- In frontmatter, always quote wikilinks and write several as a YAML list (`related: ["[[Brands/a|A]]", "[[Brands/b|B]]"]`); unquoted ones make the note unparseable and it drops out of vault search

## MCP Servers

Defined in `.mcp.json` (aggregate) and `mcp/agents/*.json` (agent-scoped). Keep versions pinned and synchronized across both files.

| Server | Assigned to | Key env var |
|---|---|---|
| `playwright` | research | — |
| `chrome-devtools` | research | — |
| `notebooklm` | research | Google login/session |
| `apify` | research | `APIFY_API_TOKEN` |
| `blender` | storyboard | requires external Blender + addon |
| `higgsfield` | storyboard | Higgsfield OAuth |
| `magnific` | storyboard | Magnific OAuth |

## Context Layers — How to Use Them

There are three layers of context. Use all three, in order, before doing any brand work:

**1. Memory files** (`~/.claude/projects/.../memory/`) — loaded automatically. Contains working rules, preferences, and brand decisions. Never ask the user to re-explain things that are already in memory.

**2. Brand note** (`$OBSIDIAN_VAULT_PATH/Brands/<slug>.md`) — read this before working on any brand. The frontmatter is the authoritative config. The markdown body has the brand essence, key constraints, audience, and the `## Memory` section — distilled run history maintained automatically by agents after every run. Read it with the `Read` tool directly. This is the single source of truth for brand-specific context.

**Do not call `search_second_brain` for brand-specific context.** The `## Memory` section in the brand note already contains what matters — past decisions, research findings, what worked, what was rejected. It is always current. Vault RAG is for broad queries only: topic research, general knowledge, things genuinely not in the brand file.

**3. Vault RAG** (`search_second_brain` tool, or `.venv/bin/agency-vault-search "query"` from the shell) — use only for broad, non-brand-specific queries: competitor landscape, topic research, industry trends. Not for "what do I know about this brand." Results cite `[[Note#Heading]]` sections from the chunked `second_brain_v2` index, rebuilt nightly per machine (`make vault-index` to refresh now). Score retrieval changes with `make rag-eval` against the vault question set at `Operations/RAG_Eval/rag-eval-questions.yaml`.

**What each layer is for:**
- Memory files = always-on rules that never change session to session
- Brand notes = current client state + distilled run history in ## Memory — always read first
- Vault RAG = broad research queries only, not brand-specific context

## Research Methodology

`skills/agency-research/METHODOLOGY.md` — practitioner guide for the human research layer. Covers what no scraper or LLM can reliably do: hypothesis formation, customer interviews, data quality judgment, triangulation, pattern recognition, and the feedback loop. Structured as a 16-week skill-building progression. Read this before designing research strategy for any client.

The automated pipeline (scraping, engagement benchmarking, content audit, hashtag landscape) handles structural facts. The methodology guide handles interpretation and strategy.

## Skills

`skills/agency-*/SKILL.md` define slash commands for Claude Code:
- `/agency-orchestrator` — master entry: onboard, pipeline, calendar, status
- `/agency-research`, `/agency-storyboard`, `/agency-content` — individual agents

Install with `make install-skills`. The orchestrator's `/agency onboard` workflow (asks questions → writes YAML → creates workspace dirs) is the standard path for adding new brand clients.

## After Changing Config or Scripts

```bash
bash -n scripts/bootstrap.sh
python3 -m json.tool .mcp.json
python3 -m json.tool mcp/agents/research.json
make status
make dry-run BRAND=example-brand
```
