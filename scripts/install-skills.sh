#!/usr/bin/env bash
# Portable project registrations for Codex and Claude; never changes global installs.
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec "$REPO_DIR/.venv/bin/python" "$REPO_DIR/scripts/sync-skills.py" --sync "$@"
