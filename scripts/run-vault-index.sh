#!/bin/sh
# Legacy entry point for schedules installed before scripts/schedule.py existed; the job itself is Python.
# Re-schedule with `python3 scripts/schedule.py install vault-index`, after which this file is unused.
exec "$(dirname "$0")/../.venv/bin/python" "$(dirname "$0")/schedule.py" run vault-index "$@"
