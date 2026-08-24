#!/usr/bin/env bash
set -euo pipefail

RETENTION_DAYS=7
while (($#)); do
    case "$1" in
        --retention-days)
            RETENTION_DAYS="${2:?missing retention days}"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

if ! [[ "$RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Retention days must be a positive integer" >&2
    exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
PYTHON="$ROOT_DIR/.venv/bin/python"
SOURCE_DIR="$ROOT_DIR/packages/agency-common/src"
LOG_DIR="$ROOT_DIR/.housekeeper/logs"
LOG_PATH="$LOG_DIR/watchdog.log"

if [[ ! -x "$PYTHON" ]]; then
    echo "Automata virtualenv is missing: $PYTHON" >&2
    exit 1
fi

mkdir -p -- "$LOG_DIR"
if [[ -n "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="$SOURCE_DIR:$PYTHONPATH"
else
    export PYTHONPATH="$SOURCE_DIR"
fi

started="$(date --iso-8601=seconds)"
set +e
output="$("$PYTHON" -m agency_common.housekeeping purge \
    --repo "$ROOT_DIR" \
    --older-than-days "$RETENTION_DAYS" \
    --confirm delete 2>&1)"
exit_code=$?
set -e

{
    printf '[%s] exit=%s\n' "$started" "$exit_code"
    printf '%s\n' "$output"
} >> "$LOG_PATH"

if ((exit_code != 0)); then
    echo "Housekeeper watchdog failed with exit code $exit_code. See $LOG_PATH" >&2
    exit "$exit_code"
fi
