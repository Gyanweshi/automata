# Agency Orchestrator — Master Skill

You are the master orchestrator for the agency multi-agent system. Route commands to the correct sub-agent skill.

## Available Commands

### Onboard a new brand
`/agency onboard <brand-name>`

1. Ask the user for: brand name, website URL (optional), Instagram handle, LinkedIn handle, competitors (Instagram handles, LinkedIn company URLs)
2. Ask about target audience, voice (formal/casual scale 1-10), archetype (authority/innovator/friend/rebel/guide)
3. If they provide a website URL, run `/market brand <url>` to auto-detect voice dimensions
4. Write the brand profile as `$OBSIDIAN_VAULT_PATH/Brands/<slug>.md` — frontmatter contains the structured data, markdown body contains human-readable sections. Never write brand files to the repo.
5. The `.md` body must include these sections in order: `## Audience`, `## Platforms` (external links, not wikilinks), `## Competitors` (external links), `## Strategy Notes` (initial decisions from this onboarding), `## Memory` (empty block with comment `<!-- Maintained automatically by agents. Max 10 bullets. -->` — do not populate manually)
6. Create workspace folders: `workspace/research/<slug>/`, `workspace/storyboards/<slug>/`, `workspace/content/<slug>/`
7. Confirm success and show next steps

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
1. `agency-research --brand <brand-slug> --workspace ./workspace` (skip if already run today)
2. `agency-storyboard --brand <brand-slug> --type <content-type> --topic "<topic>" --workspace ./workspace`
3. `agency-content --brand <brand-slug> --platform instagram --type <content-type> --topic "<topic>" --workspace ./workspace`
4. Read all three outputs and synthesize a complete content package:
   - Research brief (competitor insights, trending hashtags)
   - Storyboard (scenes + generation prompts)
   - Written content (2 variations)
   - Visual prompts ready for Freepik MCP

### Generate a weekly calendar
`/agency calendar <brand-slug> [--week YYYY-WNN]`

1. Load the brand profile to understand content pillars and posting frequency
2. Run research if no data exists this week
3. `agency-content --brand <brand-slug> --week --format markdown`
4. Read the output and assign specific topics to each placeholder slot based on:
   - Brand content pillars (educational %, social_proof %, etc.)
   - Research-informed trending topics and hashtags
5. Present a day-by-day posting calendar

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

If any import fails, run: `make install` from the automata directory.

## Skills Directory

To install all skills as symlinks in Claude Code:
```bash
bash scripts/install-skills.sh
```

This creates symlinks from `skills/agency-*/` to `~/.claude/skills/agency-*/`.
