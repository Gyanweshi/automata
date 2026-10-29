"""Run the Obsidian Agent_Sessions watchdog."""
from __future__ import annotations

import argparse
import logging

from agency_common import run_session_watchdog


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="Link and index new Agent_Sessions notes.")
    parser.add_argument("--commit-vault", action="store_true",
                        help="Allow writing Related Concepts backlinks into session notes.")
    parser.add_argument("--commit-reason", help="Required with --commit-vault; recorded by the vault write gate.")
    args = parser.parse_args()
    if args.commit_vault and not (args.commit_reason or "").strip():
        parser.error("--commit-reason is required with --commit-vault")
    run_session_watchdog(commit_vault=args.commit_vault, commit_reason=args.commit_reason)
