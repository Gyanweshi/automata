#!/usr/bin/env bash
set -euo pipefail

DAILY_AT="03:00"
RETENTION_DAYS=7
while (($#)); do
    case "$1" in
        --daily-at)
            DAILY_AT="${2:?missing daily time}"
            shift 2
            ;;
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

if ! [[ "$DAILY_AT" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ ]]; then
    echo "Daily time must use HH:MM" >&2
    exit 2
fi
if ! [[ "$RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Retention days must be a positive integer" >&2
    exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
RUNNER="$SCRIPT_DIR/run-housekeeper-watchdog.sh"
PYTHON="$ROOT_DIR/.venv/bin/python"
if [[ ! -f "$RUNNER" ]]; then
    echo "Linux watchdog runner is missing: $RUNNER" >&2
    exit 1
fi
if [[ ! -x "$PYTHON" ]]; then
    echo "Automata virtualenv is missing: $PYTHON" >&2
    exit 1
fi
if [[ "$RUNNER" == *'"'* || "$RUNNER" == *$'\n'* ]]; then
    echo "Unsupported quote or newline in repo path" >&2
    exit 1
fi

if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
    UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
    SERVICE_PATH="$UNIT_DIR/automata-housekeeper.service"
    TIMER_PATH="$UNIT_DIR/automata-housekeeper.timer"
    mkdir -p -- "$UNIT_DIR"

    {
        printf '%s\n' '[Unit]'
        printf '%s\n' 'Description=Automata quarantine housekeeper'
        printf '\n%s\n' '[Service]'
        printf '%s\n' 'Type=oneshot'
        printf 'ExecStart=/usr/bin/env bash "%s" --retention-days %s\n' "$RUNNER" "$RETENTION_DAYS"
    } > "$SERVICE_PATH"

    {
        printf '%s\n' '[Unit]'
        printf '%s\n' 'Description=Run Automata housekeeper daily'
        printf '\n%s\n' '[Timer]'
        printf 'OnCalendar=*-*-* %s:00\n' "$DAILY_AT"
        printf '%s\n' 'Persistent=true'
        printf '%s\n' 'Unit=automata-housekeeper.service'
        printf '\n%s\n' '[Install]'
        printf '%s\n' 'WantedBy=timers.target'
    } > "$TIMER_PATH"

    systemctl --user daemon-reload
    systemctl --user enable --now automata-housekeeper.timer
    echo "Installed adapter: linux-systemd-user"
    systemctl --user list-timers automata-housekeeper.timer --no-pager
    exit 0
fi

if ! command -v crontab >/dev/null 2>&1; then
    echo "Neither a usable user systemd session nor crontab is available" >&2
    exit 1
fi

hour="${DAILY_AT%%:*}"
minute="${DAILY_AT##*:}"
hour="$((10#$hour))"
minute="$((10#$minute))"
runner_quoted="$(printf '%q' "$RUNNER")"
marker="# automata-housekeeper"
temp_cron="$(mktemp)"
trap 'rm -f -- "$temp_cron"' EXIT
(crontab -l 2>/dev/null || true) | grep -vF "$marker" > "$temp_cron" || true
printf '%s %s * * * /usr/bin/env bash %s --retention-days %s %s\n' \
    "$minute" "$hour" "$runner_quoted" "$RETENTION_DAYS" "$marker" >> "$temp_cron"
crontab "$temp_cron"
echo "Installed adapter: linux-cron"
