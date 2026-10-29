"""Command-line Second Brain search for agents that run shell commands (Codex, Claude Code).

Prints the best-matching note sections with `[[Note#Heading]]` citations, the same context the
autonomous harness gets from its `search_second_brain` tool. For broad research questions only:
brand context comes from reading the brand note directly.
"""
from __future__ import annotations

import argparse
import logging
import sys

from .obsidian_vector_index import DEFAULT_COLLECTION_NAME, DEFAULT_DB_PATH, search_second_brain


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agency-vault-search",
        description="Search the Obsidian Second Brain index and print matching note sections.",
    )
    parser.add_argument("query", nargs="+", help="What to look for, in plain words.")
    parser.add_argument("-n", "--num-results", type=int, default=3, help="Number of notes to return (default 3).")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION_NAME)
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        # Windows consoles default to a legacy code page; notes contain em dashes and Devanagari.
        sys.stdout.reconfigure(encoding="utf-8")
    print(search_second_brain(" ".join(args.query), num_results=args.num_results,
                              db_path=args.db_path, collection_name=args.collection))
    return 0


if __name__ == "__main__":
    sys.exit(main())
