#!/usr/bin/env bash
# Rebuild the chunked Second Brain index in place. Run nightly by install-vault-index.sh.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"
LOG_DIR="$ROOT_DIR/.housekeeper/logs"
LOG_PATH="$LOG_DIR/vault-index.log"

if [[ ! -x "$PYTHON" ]]; then
    echo "Automata virtualenv is missing: $PYTHON" >&2
    exit 1
fi

mkdir -p -- "$LOG_DIR"
# The vault path comes from .env, which is looked up from the working directory.
cd -- "$ROOT_DIR"

started="$(date --iso-8601=seconds)"
set +e
output="$("$PYTHON" -m agency_common.obsidian_vector_index 2>&1)"
exit_code=$?
set -e

{
    printf '[%s] exit=%s\n' "$started" "$exit_code"
    printf '%s\n' "$output" | grep -E '^(INFO|WARNING|ERROR)' || true
} >> "$LOG_PATH"

if ((exit_code != 0)); then
    echo "Vault index rebuild failed with exit code $exit_code. See $LOG_PATH" >&2
    printf '%s\n' "$output" | tail -20 >&2
    exit "$exit_code"
fi
