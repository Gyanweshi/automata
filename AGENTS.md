# Agent Context

This file is for AI coding agents working in this repo. Human onboarding lives in `README.md`.

## Repo Purpose

This is an agency multi-agent monorepo for:

- brand research
- visual storyboard planning
- social content generation
- MCP-backed web research, browser automation, and visual asset workflows

## Source Of Truth

- Human setup and usage guide: `README.md`
- Aggregate MCP config: `.mcp.json`
- Agent-scoped MCP maps: `mcp/agents/research.json`, `mcp/agents/storyboard.json`
- Agent behavior docs: `skills/agency-*/SKILL.md`
- Brand configs: `$OBSIDIAN_VAULT_PATH/Brands/*.yaml` (not committed to repo)
- Generated outputs: `workspace/research/`, `workspace/storyboards/`, `workspace/content/`

Do not duplicate full README content in context files. Keep context operational and concise.

## Environment Rules

- Use `.venv` for Python package installs and CLI execution.
- On Linux, macOS, and WSL, prefer `make` targets.
- On Windows native, prefer PowerShell scripts in `scripts/*.ps1`.
- Do not install packages into system Python.
- Do not commit `.env`, real API keys, generated workspace outputs, virtualenvs, caches, or local editor state.

## Context Layers — Load These Before Any Brand Work

**1. Brand note** — read `$OBSIDIAN_VAULT_PATH/Brands/<slug>.md` before working on any brand. Frontmatter is the authoritative config. The markdown body has the brand essence, key constraints, audience, and competitors.

**2. Vault RAG** — call `search_second_brain` proactively. Specific triggers:
- Before writing content → `"<brand> content style campaigns"`
- Before research → `"<brand> competitors research findings"`
- Before storyboard → `"<brand> visual direction"`
- Any mention of history, "last time", "same as before", "that campaign", "what we decided"
- Any strategic decision — search first to avoid contradicting what's already agreed

Synthesise retrieved context directly into your work. Never say "according to your notes" — just use it.

**Note for Claude Code sessions:** a third layer exists — memory files at `~/.claude/projects/.../memory/` — which are loaded automatically and contain always-on rules and preferences. Codex does not have this layer; `AGENTS.md` serves the same purpose.

## OS Commands

Linux/macOS/WSL:

```bash
bash scripts/bootstrap.sh
make status
make dry-run BRAND=example-brand
make research BRAND=example-brand
make storyboard BRAND=example-brand TYPE=carousel TOPIC="5 tips"
make content BRAND=example-brand TYPE=carousel TOPIC="5 tips"
make pipeline BRAND=example-brand TYPE=carousel TOPIC="5 tips"
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
.\scripts\run-agent.ps1 status
.\scripts\run-agent.ps1 dry-run -Brand example-brand
.\scripts\run-agent.ps1 research -Brand example-brand
.\scripts\run-agent.ps1 storyboard -Brand example-brand -Type carousel -Topic "5 tips"
.\scripts\run-agent.ps1 content -Brand example-brand -Type carousel -Topic "5 tips"
.\scripts\run-agent.ps1 pipeline -Brand example-brand -Type carousel -Topic "5 tips"
```

## MCP Assignments

Research agent:

- `perplexity`
- `playwright`
- `firecrawl`
- `chrome-devtools`
- `apify`

Storyboard agent:

- `freepik-fastmcp`
- `blender`

Content agent:

- primarily Python CLI output and brand voice files
- may use research outputs from `workspace/research/<brand-slug>/`

MCP package versions are pinned in `.mcp.json` and `mcp/agents/*.json`. Keep them synchronized if updated.

## Verification Checklist

After setup-script, MCP-config, README, or agent-context changes, run what applies:

```bash
bash -n scripts/bootstrap.sh
bash -n scripts/setup-mcp.sh
python3 -m json.tool .mcp.json
python3 -m json.tool mcp/agents/research.json
python3 -m json.tool mcp/agents/storyboard.json
python3 -m json.tool .devcontainer/devcontainer.json
make status
make dry-run BRAND=example-brand
```

If PowerShell is available, also run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -SkipPlaywrightBrowser
.\scripts\run-agent.ps1 status
.\scripts\run-agent.ps1 dry-run -Brand example-brand
```

## Known Caveats

- `README.md` uses collapsible sections as README-safe OS selection buttons. GitHub Markdown does not allow arbitrary JavaScript buttons.
- `.mcp.json` env interpolation is common but not universal. If a harness does not support it, copy `command`, `args`, and `env` into that harness's native MCP config format.
- Blender MCP requires Blender and the MCP addon to be installed and running outside this repo.
- API keys belong in environment variables or local `.env`, never in committed config.
- `.agents` and `.codex` directories may be read-only in some harnesses. Use repo-owned `AGENTS.md`, `skills/`, and `mcp/agents/` as portable context.

## Dirty Worktree Policy

This repo may contain user-local changes such as generated `workspace/*` outputs. Do not revert unrelated changes unless explicitly asked.
