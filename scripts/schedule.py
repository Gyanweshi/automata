#!/usr/bin/env python3
"""Run or schedule the repo's nightly jobs on Linux or Windows (see agency_common.scheduled_jobs).

    python scripts/schedule.py run vault-index
    python scripts/schedule.py install vault-index [--daily-at 02:30]
    python scripts/schedule.py install housekeeper [--daily-at 03:00] [--retention-days 7] [--dry-run]
"""
from __future__ import annotations

import os
import subprocess  # nosec B404 - re-runs this script with the repo's own venv Python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
VENV_PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
# The job code needs the repo's packages, which live in .venv: if started with another Python
# (python3, py, the Store stub), hand over to the venv Python instead of failing on imports.
if VENV_PYTHON.exists() and Path(sys.prefix).resolve() != VENV.resolve():
    sys.exit(subprocess.call([str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]]))  # nosec B603

SOURCE = ROOT / "packages" / "agency-common" / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from agency_common.scheduled_jobs import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
