#!/usr/bin/env bash
# Runs the Scrapling MCP server from the repo virtualenv when available.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -x "$ROOT_DIR/.venv/bin/scrapling" ]]; then
  exec "$ROOT_DIR/.venv/bin/scrapling" mcp "$@"
fi

if [[ -x "$ROOT_DIR/.venv/Scripts/scrapling.exe" ]]; then
  exec "$ROOT_DIR/.venv/Scripts/scrapling.exe" mcp "$@"
fi

exec scrapling mcp "$@"
