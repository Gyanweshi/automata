#!/usr/bin/env python3
"""Run or schedule the repo's nightly jobs on Linux or Windows (see agency_common.scheduled_jobs).

    python scripts/schedule.py run vault-index
    python scripts/schedule.py install vault-index [--daily-at 02:30]
    python scripts/schedule.py install housekeeper [--daily-at 03:00] [--retention-days 7] [--dry-run]
"""
from __future__ import annotations

import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "packages" / "agency-common" / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from agency_common.scheduled_jobs import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
