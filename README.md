<div align="center">

![Automata — Multi-Agent AI Monorepo](docs/banner.png)

# 🤖 Automata

**A production-grade monorepo for building and running multi-agent AI systems.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Agency Swarm](https://img.shields.io/badge/Built%20on-Agency%20Swarm-7c3aed?style=flat-square)](https://github.com/VRSEN/agency-swarm)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-20%2B-brightgreen?style=flat-square&logo=node.js)](https://nodejs.org/)

*One prompt → complete deliverables. Research, slides, documents, images, videos — fully automated.*

</div>

---

## 🗺️ What is Automata?

**Automata** is a unified monorepo housing two tightly integrated AI systems that work together to automate end-to-end creative and research workflows:

| System | What it does |
|---|---|
| 🐝 **OpenedSwarm** | A full multi-agent swarm — an orchestrator + 7 specialist agents that collaborate to produce slides, research reports, documents, images, and videos from a single prompt |
| 🧠 **Automata Core** | A brand-focused autonomous agent for social media research, content strategy, and Instagram intelligence |

Think of it as your **AI agency in a box** — you describe what you need, and a coordinated team of AI specialists delivers it.

---

## 🏗️ Monorepo Structure

```
automata/
│
├── 🤖 agents/
│   ├── openedswarm_core/     ← Full multi-agent swarm (8 agents)
│   └── automata_core/        ← Brand research & social automation agent
│
├── 🧩 packages/              ← Shared Python packages (installable)
│   ├── agency-common/        ← Shared utilities across agents
│   ├── agency-research/      ← Research pipeline package
│   ├── agency-storyboard/    ← Storyboard generation package
│   ├── agency-content/       ← Content creation package
│   └── freepik-fastmcp/      ← Freepik MCP integration
│
├── 🎓 skills/                ← Reusable agent skill modules
│   ├── agency-content/
│   ├── agency-orchestrator/
│   ├── agency-research/
│   ├── agency-storyboard/
│   ├── superdesign/
│   ├── visual-image/
│   └── visual-video/
│
├── 🛠️ tools/
│   └── pdf_utils/            ← PDF processing utilities
│
├── ⚙️ core/
│   ├── runner.py             ← Unified CLI entrypoint for all agents
│   └── session_logger.py     ← Centralized session logging
│
├── 💾 memory/                ← Agent memory & vector indexes (local, gitignored)
├── 📁 data/                  ← Brand assets & outputs (local, gitignored)
└── requirements.txt          ← All Python dependencies
```

---

## 🐝 OpenedSwarm — Meet Your AI Team

OpenedSwarm runs **8 specialized agents** under a single orchestrator. Each agent is an expert — they hand off tasks to each other automatically based on what you ask for.

| Agent | 🎯 Role | What it delivers |
|---|---|---|
| 🎛️ **Orchestrator** | Traffic controller | Routes every request to the right specialist. Never answers directly. |
| 🤝 **Virtual Assistant** | General-purpose executor | Email, calendar, Slack, GitHub, HubSpot + 10,000+ integrations via Composio |
| 🔬 **Deep Research** | Evidence-based researcher | Web research, competitive analysis, source-cited reports |
| 📊 **Data Analyst** | Quantitative analyst | Charts, statistical models, data visualizations (runs in isolated IPython kernel) |
| 📑 **Slides Agent** | Presentation engineer | Polished HTML slide decks → exported `.pptx` |
| 📄 **Docs Agent** | Document engineer | Word docs, PDFs, Markdown — from outlines or raw content |
| 🎨 **Image Generation Agent** | Visual creator | AI image generation & editing via Gemini Flash Image & fal.ai |
| 🎬 **Video Generation Agent** | Video producer | AI video via Sora (OpenAI), Veo (Google), Seedance (fal.ai) |

### ✨ Example prompts

Paste any of these to see the swarm in action:

```
"Create a complete investor pitch deck for our AI SaaS product"
→ Deep Research gathers market data → Slides Agent builds the deck → Docs Agent writes the executive summary

"Research my top 5 competitors and write 3 SEO-optimized blog posts"
→ Deep Research runs competitive analysis → Docs Agent writes and formats content

"Analyze this CSV and create a quarterly performance report with charts"
→ Data Analyst crunches numbers → Slides Agent presents the findings

"Generate a 30-second product launch video with branded graphics"
→ Image Agent creates visuals → Video Agent assembles and renders the clip
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 20+** (for the npm-based launcher)
- At least one AI provider API key (see [API Keys](#️-api-keys) below)

---

### Option 1 — NPM Launcher *(Easiest)*

```bash
npm install -g @vrsen/openswarm
openswarm
```

The setup wizard handles everything: authentication, Python dependencies, and `.env` configuration.

---

### Option 2 — Run from Source

**1. Clone the repo**
```bash
git clone https://github.com/Gyanweshi/automata.git
cd automata
```

**2. Create and activate a virtual environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

**3. Install all dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure your API keys**
```bash
cp agents/openedswarm_core/.env.example agents/openedswarm_core/.env
# Edit .env and add your keys
```

**5. Run OpenedSwarm (interactive terminal)**
```bash
cd agents/openedswarm_core
python run.py
```

**5b. Or run Automata Core (brand research agent)**
```bash
python core/runner.py --agent automata --brand "YourBrandName" --action research
```

---

### Option 3 — Docker

```bash
cd agents/openedswarm_core
cp .env.example .env   # Add your API keys
docker-compose up --build
```

---

### Option 4 — API Server

```bash
cd agents/openedswarm_core
python server.py       # Runs on http://localhost:8080
```

---

## 🔑 API Keys

Configure these in `agents/openedswarm_core/.env` (copy from `.env.example`):

| Key | Required | What it unlocks |
|---|---|---|
| `OPENAI_API_KEY` | ✅ Pick one | GPT models + Sora video generation |
| `ANTHROPIC_API_KEY` | ✅ Pick one | Claude models |
| `GOOGLE_API_KEY` | ⚡ Optional | Gemini image generation + Veo video |
| `FAL_KEY` | ⚡ Optional | Advanced video editing via fal.ai |
| `SEARCH_API_KEY` | ⚡ Optional | Web search for the Deep Research agent |
| `COMPOSIO_API_KEY` | ⚡ Optional | 10,000+ external integrations (Gmail, Slack, HubSpot, etc.) |

> **💡 Tip:** Tools degrade gracefully when keys are missing — the agent will tell you exactly what to add if a feature isn't available.

---

## 🧩 Packages

The `packages/` directory contains installable Python packages shared across agents:

| Package | Purpose |
|---|---|
| `agency-common` | Shared base utilities, file I/O, logging |
| `agency-research` | Research pipeline: web scraping, source synthesis |
| `agency-storyboard` | Storyboard & scene composition generation |
| `agency-content` | Content formatting, copy generation |
| `freepik-fastmcp` | FastMCP integration for Freepik asset library |

These are installed in editable mode via `requirements.txt` automatically.

---

## 🎓 Skills

The `skills/` directory contains modular **skill packages** that can be loaded into agents on demand. Each skill is a self-contained capability:

- `agency-research/` — Research workflows
- `agency-storyboard/` — Visual storyboarding
- `agency-content/` — Content generation pipelines
- `superdesign/` — Design system generation
- `visual-image/` — Image creation workflows
- `visual-video/` — Video production workflows
- `agency-orchestrator/` — Orchestration logic

---

## 🔧 Customizing the Swarm

The swarm is designed to be forked and reshaped for any domain. To build your own:

**1. Tell your AI coding assistant:**
> *"Turn this into an SEO optimization swarm. The Research Agent becomes an SEO Keyword Planner, the Docs Agent becomes a Blog Post Writer..."*

**2. Or manually customize:**

```
agents/openedswarm_core/
  swarm.py                ← Edit this to add/remove/rewire agents
  shared_instructions.md  ← Context shared by ALL agents
  orchestrator/
    instructions.md       ← Orchestrator's system prompt
  deep_research/
    instructions.md       ← Change the researcher's behavior here
```

**Popular custom swarm ideas:**

- 🔍 **SEO Swarm** — Keyword research + competitor analysis + blog writing
- 💼 **Sales Swarm** — Lead research + outreach drafting + proposal generation
- 📢 **Marketing Swarm** — Campaign planning + creative assets + analytics
- 🛒 **E-Commerce Swarm** — Product description + image gen + listing optimization
- 📰 **Media Swarm** — Article research + writing + social media distribution

---

## ⚙️ Unified Runner

The `core/runner.py` is the single CLI entrypoint for all agents in this monorepo:

```bash
# Run OpenedSwarm
python core/runner.py --agent openedswarm

# Run Automata brand agent
python core/runner.py --agent automata --brand "Nike" --action research
```

All sessions are automatically logged via `core/session_logger.py` for audit trails and debugging.

---

## 📁 Data & Outputs

> ⚠️ **The `data/` and `workspace/` folders are gitignored** — they contain generated outputs and brand assets that are large and regenerable. They live only on your local machine.

| Folder | Contents |
|---|---|
| `data/outputs/` | All generated files (slides, docs, reports, videos) |
| `data/assets/brands/` | Brand asset libraries |
| `workspace/` | Temporary agent working directories |
| `memory/` | Local vector DB and agent memory state |

---

## 🤝 External Integrations (via Composio)

With a `COMPOSIO_API_KEY`, agents gain access to **10,000+ external tools**:

| Category | Integrations |
|---|---|
| 📧 Email | Gmail, Outlook |
| 📅 Calendar | Google Calendar, Calendly |
| 💬 Messaging | Slack, WhatsApp, Telegram, Discord |
| 📝 Docs | Google Docs, Notion, Airtable |
| 🗂️ Storage | Google Drive, Dropbox |
| 📋 PM | Jira, Asana, Trello, ClickUp, Monday |
| 📈 CRM | HubSpot, Salesforce, Pipedrive |
| 🛒 E-Commerce | Shopify |
| 🎨 Design | Figma, Canva, Miro |
| 💻 Dev | GitHub |

---

## 📺 Resources

- 🎥 [Watch the OpenedSwarm demo](https://youtu.be/c5DdXzqaeVU?si=rM2CNaZ8qVwMvqmz)
- 🦾 [Agency Swarm framework](https://github.com/VRSEN/agency-swarm)
- 🖥️ [AgentSwarm TUI](https://github.com/VRSEN/agentswarm-cli)
- 🔌 [Composio integrations](https://composio.dev)
- 📖 [AGENTS.md](agents/openedswarm_core/AGENTS.md) — Full guide for AI coding assistants customizing this repo

---

## 🧑‍💻 For Developers

**Key files to know:**

| File | Purpose |
|---|---|
| `agents/openedswarm_core/swarm.py` | Defines the swarm: all agents + their communication flows |
| `agents/openedswarm_core/shared_instructions.md` | System prompt shared by every agent |
| `agents/openedswarm_core/.env.example` | All configurable environment variables with descriptions |
| `agents/openedswarm_core/AGENTS.md` | Guide for AI assistants (Cursor, Claude Code, Codex) |
| `core/runner.py` | Unified CLI runner for the whole monorepo |
| `requirements.txt` | All Python dependencies |

**Adding a new agent:**
1. Create a folder under `agents/openedswarm_core/<agent_name>/`
2. Add `<agent_name>.py` + `instructions.md` + `tools/`
3. Import and register it in `swarm.py`
4. Update `shared_instructions.md` with the agent's role in the roster

---

## 📄 License

MIT — see [LICENSE](agents/openedswarm_core/LICENSE).

---

<div align="center">

**Built with ❤️ — Automata Monorepo**

*If this project helps you ship faster, give it a ⭐ on GitHub!*

</div>
