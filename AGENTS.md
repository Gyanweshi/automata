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
- Startup-safe MCP config: `.mcp.json` (intentionally empty by default)
- Agent-scoped MCP maps: `mcp/agents/research.json`, `mcp/agents/storyboard.json`
- Agent behavior docs: `skills/agency-*/SKILL.md`
- Brand configs: `$OBSIDIAN_VAULT_PATH/Brands/<slug>.md` — frontmatter is the agent config, body is the brand narrative and memory (not committed to repo)
- Durable research, results, briefs, scripts, captions, plans, and other knowledge Markdown: `$OBSIDIAN_VAULT_PATH/` (use `D:\Brainiac2` as the Windows fallback when unset)
- Temporary generated working files: `workspace/<brand-slug>/research/`, `workspace/<brand-slug>/storyboards/`, `workspace/<brand-slug>/content/`

## Vault-First Output Policy

- The vault is the final home for research, results, briefs, scripts, captions, content plans, storyboard notes, and other human-readable knowledge artifacts.
- Code, tests, packages, runtime configuration, caches, and disposable intermediates remain in the repo.
- Repo `workspace/` outputs and root working copies are temporary. Remove agent-created duplicates after verifying the final Markdown in the vault.
- Final vault notes require YAML frontmatter with `type`, `status`, `created` or `updated`, and relevant `tags`.
- Ongoing research/project notes require a concise `## Memory` section of no more than 10 bullets covering decisions, useful findings, rejected directions, current state, and next step.
- Brand work updates `Brands/<slug>.md` memory. Non-brand research maintains memory in its research note and records durable policy in `memory/DECISIONS.md`.
- Raw browser dumps, logs, screenshots, and extraction artifacts are not final notes. Retain only for provenance in clearly named vault subfolders; never leave misleading scratch files at the repo root.

## Vault Write Gate

- Treat the vault as read-only while a task, phase, review, or visual iteration is active. Put drafts, generated options, QA notes, research reports, session logs, and other working material under `workspace/` or another repo-owned temporary directory.
- A command finishing, an image being generated, or an agent reaching the end of a turn does not mean the work is approved or final.
- Write to the vault only when the original request explicitly asks for a vault deliverable, or the user explicitly says to finalize, approve, save, publish, commit to vault, or save a checkpoint.
- For iterative visual work, finalization begins only after the user approves the selected asset or explicitly closes the phase. Do not update brand Memory while options are still being generated or reviewed.
- Vault authorization is one-shot and target-specific. Do not persist it in an environment variable or reuse it for a later run.
- On finalization, write the smallest coherent batch: the approved artifact or note, required frontmatter, and at most one distilled Memory update. Verify the vault copy before removing workspace duplicates.
- Official Python vault writers default to denied. Callers must pass `commit_vault=True` and a non-empty `commit_reason`; CLIs expose this as `--commit-vault --commit-reason "..."`.

Do not duplicate full README content in context files. Keep context operational and concise.

## Environment Rules

- Use `.venv` for Python package installs and CLI execution.
- On Linux, macOS, and WSL, prefer `make` targets.
- On Windows native, prefer PowerShell scripts in `scripts/*.ps1`.
- Do not install packages into system Python.
- Do not commit `.env`, real API keys, generated workspace outputs, virtualenvs, caches, or local editor state.

## Context Layers — Load These Before Any Brand Work

**1. Brand note** — read `$OBSIDIAN_VAULT_PATH/Brands/<slug>.md` before working on any brand. This is the single source of truth. The frontmatter is the agent config (voice, vocabulary, writing rules, audience, competitors, platforms). The markdown body contains:
- Brand essence and the one rule that matters most
- Audience and platform summaries
- `## Memory` — distilled run history, max 10 bullets, maintained automatically by agents after every run. Read this section carefully: it contains decisions already made, what worked, what was rejected, and key findings from past research. Do not ask the user to re-explain anything already in Memory.

**Do not call `search_second_brain` for brand-specific context.** The brand `.md` contains everything already. Vault RAG is reserved for broad queries — topic research, general knowledge — where the answer is not already in the brand file.

**Note for Claude Code sessions:** a third layer exists — memory files at `~/.claude/projects/.../memory/` — which are loaded automatically and contain always-on rules and preferences. Codex does not have this layer; `AGENTS.md` serves the same purpose.

## OS Commands

Linux/macOS/WSL:

```bash
bash scripts/bootstrap.sh
make status
make dry-run BRAND=example-brand
make research BRAND=example-brand
make research BRAND=example-brand PARALLEL=1 MAX_WORKERS=4
make research BRAND=example-brand SCRAPER=browser-act PLATFORMS=ig PARALLEL=1 MAX_WORKERS=4
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

Instagram login/session helpers:

```powershell
.\scripts\open-instagram-session.ps1 -Mode cdp -CdpPort 9224 -WaitForEnter
.\scripts\open-instagram-session.ps1 -Mode browser-act -BrowserActSessionName instagram-main -WaitForEnter
```

Use the CDP helper when rendered Instagram post pages hit a login wall. It opens a persistent Chrome profile under `%USERPROFILE%\.agency\chrome-instagram-cdp`; the user logs in once and keeps the browser open while CDP research runs. Use browser-act session mode with `-BrowserActMode session -BrowserActSessionName instagram-main` after its login helper has been completed.

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
- `magnific`

Content agent:

- primarily Python CLI output and brand voice files
- may use research outputs from `workspace/<brand-slug>/research/`

MCP package versions are pinned in `mcp/agents/*.json`. Keep README and agent manifests synchronized if updated.

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
- `.mcp.json` is intentionally empty so MCP clients that auto-load project configs do not start every server at session startup. Use `mcp/agents/*.json` as the source for opt-in server registration.
- Blender MCP requires Blender and the MCP addon to be installed and running outside this repo.
- API keys belong in environment variables or local `.env`, never in committed config.
- `.agents` and `.codex` directories may be read-only in some harnesses. Use repo-owned `AGENTS.md`, `skills/`, and `mcp/agents/` as portable context.

## Dirty Worktree Policy

This repo may contain user-local changes such as generated `workspace/*` outputs. Do not revert unrelated changes unless explicitly asked.
