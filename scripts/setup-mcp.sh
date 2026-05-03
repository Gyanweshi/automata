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

if ! command -v npx &>/dev/null; then
  echo "npx is required for the Perplexity, Playwright, Firecrawl, Chrome DevTools, and Glif MCP servers."
  echo "Install Node.js 18+ and npm, then rerun this script."
  exit 1
fi

echo "==> Preparing Freepik FastMCP dependencies..."
uv sync --directory packages/freepik-fastmcp

echo "==> Checking pinned npm MCP packages..."
npm view @perplexity-ai/mcp-server@0.9.0 version >/dev/null
npm view @playwright/mcp@0.0.73 version >/dev/null
npm view firecrawl-mcp@3.14.1 version >/dev/null
npm view chrome-devtools-mcp@0.23.0 version >/dev/null
npm view @glifxyz/glif-mcp-server@0.9.9 version >/dev/null

echo "==> Done. Make sure ~/.local/bin is in your PATH, then set any API keys you use:"
echo "    export FREEPIK_API_KEY=your_key_here"
echo "    export PERPLEXITY_API_KEY=your_key_here"
echo "    export FIRECRAWL_API_KEY=your_key_here"
echo "    export GLIF_API_TOKEN=your_token_here"
