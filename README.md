# My Project

## MCP Setup

This project uses two local MCP servers: **Blender** and **Freepik**.

### Prerequisites

- [uv](https://astral.sh/uv/install.sh) — required for the Blender MCP
- A [Freepik API key](https://freepik.com/api)

### One-time setup

Run this once after cloning:

```bash
bash scripts/setup-mcp.sh
```

This installs Node 22 and the `mcp-remote-n22` wrapper needed for the Freepik MCP.

Then add your Freepik API key to your shell profile (`~/.bashrc` or `~/.zshrc`):

```bash
export FREEPIK_API_KEY=your_key_here
```

Reload your shell (`source ~/.bashrc`) and open the project in your IDE — the MCPs will start automatically.

### Team usage

Each team member uses their own Freepik API key. The key is read from your local environment and is never committed to the repo. The `setup-mcp.sh` script only installs infrastructure (Node 22 + mcp-remote) and does not require a key.

### MCP servers

| Server | Transport | Notes |
|--------|-----------|-------|
| blender | local (`uvx blender-mcp`) | Requires Blender running with the MCP addon enabled |
| freepik | remote (`https://api.freepik.com/mcp`) | Requires `FREEPIK_API_KEY` env var |
