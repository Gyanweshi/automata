<div align="center">

![Automata](docs/assets/banner.png)

# Automata

**A production-grade multi-agent AI system for brand research, visual storyboards, content generation, and autonomous task execution.**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Built on Agency Swarm](https://img.shields.io/badge/Built%20on-Agency%20Swarm-7c3aed?style=flat-square)](https://github.com/VRSEN/agency-swarm)
[![MCP Powered](https://img.shields.io/badge/MCP-Enabled-orange?style=flat-square)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

*One prompt → complete deliverables. Market research, pitch decks, copy, storyboards, and multi-platform automation.*

</div>

---

## 🗺️ What is Automata?

**Automata** unites two powerful agent paradigms in one clean monorepo:

1. **The Agency Pipeline**: A structured brand automation pipeline that takes a brand profile through competitive research, creative ideation, visual storyboarding, and platform-ready social content.
2. **OpenSwarm Specialists**: A swarm of 8 coordinated AI agents running under a single orchestrator. Agents autonomously delegate tasks to each other, execute code, generate documents, and access 10,000+ external tools.

---

## 🏗️ Repository Structure

```
automata/
│
├── 🤖 agents/
│   └── openedswarm_core/          ← 8-agent swarm built on Agency Swarm
│       ├── orchestrator/          ← Master router; delegates every incoming task
│       ├── deep_research/         ← Deep web research and source-cited reports
│       ├── data_analyst_agent/    ← Data science, statistics, and visualization
│       ├── docs_agent/            ← Polished documents (Word, PDF, Markdown)
│       ├── slides_agent/          ← Presentation slides exported to .pptx
│       ├── image_generation_agent/← AI image generation & editing
│       ├── video_generation_agent/← AI video generation & assembly
│       └── virtual_assistant/     ← 10,000+ external app actions via Composio
│
├── 🧩 packages/                   ← Installable core Python packages
│   ├── agency-common/             ← Shared models, workspace paths, and workflow discovery
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
│   ├── agency-housekeeper/        ← Workspace & vault retention hygiene
│   └── [higgsfield, design...]    ← Dedicated image, video, and design skills
│
├── ⚙️ core/                       ← Unified CLI runner and session logging
├── 🔌 mcp/                        ← Agent-scoped Model Context Protocol manifests
├── 🏷️ brands/                     ← Brand configuration templates and profiles
└── 📁 workspace/                  ← Disposable run data and scratch files (gitignored)
```

---

## 🤖 Meet the Agents

| Agent | 🎯 Role | What It Delivers |
|---|---|---|
| 🎛️ **Orchestrator** | Traffic Controller | Dispatches requests to the right specialist. Never answers directly. |
| 🔬 **Deep Research** | Evidence Researcher | Competitor audits, market analysis, and source-cited briefings. |
| 📊 **Data Analyst** | Data Scientist | Number crunching, chart generation, and dataset statistics. |
| 📑 **Slides Agent** | Presentation Designer | Slide architecture and polished decks exported to `.pptx`. |
| 📄 **Docs Agent** | Document Engineer | Comprehensive reports, Word documents, PDFs, and Markdown. |
| 🎨 **Image Agent** | Visual Creator | Image generation, mockups, restyling, and visual assets. |
| 🎬 **Video Agent** | Video Producer | Script breakdown, scene generation, and video montage assembly. |
| 🤝 **Virtual Assistant** | Tool Executor | Email, Slack, GitHub, calendar, and 10,000+ Composio integrations. |

### Example Multi-Agent Flows

- **Investor Pitch Deck**: Deep Research gathers market stats → Slides Agent designs the deck → Docs Agent writes the executive summary.
- **Competitor Strategy**: Deep Research audits top competitors → Agency Ideation crafts differentiated positioning → Agency Content drafts launch campaigns.
- **Quarterly Business Review**: Data Analyst crunches financial CSVs → Slides Agent generates visualizations → Virtual Assistant shares the draft in Slack.

---

## 🚀 Quick Start (fresh machine)

`git clone` only copies files; it never installs anything. On a machine with nothing installed (not even
Python), you install two things by hand, **Git** and **uv**, and one command does the rest: uv downloads
Python 3.12 if the machine has none, and the setup script installs Node.js and anything else missing, builds
the environment from the lockfiles, offers to register the nightly jobs, and then checks every part of the
setup one step at a time with a pass/fail summary. It is safe to re-run whenever something looks broken.

<details open>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
# 1. Git and uv (winget ships with Windows 10/11)
winget install -e --id Git.Git
winget install -e --id astral-sh.uv

# 2. Load the new PATH into this window (installers only update PATH for new windows)
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")

# 3. Clone, then run the one setup command
git clone https://github.com/Gyanweshi/automata.git
cd automata
uv run --no-project --python 3.12 scripts\bootstrap.py
```

The first `git clone` may open a browser to sign in to GitHub: approve it once. The setup asks before
installing anything (add `--yes` to skip the questions). Then copy `env.example` to `.env` and add your keys.

</details>

<details>
<summary><strong>Linux (Ubuntu, Mint, Debian) / macOS</strong></summary>

```bash
# 1. Git and uv
sudo apt install -y git curl                        # macOS: xcode-select --install
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env                             # or open a new terminal

# 2. Clone, then run the one setup command
git clone https://github.com/Gyanweshi/automata.git
cd automata
uv run --no-project --python 3.12 scripts/bootstrap.py
```

On a headless server add `--skip-browsers`. Then `cp env.example .env` and add your keys. The venv is created
by uv, so Debian/Ubuntu's separate `python3-venv` package is not needed.

</details>

**Already set up?** The same command repairs a machine after a `git pull`. To only check (changes nothing):
`python scripts/doctor.py` (or `make doctor`).

<details>
<summary><strong>Docker & Dev Containers</strong></summary>

#### Using VS Code Dev Containers
Open this folder in VS Code with the **Dev Containers** extension installed. It will automatically load [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) and set up Python, Node.js, and dependencies.

#### Using Docker Compose directly
```bash
cp agents/openedswarm_core/.env.example agents/openedswarm_core/.env
cd agents/openedswarm_core
docker-compose up --build
```

</details>

### After setup

- **Optional tools** (ffmpeg, GIMP, Blender, raea, ImageMagick, ...) show as `warn` in `deps.py check`, each with
  its install command; `python scripts/deps.py install ID` installs one. The full list, what each is for, and
  how to update or fix it is in [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md).
- **Nightly jobs:** `python scripts/schedule.py install vault-index` and `... install housekeeper` register them
  with this machine's scheduler (Task Scheduler on Windows, systemd/cron on Linux).
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
make research BRAND=example-brand SCRAPER=browser-act PLATFORMS=ig BROWSER_ACT_MODE=session BROWSER_ACT_SESSION_NAME=instagram-main
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

### Mode 2: Interactive Swarm Specialists

Run the unified CLI runner to converse with the multi-agent swarm:

```bash
# Launch interactive terminal swarm session
python core/runner.py --agent openedswarm

# Launch brand research agent directly
python core/runner.py --agent automata --brand "example-brand" --action research

# Run the OpenSwarm REST API server (localhost:8080)
python agents/openedswarm_core/server.py
```

---

## 🎓 Skills & Workflow Discovery

Automata includes modular agent skills under `skills/`. Every agent checks available skills and specialist instructions **before planning or executing any task**.

### Discovery & Sync Tools
- `make list-workflows`: Lists all registered skills, specialist agent instruction paths, and routing policies.
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
- **`frontend-design` & `superdesign`**: Token-driven slide design and UI architecture.
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
| `apify` | Research | `APIFY_API_TOKEN` | Actor-backed social media extraction (Instagram, LinkedIn) |
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
| `APIFY_API_TOKEN` | Social media scrapers | Recommended for social research |
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

<details>
<summary><strong>Fresh machine troubleshooting: "not recognized" / "command not found"</strong></summary>

- **Installed it, but the terminal still says "not recognized":** the window still has the old PATH. Run the
  PATH reload line from Quick Start step 3 (Windows), or open a new terminal.
- **winget says "Found an existing package" but the command is still not recognized:** it is installed but not
  on PATH. Find it, e.g. `Get-ChildItem "C:\Program Files\Git\cmd" -Filter git.exe`, and add that folder:
  `[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path","User") + ";C:\Program Files\Git\cmd", "User")`,
  then reload PATH. GitHub Desktop and VS Code ship their own git that PowerShell cannot see; install Git for
  Windows anyway.
- **`py` / `python` not recognized, or `python` opens the Microsoft Store:** you don't need a system Python;
  use `uv run --no-project --python 3.12 scripts\bootstrap.py`, which brings its own. After setup, the repo's
  Python is `.venv\Scripts\python.exe` (Linux `.venv/bin/python`).
- **uv missing:** install it (Quick Start step 1), reload PATH, then run the setup command again.
- **Node.js missing or too old:** re-run the setup command and answer yes, or `python scripts/deps.py install node`.
- **MCP servers say no compatible Node.js:** `node scripts/mcp-npx.mjs --which` shows which Node they will use;
  `none` means install Node 22+ (`python scripts/deps.py install node`).
</details>

<details>
<summary><strong>Playwright cannot launch browser</strong></summary>

Re-run the setup script; it installs the Chromium build for both the Node and the Python Playwright (each
version needs its own). On Linux, if system libraries are missing, Playwright prints the exact `apt-get`
command required.
</details>

<details>
<summary><strong>MCP server returns authentication error</strong></summary>

Check that your environment variable is loaded in your current shell:
```bash
echo "$APIFY_API_TOKEN"
```
Ensure keys are exported in `.env` or your shell configuration (`~/.bashrc`, `~/.zshrc`).
</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
