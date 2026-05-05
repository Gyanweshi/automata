# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# First-time setup
bash scripts/bootstrap.sh       # Install Python/Node deps, create .venv
make install                    # Install all packages in editable mode
make install-skills             # Symlink skills/ to ~/.claude/skills/

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
packages/freepik-fastmcp/   # Vendored Freepik MCP server (image/video)
```

**Data flow**: Brand YAML → agent CLI → JSON written to `workspace/{agent}/{brand}/{timestamp}.json`. Downstream agents call `workspace.read_latest(agent, brand)` to consume upstream outputs. Agents are decoupled — they share state through the filesystem only, no direct cross-package imports.

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

Brand profiles live in the **Obsidian vault** at `$OBSIDIAN_VAULT_PATH/Brands/<slug>.yaml` — not committed to the repo. The loader searches in this order: explicit `--brands-dir` arg → `AGENCY_BRANDS_DIR` env var → vault `Brands/` folder → local `brands/` directory.

Use `brands/_template.yaml` as the schema reference. When onboarding a new brand, write the YAML to the vault and create workspace directories (`workspace/research/<slug>/`, `workspace/storyboards/<slug>/`, `workspace/content/<slug>/`).

**Obsidian linking rules** — only wikilink things that have actual notes:
- Other managed brands → `[[Brands/slug|Name]]`
- Session notes → `[[Agent_Sessions/Session_...|view session]]`
- Competitor handles, Instagram pages, external accounts → plain external links `[@handle](https://instagram.com/handle)`
- Never wikilink handles, hashtags, or external accounts — Obsidian creates empty stubs

## MCP Servers

Defined in `.mcp.json` (aggregate) and `mcp/agents/*.json` (agent-scoped). Keep versions pinned and synchronized across both files.

| Server | Assigned to | Key env var |
|---|---|---|
| `perplexity` | research | `PERPLEXITY_API_KEY` |
| `playwright` | research | — |
| `firecrawl` | research | `FIRECRAWL_API_KEY` |
| `chrome-devtools` | research | — |
| `apify` | research | `APIFY_API_TOKEN` |
| `freepik-fastmcp` | storyboard | `FREEPIK_API_KEY` |
| `blender` | storyboard | requires external Blender + addon |

## Context Layers — How to Use Them

There are three layers of context. Use all three, in order, before doing any brand work:

**1. Memory files** (`~/.claude/projects/.../memory/`) — loaded automatically. Contains working rules, preferences, and brand decisions. Never ask the user to re-explain things that are already in memory.

**2. Brand note** (`$OBSIDIAN_VAULT_PATH/Brands/<slug>.md`) — read this before working on any brand. The frontmatter is the authoritative config. The markdown body gives the feel, the key constraint, and the audience tension. Read it with the `Read` tool directly.

**3. Vault RAG** (`search_second_brain` tool) — call this proactively, not just when asked. Specific triggers:
- Before writing any content for a brand → search `"<brand> content style campaigns"`
- Before research → search `"<brand> competitors research findings"`
- Before onboarding a new brand → search the brand name in case notes exist
- Any reference to history → "last time", "same as before", "that campaign", "what we decided"
- Any strategic decision → search first to avoid contradicting something already agreed

Synthesise what you find directly into your work. Never say "according to your notes" — just use the context.

**What each layer is for:**
- Memory files = always-on rules that never change session to session
- Brand notes = current client state, lean and accurate
- Vault RAG = deep context, past decisions, anything written in Obsidian

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
