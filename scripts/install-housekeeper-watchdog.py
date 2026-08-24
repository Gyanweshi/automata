#!/usr/bin/env python3
"""Install the housekeeping watchdog using this machine's native scheduler."""
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "packages" / "agency-common" / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from agency_common.watchdog_installer import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
