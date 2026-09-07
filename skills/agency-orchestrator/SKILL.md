---
name: agency-orchestrator
description: Route and coordinate agency brand onboarding, research, storyboard, content, calendar, status, and full-pipeline requests across the repo's specialized agents.
---

# Agency Orchestrator - Master Skill

You are the master orchestrator for the agency multi-agent system. Route commands to the correct sub-agent skill.

## Available Commands

### Brainstorm creative routes

`/agency ideate <brand-slug> "<brief>"`

Read `skills/agency-ideation/SKILL.md` and use its mechanism bank to create distinct
concept routes. This is a conversational skill command, not a Python CLI subcommand.
Carry the chosen concept ID, proposition, brand role, and tool IDs into both
storyboard and content work. A recommendation remains distinct from user approval.

### Onboard a new brand

`/agency onboard <brand-name>`

1. Ask the user for: brand name, website URL (optional), Instagram handle, LinkedIn handle, competitors (Instagram handles, LinkedIn company URLs).
2. Ask about target audience, voice (formal/casual scale 1-10), archetype (authority/innovator/friend/rebel/guide).
3. If they provide a website URL, run `/market brand <url>` to auto-detect voice dimensions.
4. Write the brand profile as `$OBSIDIAN_VAULT_PATH/Brands/<slug>.md`. Frontmatter contains the structured config; markdown body contains human-readable brand narrative and memory. Never write real brand files to the repo.
5. The `.md` body must include these sections in order: `## Audience`, `## Platforms` (external links, not wikilinks), `## Competitors` (external links), `## Strategy Notes` (initial decisions from onboarding), `## Memory` (empty block with comment `<!-- Maintained automatically by agents. Max 10 bullets. -->` - do not populate manually).
6. Create workspace folders for JSON and disposable intermediates: `workspace/<slug>/research/`, `workspace/<slug>/storyboards/`, `workspace/<slug>/content/`. Human-readable drafts go to the matching brand folders in the vault.
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

Run the research and execution CLIs for a brand and topic. Concept development is an
agent-led gate between them; it is not currently a Python CLI stage.

1. Read `$OBSIDIAN_VAULT_PATH/Brands/<brand-slug>.md`, especially `## Memory`, before deciding whether to reuse prior outputs.
2. `agency-research --brand <brand-slug> --workspace ./workspace` (skip if already run today unless the user asks for fresh research).
   - For Instagram login walls, use `scripts/open-instagram-session.ps1` and rerun with `--scraper cdp` or browser-act session mode instead of repeatedly retrying blocked public pages.
3. Read the research `evidence_readiness` object before downstream work. If it is
   `blocked`, surface missing, stale, irrelevant, or unreliable inputs and stop the
   dependent storyboard/content path. Ask for the smallest next action. If it is
   `provisional`, continue only with explicit hypotheses and tests; `ready` permits
   normal strategy work. This readiness gate is upstream of ideation, not a storyboard
   afterthought.
4. If concept development is needed and no concept is selected, pause the CLI sequence
   and apply `skills/agency-ideation/SKILL.md`, consuming the research readiness
   object. Resume only with a selected concept handoff. This conversational step is
   intentionally outside the CLI numbering because the Python commands do not ingest
   its JSON automatically.
5. `agency-storyboard --brand <brand-slug> --type <content-type> --topic "<topic>" --workspace ./workspace`
   - Storyboard is the execution stage: run it only after a selected concept or an
     explicitly execution-only brief. Do not use it to silently resolve strategy gaps.
6. `agency-content --brand <brand-slug> --platform instagram --type <content-type> --topic "<topic>" --workspace ./workspace`
7. Read all outputs and synthesize a complete content package:
   - Research brief (competitor insights, trending hashtags)
   - Storyboard (scenes + generation prompts)
   - Written content (2 variations)
   - Visual prompts ready for the configured image/video generation tooling

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

## Hybrid finalization boundary

Delegated agents write human-readable notes to the vault with `status: draft`; JSON,
browser artifacts, generated variants, and other disposable intermediates stay in
`workspace/`. Do not treat completion of a pipeline step, tool call, generation, or chat
turn as permission to mark a note final, promote an asset, or update canonical Memory.
Those actions require explicit user approval, an explicit checkpoint request, or an
original request for a final deliverable. Finalize in one coherent batch with a one-shot
reason; never carry authorization into the next phase or run.

## Skills Directory

To install all repo skills as symlinks in Claude Code:

```bash
bash scripts/install-skills.sh
```

This creates symlinks from `skills/agency-*/` to `~/.claude/skills/agency-*/`.

Codex should read `AGENTS.md` and these repo-owned `skills/agency-*/SKILL.md` files directly when working in this workspace.
