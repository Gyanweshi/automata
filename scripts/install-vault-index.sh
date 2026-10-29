#!/usr/bin/env bash
# Schedule the nightly Second Brain index rebuild (systemd user timer, else cron).
set -euo pipefail

DAILY_AT="02:30"
while (($#)); do
    case "$1" in
        --daily-at)
            DAILY_AT="${2:?missing daily time}"
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

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$SCRIPT_DIR/run-vault-index.sh"
if [[ "$RUNNER" == *'"'* || "$RUNNER" == *$'\n'* ]]; then
    echo "Unsupported quote or newline in repo path" >&2
    exit 1
fi

if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
    UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
    mkdir -p -- "$UNIT_DIR"

    {
        printf '%s\n' '[Unit]'
        printf '%s\n' 'Description=Automata Second Brain index rebuild'
        printf '\n%s\n' '[Service]'
        printf '%s\n' 'Type=oneshot'
        printf '%s\n' 'Nice=10'
        printf 'ExecStart=/usr/bin/env bash "%s"\n' "$RUNNER"
    } > "$UNIT_DIR/automata-vault-index.service"

    {
        printf '%s\n' '[Unit]'
        printf '%s\n' 'Description=Rebuild the Automata Second Brain index nightly'
        printf '\n%s\n' '[Timer]'
        printf 'OnCalendar=*-*-* %s:00\n' "$DAILY_AT"
        printf '%s\n' 'Persistent=true'
        printf '%s\n' 'Unit=automata-vault-index.service'
        printf '\n%s\n' '[Install]'
        printf '%s\n' 'WantedBy=timers.target'
    } > "$UNIT_DIR/automata-vault-index.timer"

    systemctl --user daemon-reload
    systemctl --user enable --now automata-vault-index.timer
    echo "Installed adapter: linux-systemd-user"
    systemctl --user list-timers automata-vault-index.timer --no-pager
    exit 0
fi

if ! command -v crontab >/dev/null 2>&1; then
    echo "Neither a usable user systemd session nor crontab is available" >&2
    exit 1
fi

hour="$((10#${DAILY_AT%%:*}))"
minute="$((10#${DAILY_AT##*:}))"
marker="# automata-vault-index"
temp_cron="$(mktemp)"
trap 'rm -f -- "$temp_cron"' EXIT
(crontab -l 2>/dev/null || true) | grep -vF "$marker" > "$temp_cron" || true
printf '%s %s * * * /usr/bin/env bash %s %s\n' "$minute" "$hour" "$(printf '%q' "$RUNNER")" "$marker" >> "$temp_cron"
crontab "$temp_cron"
echo "Installed adapter: linux-cron"
