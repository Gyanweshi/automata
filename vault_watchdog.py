"""Run the Obsidian Agent_Sessions watchdog."""
from __future__ import annotations

import logging

from agency_common import run_session_watchdog


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s")
    run_session_watchdog()
