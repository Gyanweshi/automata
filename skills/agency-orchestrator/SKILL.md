---
name: agency-orchestrator
description: Route and coordinate agency brand onboarding, research, storyboard, content, calendar, status, and full-pipeline requests across the repo's specialized agents.
---

# Agency Orchestrator - Master Skill

You are the master orchestrator for the agency multi-agent system. Route commands to the correct sub-agent skill.

## Available Commands

### Onboard a new brand

`/agency onboard <brand-name>`

1. Ask the user for: brand name, website URL (optional), Instagram handle, LinkedIn handle, competitors (Instagram handles, LinkedIn company URLs).
2. Ask about target audience, voice (formal/casual scale 1-10), archetype (authority/innovator/friend/rebel/guide).
3. If they provide a website URL, run `/market brand <url>` to auto-detect voice dimensions.
4. Write the brand profile as `$OBSIDIAN_VAULT_PATH/Brands/<slug>.md`. Frontmatter contains the structured config; markdown body contains human-readable brand narrative and memory. Never write real brand files to the repo.
5. The `.md` body must include these sections in order: `## Audience`, `## Platforms` (external links, not wikilinks), `## Competitors` (external links), `## Strategy Notes` (initial decisions from onboarding), `## Memory` (empty block with comment `<!-- Maintained automatically by agents. Max 10 bullets. -->` - do not populate manually).
6. Create workspace folders: `workspace/<slug>/research/`, `workspace/<slug>/storyboards/`, `workspace/<slug>/content/`.
7. Confirm success and show next steps.

### Run research

`/agency research <brand-slug> [--platforms ig,li,fb]`

Delegate to the agency-research skill. The research agent scrapes competitors and trends.

### Create a storyboard

`/agency storyboard <brand-slug> <type> "<topic>"`

Delegate to the agency-storyboard skill. Generates visual scene breakdowns and AI prompts.

### Write content

`/agency content <brand-slug> <platform> <type> "<topic>"`

Delegate to the agency-content skill. Generates structured writing briefs and actual copy.

### Run the full pipeline

`/agency pipeline <brand-slug> <content-type> "<topic>"`

Run all three agents in sequence for a brand and topic:

1. Read `$OBSIDIAN_VAULT_PATH/Brands/<brand-slug>.md`, especially `## Memory`, before deciding whether to reuse prior outputs.
2. `agency-research --brand <brand-slug> --workspace ./workspace` (skip if already run today unless the user asks for fresh research).
   - For Instagram login walls, use `scripts/open-instagram-session.ps1` and rerun with `--scraper cdp` or browser-act session mode instead of repeatedly retrying blocked public pages.
3. `agency-storyboard --brand <brand-slug> --type <content-type> --topic "<topic>" --workspace ./workspace`
4. `agency-content --brand <brand-slug> --platform instagram --type <content-type> --topic "<topic>" --workspace ./workspace`
5. Read all three outputs and synthesize a complete content package:
   - Research brief (competitor insights, trending hashtags)
   - Storyboard (scenes + generation prompts)
   - Written content (2 variations)
   - Visual prompts ready for Freepik MCP

### Generate a weekly calendar

`/agency calendar <brand-slug> [--week YYYY-WNN]`

1. Load `$OBSIDIAN_VAULT_PATH/Brands/<brand-slug>.md`, including `## Memory`, to understand content pillars, posting frequency, and prior decisions.
2. Run research if no data exists this week.
3. `agency-content --brand <brand-slug> --week --format markdown`
4. Read the output and assign specific topics to each placeholder slot based on:
   - Brand content pillars (educational %, social_proof %, etc.)
   - Research-informed trending topics and hashtags
5. Present a day-by-day posting calendar.

### List brands

`/agency brands`

```bash
python3 -c "from agency_common.brand_loader import list_brands; print(list_brands())"
```

### Show brand profile

`/agency profile <brand-slug>`

```bash
python3 -c "
from agency_common.brand_loader import load_brand
import json
b = load_brand('<brand-slug>')
print(b.model_dump_json(indent=2))
"
```

### Check workspace

`/agency status`

Show latest runs for all brands:

```bash
agency-research --brand <slug> --list
agency-storyboard --brand <slug> --list
agency-content --brand <slug> --list
```

## Installation Check

Before any command, verify packages are installed:

```bash
python3 -c "import agency_common, agency_research, agency_storyboard, agency_content; print('All agents installed')"
```

If any import fails, run `make install` from the automata directory.

## Finalization boundary

All delegated agents are workspace-only by default. Do not treat completion of a
pipeline step, tool call, generation, or chat turn as permission to write reports,
session notes, project notes, or Memory to the vault. Wait for explicit user approval,
an explicit checkpoint request, or an original request that specifically requires a
vault deliverable. Finalize in one coherent batch with a one-shot reason; never carry
authorization into the next phase or run.

## Skills Directory

To install all repo skills as symlinks in Claude Code:

```bash
bash scripts/install-skills.sh
```

This creates symlinks from `skills/agency-*/` to `~/.claude/skills/agency-*/`.

Codex should read `AGENTS.md` and these repo-owned `skills/agency-*/SKILL.md` files directly when working in this workspace.
