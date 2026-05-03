# Agency Agent Monorepo

This repo contains a small multi-agent system for brand research, storyboard planning, and social content generation. It is designed so a new machine can be prepared with one bootstrap script, then used through the Python CLIs, Makefile targets, PowerShell commands, skills, and MCP servers.

## What Is Inside

| Path | Purpose |
|------|---------|
| `packages/agency-common` | Shared brand loading, workspace paths, output writing, and models |
| `packages/agency-research` | Research agent CLI for competitor, trend, and sentiment analysis |
| `packages/agency-storyboard` | Storyboard agent CLI for scenes, visual direction, and generation prompts |
| `packages/agency-content` | Content agent CLI for captions, carousels, and weekly content |
| `packages/freepik-fastmcp` | Vendored Freepik MCP server used for image and resource workflows |
| `skills/` | Agent instructions for MCP-capable coding assistants |
| `mcp/agents/` | Agent-scoped MCP manifests |
| `.mcp.json` | Aggregate MCP config for clients that use one project-level MCP file |
| `brands/` | Brand configuration files |
| `workspace/` | Generated research, storyboard, and content outputs |

## Fresh Setup

These steps are for someone starting from a clean computer.

First install these on your computer:

- Git
- Python 3.11 or newer
- Node.js 18 or newer, which includes `npm` and `npx`
- `uv`

Then open only the section for your operating system.

<details open>
<summary><strong>Linux, macOS, or WSL</strong></summary>

### Linux/macOS/WSL Setup

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Clone the repo:

```bash
git clone <this-repo-url>
cd automata
```

Run bootstrap:

```bash
bash scripts/bootstrap.sh
```

If Playwright browser installation fails on a minimal server:

```bash
bash scripts/bootstrap.sh --skip-playwright-browser
```

Copy the API key template:

```bash
cp env.example .env
```

Add keys to `~/.bashrc`, `~/.zshrc`, or your shell profile:

```bash
export FREEPIK_API_KEY=your_freepik_key_here
export PERPLEXITY_API_KEY=your_perplexity_key_here
export FIRECRAWL_API_KEY=your_firecrawl_key_here
export GLIF_API_TOKEN=your_glif_token_here
```

Reload your shell:

```bash
source ~/.bashrc
```

Use `source ~/.zshrc` if you use Zsh.

Activate Python:

```bash
source .venv/bin/activate
```

You can skip activation when using `make` because the Makefile points to `.venv` directly.

</details>

<details>
<summary><strong>Windows PowerShell</strong></summary>

### Windows PowerShell Setup

Install `uv`:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen PowerShell.

Clone the repo:

```powershell
git clone <this-repo-url>
cd automata
```

Run bootstrap:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

If Playwright browser installation fails:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 -SkipPlaywrightBrowser
```

Copy the API key template:

```powershell
Copy-Item env.example .env
```

Set API keys:

```powershell
[Environment]::SetEnvironmentVariable("FREEPIK_API_KEY", "your_freepik_key_here", "User")
[Environment]::SetEnvironmentVariable("PERPLEXITY_API_KEY", "your_perplexity_key_here", "User")
[Environment]::SetEnvironmentVariable("FIRECRAWL_API_KEY", "your_firecrawl_key_here", "User")
[Environment]::SetEnvironmentVariable("GLIF_API_TOKEN", "your_glif_token_here", "User")
```

Close and reopen PowerShell.

Activate Python:

```powershell
.\.venv\Scripts\Activate.ps1
```

You can skip activation when using `scripts/run-agent.ps1` because it points to `.venv` directly.

</details>

<details>
<summary><strong>Windows Command Prompt</strong></summary>

### Windows Command Prompt Setup

PowerShell is still recommended for Windows because API key setup is clearer. If you use Command Prompt, run:

```cmd
scripts\bootstrap.cmd
```

Activate Python:

```cmd
.venv\Scripts\activate.bat
```

For daily agent commands on Windows, use PowerShell:

```powershell
.\scripts\run-agent.ps1 dry-run -Brand example-brand
```

</details>

The bootstrap script checks Python, Node, npm, npx, and `uv`; creates `.venv`; installs the agency packages; prepares the vendored Freepik MCP server; validates MCP configs; verifies pinned npm MCP packages; installs Playwright Chromium; and reports missing API keys.

## MCP Servers

The aggregate MCP config is [.mcp.json](.mcp.json). Agent-specific MCP manifests live under `mcp/agents/`.

| Server | Version | Agent | Needs Key | Purpose |
|--------|---------|-------|-----------|---------|
| `blender` | via `uvx blender-mcp` | Storyboard/3D | No | Blender scene creation and inspection |
| `freepik-fastmcp` | vendored | Storyboard/content | `FREEPIK_API_KEY` | Freepik search, downloads, Mystic image generation |
| `perplexity` | `@perplexity-ai/mcp-server@0.9.0` | Research | `PERPLEXITY_API_KEY` | Current web search, deep research, and citations |
| `playwright` | `@playwright/mcp@0.0.73` | Research | No | Browser automation and page extraction |
| `firecrawl` | `firecrawl-mcp@3.14.1` | Research | `FIRECRAWL_API_KEY` | Search, scrape, crawl, and structured extraction |
| `chrome-devtools` | `chrome-devtools-mcp@0.23.0` | Research | No | Console, network, screenshot, and performance inspection |
| `glif` | `@glifxyz/glif-mcp-server@0.9.9` | Storyboard | `GLIF_API_TOKEN` | Glif.app creative workflows and visual assets |

### Different MCP Harnesses

Most MCP clients can use `.mcp.json` directly or with small changes. If your harness expects a different format, use `.mcp.json` as the source of truth and copy the `command`, `args`, and `env` entries into that client.

For Codex on this machine, you can register a server manually with:

<details open>
<summary><strong>Linux, macOS, or WSL</strong></summary>

```bash
codex mcp add perplexity --env 'PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}' -- npx -y @perplexity-ai/mcp-server@0.9.0
```

</details>

<details>
<summary><strong>Windows PowerShell</strong></summary>

```powershell
codex mcp add perplexity --env "PERPLEXITY_API_KEY=$env:PERPLEXITY_API_KEY" -- npx -y @perplexity-ai/mcp-server@0.9.0
```

</details>

Repeat the same pattern for any server in `.mcp.json`.

## Using The Agents

Open the section for your operating system.

<details open>
<summary><strong>Linux, macOS, or WSL</strong></summary>

### Linux/macOS/WSL Agent Commands

Check install:

```bash
make status
```

Validate a brand without API calls:

```bash
make dry-run BRAND=example-brand
```

Run research:

```bash
make research BRAND=example-brand
```

Run storyboard:

```bash
make storyboard BRAND=example-brand TYPE=carousel TOPIC="5 tips for entrepreneurs"
```

Run content:

```bash
make content BRAND=example-brand TYPE=carousel TOPIC="5 tips for entrepreneurs"
```

Run the full pipeline:

```bash
make pipeline BRAND=example-brand TYPE=carousel TOPIC="5 tips for entrepreneurs"
```

</details>

<details>
<summary><strong>Windows PowerShell</strong></summary>

### Windows PowerShell Agent Commands

Check install:

```powershell
.\scripts\run-agent.ps1 status
```

Validate a brand without API calls:

```powershell
.\scripts\run-agent.ps1 dry-run -Brand example-brand
```

Run research:

```powershell
.\scripts\run-agent.ps1 research -Brand example-brand
```

Run storyboard:

```powershell
.\scripts\run-agent.ps1 storyboard -Brand example-brand -Type carousel -Topic "5 tips for entrepreneurs"
```

Run content:

```powershell
.\scripts\run-agent.ps1 content -Brand example-brand -Type carousel -Topic "5 tips for entrepreneurs"
```

Run the full pipeline:

```powershell
.\scripts\run-agent.ps1 pipeline -Brand example-brand -Type carousel -Topic "5 tips for entrepreneurs"
```

</details>

Outputs are written to:

```text
workspace/research/<brand-slug>/
workspace/storyboards/<brand-slug>/
workspace/content/<brand-slug>/
```

## Adding A New Brand

<details open>
<summary><strong>Linux, macOS, or WSL</strong></summary>

Copy the template:

```bash
cp brands/_template.yaml brands/my-brand.yaml
```

Edit `brands/my-brand.yaml`, then run:

```bash
make dry-run BRAND=my-brand
```

</details>

<details>
<summary><strong>Windows PowerShell</strong></summary>

Copy the template:

```powershell
Copy-Item brands/_template.yaml brands/my-brand.yaml
```

Edit `brands/my-brand.yaml`, then run:

```powershell
.\scripts\run-agent.ps1 dry-run -Brand my-brand
```

</details>

## Dev Containers

This repo includes [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) for VS Code Dev Containers or compatible tools. It installs Python and Node, installs `uv`, and runs:

```bash
bash scripts/bootstrap.sh --skip-playwright-browser
```

You still need to provide your own API keys inside the container.

## Common Problems

### `uv: command not found`

Install `uv`, then reopen your terminal:

<details open>
<summary><strong>Linux, macOS, or WSL</strong></summary>

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

</details>

<details>
<summary><strong>Windows PowerShell</strong></summary>

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

</details>

### `npx: command not found`

Install Node.js 18 or newer from `https://nodejs.org/`, then reopen your terminal.

### MCP Server Starts But Tool Fails With Auth Error

The API key is missing or not loaded into the environment. Check with:

<details open>
<summary><strong>Linux, macOS, or WSL</strong></summary>

```bash
echo "$PERPLEXITY_API_KEY"
echo "$FIRECRAWL_API_KEY"
echo "$GLIF_API_TOKEN"
echo "$FREEPIK_API_KEY"
```

</details>

<details>
<summary><strong>Windows PowerShell</strong></summary>

```powershell
echo $env:PERPLEXITY_API_KEY
echo $env:FIRECRAWL_API_KEY
echo $env:GLIF_API_TOKEN
echo $env:FREEPIK_API_KEY
```

</details>

### Playwright Cannot Open A Browser

Install Chromium:

<details open>
<summary><strong>Linux, macOS, WSL, or Windows PowerShell</strong></summary>

```bash
npx -y playwright@1.56.1 install chromium
```

</details>

On Linux servers, you may also need OS browser dependencies. Playwright will print the exact command for your distribution.

### Blender MCP Does Not Work

Blender MCP needs Blender running with the MCP addon enabled. The repo config only defines how the MCP server starts; it does not install Blender itself.

### A Different Harness Does Not Read `.mcp.json`

Use `.mcp.json` as a copy source. The important pieces are the server name, `command`, `args`, and `env`. Keep real API keys out of committed files.

## Maintenance

Pinned npm MCP versions are intentional. To update them later:

```bash
npm view @perplexity-ai/mcp-server version
npm view @playwright/mcp version
npm view firecrawl-mcp version
npm view chrome-devtools-mcp version
npm view @glifxyz/glif-mcp-server version
```

Then update `.mcp.json`, `mcp/agents/*.json`, and this README together.
