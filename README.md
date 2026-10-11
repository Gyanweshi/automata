<div align="center">

![Automata](docs/assets/banner.png)

# Automata

**A production-grade multi-agent AI system for brand research, visual storyboards, content generation, and autonomous task execution.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
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

## 🚀 Quick Start

### Prerequisites
Before starting, ensure your system has:
- **Python 3.11+**
- **Node.js 20.19+, 22.12+, or 23+** (includes `npm` and `npx`)
- **Git**
- **uv** (fast Python package manager)

---

### Step-by-Step Setup

Open the tab for your operating system:

<details open>
<summary><strong>Linux, macOS, or WSL (Recommended)</strong></summary>

#### 1. Install `uv` (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. Clone the repository
```bash
git clone https://github.com/Gyanweshi/automata.git
cd automata
```

#### 3. Run the bootstrap script
```bash
bash scripts/bootstrap.sh
```
*(If you are on a headless server without GUI libraries, run `bash scripts/bootstrap.sh --skip-playwright-browser`)*

#### 4. Configure API Keys
Copy the environment template and edit `.env`:
```bash
cp env.example .env
```
Export your core keys in your shell profile (`~/.bashrc` or `~/.zshrc`):
```bash
export FIRECRAWL_API_KEY="your_firecrawl_key"
export APIFY_API_TOKEN="your_apify_token"
export OPENAI_API_KEY="your_openai_key"       # or ANTHROPIC_API_KEY
source ~/.bashrc
```

#### 5. Verify the installation
```bash
make status
make dry-run BRAND=example-brand
```

</details>

<details>
<summary><strong>Windows PowerShell</strong></summary>

#### 1. Install `uv`
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
*(Close and reopen PowerShell after installing uv)*

#### 2. Clone the repository
```powershell
git clone https://github.com/Gyanweshi/automata.git
cd automata
```

#### 3. Run the bootstrap script
```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```
*(To skip Playwright browser download: `-SkipPlaywrightBrowser`)*

#### 4. Configure API Keys
```powershell
Copy-Item env.example .env
[Environment]::SetEnvironmentVariable("FIRECRAWL_API_KEY", "your_firecrawl_key", "User")
[Environment]::SetEnvironmentVariable("APIFY_API_TOKEN", "your_apify_token", "User")
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your_openai_key", "User")
```
*(Close and reopen PowerShell to load the new environment variables)*

#### 5. Verify the installation
```powershell
.\scripts\run-agent.ps1 status
.\scripts\run-agent.ps1 dry-run -Brand example-brand
```

</details>

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
.\scripts\run-agent.ps1 research -Brand example-brand

# 2. Visual storyboard creation
.\scripts\run-agent.ps1 storyboard -Brand example-brand -Type carousel -Topic "5 tips for entrepreneurs"

# 3. Copywriting & captions
.\scripts\run-agent.ps1 content -Brand example-brand -Type carousel -Topic "5 tips for entrepreneurs"

# 4. Full end-to-end pipeline
.\scripts\run-agent.ps1 pipeline -Brand example-brand -Type carousel -Topic "5 tips for entrepreneurs"
```

**Persistent Instagram Login Helper (Windows):**
```powershell
# Open persistent CDP Chrome profile for one-time login:
.\scripts\open-instagram-session.ps1 -Mode cdp -CdpPort 9224 -WaitForEnter

# Run CDP-backed research:
.\scripts\run-agent.ps1 research -Brand example-brand -Scraper cdp -Platforms ig
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

---

## 🔌 Model Context Protocol (MCP)

Automata connects agents directly to external browsers, design tools, and AI generation backends via MCP:

| Server | Agent Scope | Required Auth | Purpose |
|---|---|---|---|
| `playwright` | Research | None | Headless browser automation and page scraping |
| `firecrawl` | Research | `FIRECRAWL_API_KEY` | Deep web crawling, search, and Markdown extraction |
| `chrome-devtools` | Research | None | Console inspection, network monitoring, screenshots |
| `notebooklm` | Research | Google Login | Grounded Q&A against source documents |
| `apify` | Research | `APIFY_API_TOKEN` | Actor-backed social media extraction (Instagram, LinkedIn) |
| `figma` | Design | Figma Desktop | Canvas context inspection and vector delivery |
| `higgsfield` | Storyboard / Content | Higgsfield OAuth | Up to 4K image and video generation |
| `magnific` | Storyboard / Content | Magnific OAuth | AI upscaling, restyling, and generation history |
| `blender` | Storyboard / 3D | Blender + Addon | Programmatic 3D scene creation and rendering |

*Project-wide MCP configuration is managed in [.mcp.json](.mcp.json); agent-specific configurations live in `mcp/agents/`.*

---

## 🔑 API Keys Reference

| Key | Purpose | Required? |
|---|---|---|
| `OPENAI_API_KEY` | GPT models + Sora video | ✅ Yes (or Anthropic) |
| `ANTHROPIC_API_KEY` | Claude 3.5 / 3.7 models | ✅ Yes (or OpenAI) |
| `FIRECRAWL_API_KEY` | Web crawling and scraping | Recommended for research |
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
<summary><strong><code>uv: command not found</code></strong></summary>

Install `uv` via Astral's installer:
- **Linux/macOS**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows**: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`  
Reopen your terminal after installation.
</details>

<details>
<summary><strong><code>npx: command not found</code></strong></summary>

Install Node.js 20.19+, 22.12+, or 23+ from [nodejs.org](https://nodejs.org/). `npm` and `npx` are bundled with Node.js.
</details>

<details>
<summary><strong>Playwright cannot launch browser</strong></summary>

Install the Chromium binary:
```bash
npx -y playwright@1.56.1 install chromium
```
On Linux, if system libraries are missing, Playwright will print the exact `apt-get` or distribution command required.
</details>

<details>
<summary><strong>MCP server returns authentication error</strong></summary>

Check that your environment variable is loaded in your current shell:
```bash
echo "$FIRECRAWL_API_KEY"
echo "$APIFY_API_TOKEN"
```
Ensure keys are exported in `.env` or your shell configuration (`~/.bashrc`, `~/.zshrc`).
</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
