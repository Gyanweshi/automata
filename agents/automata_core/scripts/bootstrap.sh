#!/usr/bin/env bash
# Fresh-machine bootstrap for the agency agent monorepo.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SKIP_PLAYWRIGHT_BROWSER=0
SKIP_SCRAPLING_BROWSER=0
for arg in "$@"; do
  case "$arg" in
    --skip-playwright-browser)
      SKIP_PLAYWRIGHT_BROWSER=1
      ;;
    --skip-scrapling-browser)
      SKIP_SCRAPLING_BROWSER=1
      ;;
    -h|--help)
      echo "Usage: bash scripts/bootstrap.sh [--skip-playwright-browser] [--skip-scrapling-browser]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: bash scripts/bootstrap.sh [--skip-playwright-browser] [--skip-scrapling-browser]"
      exit 1
      ;;
  esac
done

ok() {
  echo "OK  $1"
}

warn() {
  echo "WARN $1"
}

fail() {
  echo "FAIL $1"
  exit 1
}

require_cmd() {
  local cmd="$1"
  local hint="$2"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    fail "$cmd is missing. $hint"
  fi
  ok "$cmd found: $(command -v "$cmd")"
}

echo "==> Checking required tools"
require_cmd python3 "Install Python 3.11+."
require_cmd uv "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
require_cmd node "Install Node.js 20.19+, 22.12+, or 23+ from https://nodejs.org/."
require_cmd npm "Install npm with Node.js."

PYTHON_OK="$(python3 - <<'PY'
import sys
print("yes" if sys.version_info >= (3, 11) else "no")
PY
)"
if [[ "$PYTHON_OK" != "yes" ]]; then
  fail "Python 3.11+ is required. Found: $(python3 --version)"
fi
ok "$(python3 --version)"

MCP_NODE_VERSION="$(scripts/mcp-npx.sh -c "node --version" 2>/dev/null || true)"
if [[ -z "$MCP_NODE_VERSION" ]]; then
  fail "Node.js 20.19+, 22.12+, or 23+ is required for chrome-devtools-mcp. Found default node: $(node --version)"
fi
ok "MCP Node $MCP_NODE_VERSION"

echo ""
echo "==> Creating Python virtual environment"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  ok "created .venv"
else
  ok ".venv already exists"
fi

echo ""
echo "==> Installing agency packages into .venv"
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e ./packages/agency-common
.venv/bin/pip install -e ./packages/agency-research
.venv/bin/pip install -e ./packages/agency-storyboard
.venv/bin/pip install -e ./packages/agency-content
ok "agency CLIs installed"

echo ""
echo "==> Preparing vendored MCP dependencies"
uv sync --directory packages/freepik-fastmcp
ok "vendored MCP dependencies ready"

echo ""
echo "==> Validating MCP JSON files"
python3 -m json.tool .mcp.json >/dev/null
python3 -m json.tool mcp/agents/research.json >/dev/null
python3 -m json.tool mcp/agents/storyboard.json >/dev/null
ok "MCP configs are valid JSON"

echo ""
echo "==> Checking npm MCP packages"
npm view @perplexity-ai/mcp-server@0.9.0 version >/dev/null
npm view @playwright/mcp@0.0.73 version >/dev/null
npm view firecrawl-mcp@3.14.1 version >/dev/null
npm view chrome-devtools-mcp@0.23.0 version >/dev/null
npm view @roomi-fields/notebooklm-mcp@1.5.9 version >/dev/null
npm view mcp-remote@0.1.38 version >/dev/null
npm view @apify/actors-mcp-server@0.9.20 version >/dev/null
ok "pinned npm MCP packages are available"

if [[ "$SKIP_PLAYWRIGHT_BROWSER" -eq 0 ]]; then
  echo ""
  echo "==> Installing Playwright Chromium browser"
  scripts/mcp-npx.sh -y playwright@1.56.1 install chromium
  ok "Playwright Chromium ready"
else
  warn "skipped Playwright browser install"
fi

if [[ "$SKIP_SCRAPLING_BROWSER" -eq 0 ]]; then
  echo ""
  echo "==> Installing Scrapling browser dependencies"
  .venv/bin/scrapling install
  ok "Scrapling browser dependencies ready"
else
  warn "skipped Scrapling browser dependency install"
fi

echo ""
echo "==> Checking API key environment variables"
for var in FREEPIK_API_KEY PERPLEXITY_API_KEY FIRECRAWL_API_KEY CAPSULEHUB_API_KEY APIFY_API_TOKEN; do
  if [[ -n "${!var:-}" ]]; then
    ok "$var is set"
  else
    warn "$var is not set"
  fi
done

echo ""
echo "Bootstrap complete."
echo "Activate the Python environment with:"
echo "  source .venv/bin/activate"
echo ""
echo "If any API key showed WARN, add it to your shell profile or copy env.example to .env and fill it in."
