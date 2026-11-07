<div align="center">

![Automata](docs/assets/banner.png)

# Automata

**A production-grade multi-agent AI system for brand research, visual storyboards, content generation, and autonomous task execution.**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![MCP Powered](https://img.shields.io/badge/MCP-Enabled-orange?style=flat-square)](https://modelcontextprotocol.io/)

*One prompt → complete deliverables. Market research, pitch decks, copy, storyboards, and multi-platform automation.*

</div>

---

## 🗺️ What is Automata?

**Automata** is a brand automation system: a structured pipeline that takes a brand profile through competitive
research, creative ideation, visual storyboarding (including local 3D previz), and platform-ready social content,
driven by coding agents (Claude Code, Codex) through repo skills and MCP servers, with the Obsidian vault as memory.

---

## 🏗️ Repository Structure

```
automata/
│
├── 🧩 packages/                   ← Installable core Python packages
│   ├── agency-common/             ← Shared models, workspace paths, vault search, scheduled jobs
│   ├── agency-research/           ← Research pipeline (scrapers, competitor analysis)
│   ├── agency-storyboard/         ← Storyboard & visual scene composition
│   └── agency-content/            ← Copywriting, carousels, and calendars
│
├── 🎓 skills/                     ← Modular agent skill packages
│   ├── agency-orchestrator/       ← Master skill & agent routing
│   ├── agency-research/           ← Deep competitor & audience research
│   ├── agency-ideation/           ← Sourced creative frameworks (IDEO, Strategyzer, Blue Ocean)
│   ├── agency-storyboard/         ← Scene planning & visual prompts
│   ├── agency-content/            ← Brand-aligned social copy & calendars
│   ├── previz-3d/                 ← Greybox 3D previz with raea before AI video
│   ├── agency-housekeeper/        ← Workspace & vault retention hygiene
│   └── [image, video, design...]  ← Image editing, generation, upscaling, slides
│
├── 🤖 agents/automata_core/       ← Autonomous agent loop
├── ⚙️ core/                       ← Unified CLI runner and session logging
├── 🔌 mcp/                        ← Agent-scoped Model Context Protocol manifests
├── 🛠️ scripts/                    ← One cross-platform toolchain: bootstrap, doctor, deps, schedule, run-agent
├── 🏷️ brands/                     ← Brand configuration template
├── 📚 docs/                       ← Dependency register (docs/DEPENDENCIES.md)
└── 📁 workspace/                  ← Disposable run data and scratch files (gitignored)
```

---

## 🤖 Meet the Agents

| Agent / skill | 🎯 Role | What It Delivers |
|---|---|---|
| 🎛️ **Orchestrator** | Router | Onboards brands and routes research, storyboard, content, calendar and full-pipeline requests. |
| 🔬 **Research** | Evidence Researcher | Competitor audits, social trends, audience sentiment, engagement benchmarks. |
| 💡 **Ideation** | Strategist | Problem framing, propositions and campaign concepts from sourced frameworks. |
| 🎬 **Storyboard** | Visual Director | Scene plans, visual direction, image/video prompts, and 3D previz. |
| ✍️ **Content** | Copywriter | Brand-voice captions, carousels, posts, articles and weekly calendars. |
| 🧹 **Housekeeper** | Librarian | Keeps the repo lean and the vault the single home for durable work. |

### Example Flows

- **Brand launch**: Research audits competitors → Ideation picks a positioning → Storyboard plans the reel (with 3D previz) → Content writes the captions.
- **Weekly calendar**: Research refreshes trends → Content drafts a week of platform-ready posts in the brand voice.

---

## 🚀 Quick Start

> **Full guide:** [docs/SETUP.md](docs/SETUP.md) covers the steps, how to check a machine, and a troubleshooting
> table for every problem seen so far on fresh Windows and Linux machines. Send new people there.

### New machine: one paste

Works on a machine with nothing installed, not even Python. Open a terminal, paste the block for your OS,
approve the GitHub login that opens in your browser, and wait (about 5–10 minutes, mostly downloads). Running it
again later is safe: it skips whatever is already there.

**Windows** (PowerShell; winget ships with Windows 10 and 11):
```powershell
foreach ($id in "Git.Git", "GitHub.cli", "astral-sh.uv") { winget install -e --id $id --accept-source-agreements --accept-package-agreements }
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User") + ";$env:LOCALAPPDATA\Microsoft\WinGet\Links"
gh auth status 2>$null; if ($LASTEXITCODE) { gh auth login --web --git-protocol https }; gh auth setup-git
if (-not (Test-Path automata)) { gh repo clone Gyanweshi/automata }; Set-Location automata
uv run --no-project --python 3.12 scripts\bootstrap.py --yes
```

**Linux** (Ubuntu, Mint, Debian):
```bash
sudo apt-get update && sudo apt-get install -y git curl gh
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"
gh auth status >/dev/null 2>&1 || gh auth login --web --git-protocol https; gh auth setup-git
[ -d automata ] || gh repo clone Gyanweshi/automata; cd automata
uv run --no-project --python 3.12 scripts/bootstrap.py --yes
```

**macOS** (Terminal app; Apple silicon or Intel):
```bash
command -v brew >/dev/null || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"; grep -qs 'brew shellenv' ~/.zprofile || echo 'eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"' >> ~/.zprofile
brew install git gh uv
gh auth status >/dev/null 2>&1 || gh auth login --web --git-protocol https; gh auth setup-git
[ -d automata ] || gh repo clone Gyanweshi/automata; cd automata
uv run --no-project --python 3.12 scripts/bootstrap.py --yes
```
The first line installs Homebrew, the Mac's package manager, if it is missing: it asks for the Mac's login
password once (nothing shows while you type) and may install Apple's Command Line Tools. The second line puts
Homebrew on PATH now and for every new terminal.

What happens: Git, the GitHub CLI and uv are installed; you log in to GitHub once in the browser; the repo is
cloned; then the setup script downloads Python 3.12 if the machine has none, installs Node.js and the rest,
builds the environment from the lockfiles and installs the browsers. It asks three things once:
- **Your Obsidian vault folder**, or Enter for none: without a vault, notes, drafts and session logs stay in
  `workspace/vault` with the same layout, and everything works the same.
- **What this machine is for** (`research`, `video`, `slides`, `images`, `3d`, or `all`): it installs only those
  optional tools, and the checks only expect those. Change later with `--roles`.
- **Whether to register the nightly jobs.**

It finishes by checking every part of the setup with a `PASS` / `WARN` / `FAIL` summary.

Last step: copy `env.example` to `.env` and add your API keys.

### Machine already set up

```bash
git pull
```

That is all: the setup script installs git hooks, so a pull that changes dependencies, MCP config or the setup
itself re-runs the setup automatically (it also removes leftovers of removed components and re-registers scheduled
jobs that belong to this copy, never ones registered for another copy). A clone made before those hooks existed
gets them the first time the setup runs: Claude Code flags it at the start of a session, and `run-agent.py` warns.

```bash
python scripts/setup_state.py --check   # is this machine in step with the checkout?
python scripts/bootstrap.py             # repair / update by hand (Windows: python scripts\bootstrap.py)
python scripts/doctor.py                # only check, changes nothing (or: make doctor)
```

<details>
<summary><strong>Docker & Dev Containers</strong></summary>

#### Using VS Code Dev Containers
Open this folder in VS Code with the **Dev Containers** extension installed. It will automatically load [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) and set up Python, Node.js, and dependencies.

</details>

### After setup

- **Optional tools** are installed per machine role (`python scripts/bootstrap.py --roles ...`); a missing one
  shows as `warn` in `deps.py check` with its install command, and `python scripts/deps.py install ID` installs one. The full list, what each is for, and
  how to update or fix it is in [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md).
- **Scheduled jobs:** `python scripts/schedule.py install vault-index`, `... install housekeeper` and `... install vault-watchdog`
  register them with this machine's scheduler (Task Scheduler on Windows, systemd/cron on Linux).
- **After `git pull`** on either machine, re-run the setup script if dependencies changed; it is quick when
  nothing is missing.

---

## ⚡ Running Automata

Automata supports two primary execution modes:

### Mode 1: The Agency Brand Pipeline

Run individual stages or execute the full end-to-end agency pipeline:

<details open>
<summary><strong>Linux / macOS / WSL</strong></summary>

```bash
# 1. Competitive & audience research
make research BRAND=example-brand

# 2. Visual storyboard creation
make storyboard BRAND=example-brand TYPE=carousel TOPIC="5 tips for entrepreneurs"

# 3. Copywriting & captions
make content BRAND=example-brand TYPE=carousel TOPIC="5 tips for entrepreneurs"

# 4. Full end-to-end pipeline (Research -> Storyboard -> Content)
make pipeline BRAND=example-brand TYPE=carousel TOPIC="5 tips for entrepreneurs"
```

**Advanced Research Options:**
```bash
# Bounded parallel workers
make research BRAND=example-brand PARALLEL=1 MAX_WORKERS=4

# Stealth Instagram scraper via browser-act
make research BRAND=example-brand SCRAPER=browser-act PLATFORMS=ig PARALLEL=1 MAX_WORKERS=4

# Authenticated persistent browser session
make research BRAND=example-brand SCRAPER=browser-act PLATFORMS=ig BROWSER_ACT_MODE=session BROWSER_ACT_BROWSER=instagram-research
```

</details>

<details>
<summary><strong>Windows PowerShell</strong></summary>

```powershell
# 1. Competitive & audience research
py scripts\run-agent.py research --brand example-brand

# 2. Visual storyboard creation
py scripts\run-agent.py storyboard --brand example-brand --type carousel --topic "5 tips for entrepreneurs"

# 3. Copywriting & captions
py scripts\run-agent.py content --brand example-brand --type carousel --topic "5 tips for entrepreneurs"

# 4. Full end-to-end pipeline
py scripts\run-agent.py pipeline --brand example-brand --type carousel --topic "5 tips for entrepreneurs"
```

**Persistent Instagram Login Helper (Windows):**
```powershell
# Open persistent CDP Chrome profile for one-time login:
py scripts\open-instagram-session.py --cdp-port 9224 --wait

# Run CDP-backed research:
py scripts\run-agent.py research --brand example-brand --scraper cdp --platforms ig
```

</details>

---

### Mode 2: Autonomous brand agent

Run the autonomous agent loop for one brand and action (it logs the session to the vault):

```bash
python core/runner.py --brand "example-brand" --action research
```

---

## 🎓 Skills & Workflow Discovery

Automata includes modular agent skills under `skills/`. Every agent checks available skills **before planning or executing any task**.

### Discovery & Sync Tools
- `make list-workflows`: Lists all registered skills and the routing policy.
- `make check-skills`: Verifies that skill shims are synchronized across Codex (`.agents/skills/`) and Claude Code (`.claude/skills/`).
- `make install-skills`: Generates or updates missing discovery shims for your local coding assistants.

### Available Skill Catalog
- **`agency-orchestrator`**: Master routing and brand execution coordinator.
- **`agency-research`**: Competitor analysis, audience sentiment, and platform trends.
- **`agency-ideation`**: Problem framing and campaign ideation using frameworks from IDEO, Strategyzer, and Blue Ocean Strategy.
- **`agency-storyboard`**: Visual scenes, shot lists, and image generation prompts.
- **`agency-content`**: Brand voice copywriting, captions, carousels, and calendars.
- **`agency-housekeeper`**: Retention policies and workspace/vault cleanup decisions.
- **`higgsfield-*` suite**: Image generation, product photoshoots, brand kits, and video explainers.
- **`frontend-design`**: Token-driven slide decks with an inline editor for spacing and type.
- **`html-preview`**: Headless Playwright screenshot verification of local HTML files.
- **`visual-image` & `visual-video`**: Curated prompt libraries for AI image/video models.
- **`image-gen`**: OpenAI GPT Image generation/edits and local animated-GIF assembly via portable Python CLIs.
- **`image-compositing-repair`**: Local, non-generative image editing (GIMP MCP or Python/OpenCV/Pillow) that preserves untouched pixels.
- **`previz-3d`**: Greybox 3D previz (camera moves, subject motion, keyframes) rendered locally with [raea](https://github.com/shinyobjectz/raea) before AI video generation. Install with `python scripts/deps.py install raea`.

---

## 🔌 Model Context Protocol (MCP)

Automata connects agents directly to external browsers, design tools, and AI generation backends via MCP:

| Server | Agent Scope | Required Auth | Purpose |
|---|---|---|---|
| `playwright` | Research | None | Headless browser automation and page scraping |
| `chrome-devtools` | Research | None | Console inspection, network monitoring, screenshots |
| `notebooklm` | Research | Google Login | Grounded Q&A against source documents |
| `figma` | Design | Figma Desktop | Canvas context inspection and vector delivery |
| `higgsfield` | Storyboard / Content | Higgsfield OAuth | Up to 4K image and video generation |
| `magnific` | Storyboard / Content | Magnific OAuth | AI upscaling, restyling, and generation history |
| `blender` | Storyboard / 3D | Blender + Addon | Programmatic 3D scene creation and rendering |
| `gimp` | Storyboard / Image editing | GIMP 3.2 + plugin (`python scripts/install-gimp-mcp.py`) | Local image editing: retouch, masks, layers, color, text, XCF export |

*Project-wide MCP configuration is managed in [.mcp.json](.mcp.json); agent-specific configurations live in `mcp/agents/`.*

---

## 🔑 API Keys Reference

| Key | Purpose | Required? |
|---|---|---|
| `OPENAI_API_KEY` | GPT models + Sora video | ✅ Yes (or Anthropic) |
| `ANTHROPIC_API_KEY` | Claude 3.5 / 3.7 models | ✅ Yes (or OpenAI) |
| `GOOGLE_API_KEY` | Gemini and Veo models | Optional |
| `COMPOSIO_API_KEY` | 10,000+ app integrations (Slack, Gmail, HubSpot) | Optional (for Virtual Assistant) |
| `PEXELS_API_KEY` / `UNSPLASH_ACCESS_KEY` | Stock photography in presentations | Optional (for Slides Agent) |

> 💡 **Graceful Degradation**: Agents report missing API keys when an optional tool is called rather than failing to start.

---

## 📁 Storage & Obsidian Vault Integration

Automata keeps code and disposable runs clean by separating working files:

1. **Obsidian Vault (`$OBSIDIAN_VAULT_PATH`)**:
   - The permanent home for human-readable notes, research briefings, scripts, and content calendars.
   - Drafts are stored under `Brands/<slug>/Drafts/<type>/` (`status: draft`).
   - Approved final assets live under `Brands/<slug>/<type>/` (`status: final`).
   - Memory is recorded in `Brands/<slug>.md` (distilled to at most 10 key bullets).
2. **Local Workspace (`workspace/`)**:
   - Temporary intermediate JSON files, browser screenshots, and generated image variants remain strictly local and are **gitignored**.

---

## 🛠️ Adding a New Brand

To onboard a brand:

```bash
# 1. Copy the brand template
cp brands/_template.yaml brands/my-brand.yaml

# 2. Fill in voice, audience, competitors, and tone in brands/my-brand.yaml

# 3. Validate configuration without incurring API costs
make dry-run BRAND=my-brand
```

---

## ❓ Troubleshooting & FAQ

**Setup problems** ("not recognized", `FAIL` / `warn` in the checks, winget codes, PATH): see the
troubleshooting table in [docs/SETUP.md](docs/SETUP.md#4-troubleshooting).

<details>
<summary><strong>Playwright cannot launch browser</strong></summary>

Re-run the setup script; it installs the Chromium build for both the Node and the Python Playwright (each
version needs its own). On Linux, if system libraries are missing, Playwright prints the exact `apt-get`
command required.
</details>

<details>
<summary><strong>MCP server returns authentication error</strong></summary>

Servers that need a key read it from `.env` in the repo root (see `env.example`); ones that need a login
(NotebookLM, Higgsfield, Magnific) are authenticated from the client (`/mcp` in Claude Code).
`python scripts/mcp-smoke.py <server>` starts one exactly as configured and lists its tools.
</details>

---

## 📄 License

Private repository. All rights reserved; not licensed for redistribution.
