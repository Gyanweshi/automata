#!/bin/bash
# Sets up MCP dependencies for this project on a fresh system.
# Run once after cloning: bash scripts/setup-mcp.sh

set -e

if ! command -v uv &>/dev/null; then
  echo "uv is required for the Blender and Freepik MCP servers."
  echo "Install it with:"
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

if ! command -v npm &>/dev/null; then
  echo "npm is required to check pinned MCP packages."
  echo "Install Node.js 20.19+, 22.12+, or 23+ and npm, then rerun this script."
  exit 1
fi

MCP_NODE_VERSION="$(scripts/mcp-npx.sh -c "node --version" 2>/dev/null || true)"
if [[ -z "$MCP_NODE_VERSION" ]]; then
  echo "Node.js 20.19+, 22.12+, or 23+ is required for chrome-devtools-mcp. Found default node: $(node --version)"
  echo "Install or activate a compatible Node.js version, then rerun this script."
  exit 1
fi

echo "==> Preparing vendored MCP dependencies..."
uv sync --directory packages/freepik-fastmcp

if [[ -x .venv/bin/scrapling ]]; then
  echo "==> Checking Scrapling MCP command..."
  .venv/bin/scrapling --version >/dev/null
elif command -v scrapling &>/dev/null; then
  echo "==> Checking Scrapling MCP command..."
  scrapling --version >/dev/null
else
  echo "WARN Scrapling is not installed yet. Run scripts/bootstrap.sh or install the agency-research package first."
fi

echo "==> Checking pinned npm MCP packages..."
npm view @perplexity-ai/mcp-server@0.9.0 version >/dev/null
npm view @playwright/mcp@0.0.73 version >/dev/null
npm view firecrawl-mcp@3.14.1 version >/dev/null
npm view chrome-devtools-mcp@0.23.0 version >/dev/null
npm view @roomi-fields/notebooklm-mcp@1.5.9 version >/dev/null
npm view mcp-remote@0.1.38 version >/dev/null
npm view @apify/actors-mcp-server@0.9.20 version >/dev/null

echo "==> Done. Make sure ~/.local/bin is in your PATH, then set any API keys you use:"
echo "    export FREEPIK_API_KEY=your_key_here"
echo "    export PERPLEXITY_API_KEY=your_key_here"
echo "    export FIRECRAWL_API_KEY=your_key_here"
echo "    export CAPSULEHUB_API_KEY=your_key_here"
echo "    export APIFY_API_TOKEN=your_token_here"
