# Agent Context

This file is for AI coding agents working in this repo. Human onboarding lives in `README.md`.

## First Action — Discover Skills and Agents

For every new request, and whenever its scope changes, check the available skills
and existing agent workflows **before planning or executing the task**. This applies
to every domain, project, agent, and workflow, not only brand or visual work.

1. Match the requested outcome against the session's skill catalog and repo
   `skills/*/SKILL.md` descriptions. Check agency skills and relevant
   `mcp/agents/` manifests. `make list-workflows` lists local skills and agent
   instruction paths; a missing discovery registration does not mean a skill is absent.
2. Read the best-matching skill and the references it requires before using tools
   for the substantive task. Follow required skill-to-skill links. Use the smallest
   relevant set; do not load every skill or force an unrelated workflow.
3. Use the existing specialist route when available and permitted. A skill, an
   agent instruction file, and a callable agent are different things: do not claim
   delegation unless it actually happened. If delegation is unavailable, follow the
   applicable instructions locally and state any material capability gap.
4. Load project context and prior decisions before execution. Preserve selected
   assets, constraints, approvals and remaining budgets across retries and handoffs.
   Reuse context already read in this session unless it changed; a follow-up does
   not require restarting a completed pipeline.
5. Briefly name the chosen skill/workflow on first use. If none fits, proceed with
   the best available method and mention the fallback when material. Do not make
   the user choose skills, repeat known context, or approve routine routing.
6. Before a consequential action, apply the chosen workflow's actual checks to the
   exact inputs. Reading a skill or writing a checklist is not proof of compliance,
   output quality, or completed review. Respect user instructions and authorization;
   discovering a skill never grants new permission to spend, publish, or send.

This is the default operating procedure, including fresh sessions and delegated
tasks. It is instruction-level routing, not a guarantee that a model will obey.
`make check-skills` verifies local registration coverage; it does not certify agent
judgment. Keep registrations current with `make install-skills`.

## Repo Purpose

This is an agency multi-agent monorepo for:

- brand research
- visual storyboard planning
- social content generation
- MCP-backed web research, browser automation, and visual asset workflows

## Source Of Truth

- Human setup and usage guide: `README.md`
- Project-level MCP config: `.mcp.json` (shared servers: `figma`, `playwright`, `blender`, `higgsfield`, `magnific`, `gimp`)
- Agent-scoped MCP maps: `mcp/agents/research.json`, `mcp/agents/storyboard.json`
- Canonical agent skills: `skills/*/SKILL.md`
- Skill discovery shims: `.agents/skills/` for Codex and `.claude/skills/` for Claude Code
- Brand configs: `$OBSIDIAN_VAULT_PATH/Brands/<slug>.md` — frontmatter is the agent config, body is the brand narrative and memory (not committed to repo)
- Durable research, results, briefs, scripts, captions, plans, and other knowledge Markdown: `$OBSIDIAN_VAULT_PATH/` (use `D:\Brainiac2` as the Windows fallback when unset)
- Machine-readable run data and disposable working files: `workspace/<brand-slug>/research/`, `workspace/<brand-slug>/storyboards/`, `workspace/<brand-slug>/content/`

## Vault Output Policy

- The vault is the working and final home for research, results, briefs, scripts, captions, content plans, storyboard notes, and other human-readable knowledge artifacts.
- Write active brand drafts under `Brands/<slug>/Drafts/<type>/` with `status: draft`. Approved notes live under `Brands/<slug>/<Type>/` with `status: final`.
- Code, tests, packages, runtime configuration, caches, and disposable intermediates remain in the repo.
- Keep machine-readable interchange JSON, browser dumps, logs, screenshots, cookies, browser profiles, masks, previews, generated variants, and other disposable or high-volume artifacts in `workspace/`.
- Repo `workspace/` outputs and root working copies are temporary. Remove agent-created duplicates after verifying any approved asset or human-readable note in the vault.
- Final vault notes require YAML frontmatter with `type`, `status`, `created` or `updated`, and relevant `tags`.
- Frontmatter must be valid YAML: quote any value containing `[[wikilinks]]`, `: `, or `#`, and write multiple links as a list, e.g. `related: ["[[Brands/a|A]]", "[[Brands/b|B]]"]`. Unquoted wikilink values break parsing and the note is silently dropped from the vault search index.
- Ongoing research/project notes require a concise `## Memory` section of no more than 10 bullets covering decisions, useful findings, rejected directions, current state, and next step.
- Brand work updates `Brands/<slug>.md` memory. Non-brand research maintains memory in its research note and records durable policy in `memory/DECISIONS.md`.
- Raw browser dumps, logs, screenshots, and extraction artifacts are not vault notes. Keep them in `workspace/`; never leave misleading scratch files at the repo root.

## Hybrid Vault Finalization

- Creating a new human-readable draft note in the vault does not require final approval. Do not silently overwrite an existing vault note.
- A command finishing, an image being generated, or an agent reaching the end of a turn does not mean the work is approved or final.
- For iterative visual work, keep generated options and review media in `workspace/`. Copy only the selected asset and necessary provenance into the vault after approval.
- Canonical brand notes, `## Memory`, final status, approved assets, and destructive overwrites remain approval-gated. Authorization is one-shot and target-specific; do not persist or reuse it.
- On finalization, promote or write the smallest coherent batch: the approved artifact or note with `status: final`, required frontmatter, and at most one distilled Memory update.
- Official Python Memory/session writers remain default-deny. Callers pass `commit_vault=True` and a non-empty `commit_reason`; CLIs expose this as `--commit-vault --commit-reason "..."`. Without that flag, CLIs write Markdown as a vault draft and JSON to `workspace/`.

Do not duplicate full README content in context files. Keep context operational and concise.

## Creative Ideation

For campaign brainstorming, creative routes, or applying Deck of Brilliance, read
`skills/agency-ideation/SKILL.md`. It provides an agency-authored mechanism bank and a shared
concept handoff for the storyboard and content skills. Preserve selected concepts
during execution. This is an agent-led skill; the standalone Python pipeline does
not automatically generate or consume ideation handoffs.

The same skill includes a separate framework bank for selected public methods from
IDEO.org, Strategyzer, Blue Ocean Strategy, and the Ehrenberg-Bass Institute. Use it
to carry evidence-linked themes, memory/distinctiveness choices, propositions,
differentiation choices, and test plans into creative routes.
The normal agent order is research (including an `evidence_readiness` handoff), then
ideation and concept selection, then storyboard and content. A blocked research
readiness result stops dependent execution; do not hide missing or stale inputs in a
storyboard.

## Cross-Platform Rule (Linux + Windows)

The same repo is used on a Linux machine and a Windows machine. Anything built on one must run on the other
without a rebuild there.

- Write new scripts and tools once, in Python (or Node where the tool is already Node). Handle OS
  differences inside them with `pathlib`, `sys.platform`/`platform.system()`, and `Path.home()`. Do not
  write a new `.sh` + `.ps1` pair; a launcher, if one is needed at all, only calls the Python.
- No machine paths in tracked code or config: no `/home/<user>`, `/mnt/<disk>`, `C:\Users\<name>`. Use
  `Path.home()`, the repo root, `workspace/`, or an env var (`OBSIDIAN_VAULT_PATH`).
- Third-party tools: install them through one Python script that picks the right build per OS
  (pattern: `scripts/deps.py` + `dependencies.toml`), with pure logic covered by tests that run on both OSes.
- Before calling work done, run `make check-cross-platform` (`python scripts/check-cross-platform.py`).
  It fails on new one-OS scripts, machine paths, and CRLF shell scripts; existing debt is listed in
  `scripts/cross-platform-baseline.txt`, so remove lines there as you migrate old scripts.
- The `Cross-platform` GitHub workflow runs the checks and tests on Ubuntu and Windows on every push.
  If you can only verify on one OS locally, say which, and point at that workflow for the other.

## Use the Repo's Tools, Not the Old Way

Each of these replaced something; reaching for the old way costs time and usually breaks on the other OS.

| Instead of | Use |
|---|---|
| `bootstrap.sh` / `.ps1` / `.cmd`, manual `pip`/`npm` installs | `uv run --no-project --python 3.12 scripts/bootstrap.py` |
| `run-agent.ps1`, `run-pipeline.sh` | `python scripts/run-agent.py <command>` (Make targets call it) |
| `install-*.sh/.ps1`, upstream installers (`curl raea.io/install`, `uv tool install browser-act-cli`) | `python scripts/deps.py install ID` (pinned, checksummed, per OS) |
| editing a version in one config file | `python scripts/deps.py set-pin ID VERSION` (moves every copy) |
| ad-hoc dependency bumps | the quarterly routine: `python scripts/deps.py update` / the Dependency update workflow |
| starting an MCP server by hand to see if it works | `python scripts/mcp-smoke.py NAME [--save/--compare]` |
| cron/Task Scheduler edits by hand | `python scripts/schedule.py install JOB` |
| a new `.sh` + `.ps1` pair | one Python script (Cross-Platform Rule) |
| guessing whether a machine is healthy | `python scripts/doctor.py` |
| any `browser-act` command first | `browser-act get-skills core --skill-version 2.0.2`, then the command |
| grepping the vault for knowledge | `.venv/bin/agency-vault-search "query"` (cited sections) |

Enforcement: a git **pre-commit** hook (installed by the bootstrap, so it applies to Claude Code, Codex and
people alike) blocks commits that break the cross-platform rules, pin agreement, the dependency register or skill
registrations; Claude Code also has a guard hook (`scripts/hooks/repo_guard.py`) that stops the clear-cut old-way
commands above before they run and names the replacement.

## Keeping Machines in Step

If the session starts with "SETUP OUT OF DATE", run the bootstrap it names before anything else and report the
doctor summary. The bootstrap records a setup stamp and installs post-merge/post-rewrite git hooks
(`scripts/setup_state.py`), so later pulls that change the setup re-run it automatically. Its automatic mode
(`--auto-schedules`) never takes over scheduled jobs registered for another checkout.

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

**2. Vault search (RAG)** — for broad questions across past research ("what did we find about insurance ads on Threads?"), search the chunked vault index from the shell instead of grepping the vault:

```bash
.venv/bin/agency-vault-search "ethanol petrol motor insurance claims" -n 3     # Linux
.venv\Scripts\agency-vault-search.exe "ethanol petrol motor insurance claims"   # Windows
```

It prints the best-matching note sections with `[[Note#Heading]]` citations; cite those, then open the note if you need more than the excerpt. The index (`chroma_db/`, collection `second_brain_v2`) is per machine and rebuilt nightly, so notes edited today may not appear until tomorrow — run `make vault-index` (or `python scripts/schedule.py run vault-index`) first if freshness matters. After changing chunking, the embedder, or search code, run `make rag-eval` and compare against the last score; add a question to `Operations/RAG_Eval/rag-eval-questions.yaml` in the vault whenever search misses a note it should have found.

**Note for Claude Code sessions:** a third layer exists — memory files at `~/.claude/projects/.../memory/` — which are loaded automatically and contain always-on rules and preferences. Codex does not have this layer; `AGENTS.md` serves the same purpose.

## OS Commands

The same commands work on both machines; only the Python launcher differs (`python3` on Linux/macOS,
`python` or `py` on Windows). Make targets are shortcuts for the Linux side.

```bash
uv run --no-project --python 3.12 scripts/bootstrap.py   # set up or repair this machine (fresh machine: see README Quick Start)
python3 scripts/doctor.py                             # check everything, step by step (read-only)
python3 scripts/setup_state.py --check                # is the setup in step with this checkout? (git hooks re-run setup after pulls)
python3 scripts/deps.py check                         # every external dependency (dependencies.toml)
python3 scripts/deps.py update --report r.md          # quarterly update routine (cool-down, no majors); CI runs it
python3 scripts/run-agent.py status
python3 scripts/run-agent.py dry-run --brand example-brand
python3 scripts/run-agent.py research --brand example-brand [--parallel --max-workers 4] [--scraper browser-act --platforms ig]
python3 scripts/run-agent.py storyboard --brand example-brand --type carousel --topic "5 tips"
python3 scripts/run-agent.py content --brand example-brand --type carousel --topic "5 tips"
python3 scripts/run-agent.py pipeline --brand example-brand --type carousel --topic "5 tips"
python3 scripts/schedule.py run vault-index           # rebuild the vault search index now
python3 scripts/schedule.py install vault-index       # nightly rebuild (systemd/cron on Linux, Task Scheduler on Windows)
python3 scripts/schedule.py install housekeeper       # nightly quarantine purge
python3 scripts/schedule.py install vault-watchdog    # session backlinks, runs from login (Linux: defers to an existing vault-watchdog.service)
```

Make equivalents: `make bootstrap`, `make deps`, `make dry-run BRAND=x`, `make research BRAND=x PARALLEL=1`,
`make pipeline BRAND=x TYPE=carousel TOPIC="5 tips"`, `make vault-index`, `make install-vault-index`.

Instagram login/session helpers:

```bash
python3 scripts/open-instagram-session.py --cdp-port 9224 --wait          # CDP: persistent Chrome/Edge profile
python3 scripts/open-instagram-session.py --mode browser-act --wait       # browser-act session
```

Use the CDP helper when rendered Instagram post pages hit a login wall. It opens the persistent profile
`~/.agency/chrome-instagram-cdp` (the same profile the Playwright MCP uses); log in once and keep the browser
open while CDP research runs. Use browser-act session mode with `--browser-act-mode session --browser-act-browser instagram-research`
after logging in once with `python3 scripts/open-instagram-session.py --mode browser-act --wait` (free; no proxy
unless `BROWSER_ACT_PROXY_REGION` is set, which costs BrowserAct credits).

## MCP Assignments

Research agent:

- `playwright`
- `chrome-devtools`
- `notebooklm`
- `apify`

Storyboard agent:

- `blender`
- `higgsfield`
- `magnific`
- `gimp` (default for all local, non-generative image editing; see `skills/image-compositing-repair/SKILL.md`)
- local CLI `raea` (not an MCP server): default 3D previz route before AI video; see `skills/previz-3d/SKILL.md`. Install or update with `python scripts/deps.py install raea` (pinned in `dependencies.toml`).

Content agent:

- primarily Python CLI output and brand voice files
- may use research outputs from `workspace/<brand-slug>/research/`

MCP package versions are pinned in `.mcp.json` and `mcp/agents/*.json` and mirrored in `dependencies.toml`; `python scripts/deps.py check --pins-only` fails when they disagree and `set-pin` moves them together. Full register: `docs/DEPENDENCIES.md`.

## Verification Checklist

After setup-script, MCP-config, README, or agent-context changes, run what applies:

```bash
python3 scripts/deps.py check --pins-only
python3 scripts/deps.py docs --check
python3 scripts/check-cross-platform.py
python3 -m json.tool .mcp.json
python3 -m json.tool mcp/agents/research.json
python3 -m json.tool mcp/agents/storyboard.json
python3 -m json.tool .devcontainer/devcontainer.json
make status
make dry-run BRAND=example-brand
```

The `Cross-platform` GitHub workflow runs the same checks and the tests on Windows on every push.

## Known Caveats

- `README.md` uses collapsible sections as README-safe OS selection buttons. GitHub Markdown does not allow arbitrary JavaScript buttons.
- `.mcp.json` carries the shared servers (`figma`, `playwright`, `blender`, `higgsfield`). Use `mcp/agents/*.json` as the source for agent-scoped server registration.
- Blender MCP requires Blender and the MCP addon to be installed and running outside this repo.
- GIMP MCP requires GIMP 3.2 running with Tools > MCP > Start MCP Server (localhost:9877). Install or refresh the plugin with `python scripts/install-gimp-mcp.py`, and re-run it after a GIMP minor upgrade. Server and plugin use the one commit pinned in `dependencies.toml`; move it with `python scripts/deps.py set-pin gimp-mcp SHA`.
- API keys belong in environment variables or local `.env`, never in committed config.
- `.agents` and `.codex` directories may be read-only in some harnesses. Use repo-owned `AGENTS.md`, `skills/`, and `mcp/agents/` as portable context.

## Dirty Worktree Policy

This repo may contain user-local changes such as generated `workspace/*` outputs. Do not revert unrelated changes unless explicitly asked.
