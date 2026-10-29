"""Score Second Brain retrieval against a fixed question set.

The question file is YAML: a list of entries, each with a `question` and an `expect` list of
vault-relative note paths that answer it. A question scores a hit at rank r when the r-th unique
note returned is one of its expected notes. Reports hit@1, hit@k and mean reciprocal rank per
collection, so a change to chunking or the embedder can be judged on numbers, not impressions.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from .knowledge_reader import get_vault_path
from .obsidian_vector_index import DEFAULT_DB_PATH, search_second_brain_notes

DEFAULT_QUESTIONS_PATH = "Operations/RAG_Eval/rag-eval-questions.yaml"


def load_questions(path: Path) -> list[dict[str, Any]]:
    entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    for entry in entries:
        if not entry.get("question") or not entry.get("expect"):
            raise ValueError(f"Eval entry needs `question` and `expect`: {entry}")
    return entries


def evaluate_collection(
    questions: list[dict[str, Any]],
    *,
    collection_name: str,
    vault_path: Path,
    db_path: str | Path = DEFAULT_DB_PATH,
    k: int = 3,
) -> dict[str, Any]:
    """Run every question against one collection and return per-question ranks and summary scores."""
    rows: list[dict[str, Any]] = []
    for entry in questions:
        expected = {str((vault_path / rel).resolve()) for rel in entry["expect"]}
        notes = search_second_brain_notes(entry["question"], num_results=k, db_path=db_path, collection_name=collection_name)
        found = [str(Path(note["filepath"]).resolve()) for note in notes if note.get("filepath")]
        rank = next((index + 1 for index, filepath in enumerate(found) if filepath in expected), None)
        rows.append({"question": entry["question"], "rank": rank, "top": notes[0]["wikilink"] if notes else None})

    total = len(rows) or 1
    return {
        "collection": collection_name,
        "hit_at_1": sum(1 for row in rows if row["rank"] == 1) / total,
        "hit_at_k": sum(1 for row in rows if row["rank"] is not None) / total,
        "mrr": sum(1 / row["rank"] for row in rows if row["rank"]) / total,
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score Second Brain retrieval against a question set.")
    parser.add_argument("--collection", action="append", required=True, help="Repeat to compare collections.")
    parser.add_argument("--questions", help=f"Question YAML (default: <vault>/{DEFAULT_QUESTIONS_PATH}).")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("-k", type=int, default=3)
    parser.add_argument("--verbose", action="store_true", help="Print the rank of every question.")
    args = parser.parse_args(argv)

    vault_path = get_vault_path()
    questions = load_questions(Path(args.questions) if args.questions else vault_path / DEFAULT_QUESTIONS_PATH)
    print(f"{len(questions)} questions, k={args.k}\n")
    print(f"{'collection':<20} {'hit@1':>6} {'hit@' + str(args.k):>6} {'MRR':>6}")
    reports = [
        evaluate_collection(questions, collection_name=name, vault_path=vault_path, db_path=args.db_path, k=args.k)
        for name in args.collection
    ]
    for report in reports:
        print(f"{report['collection']:<20} {report['hit_at_1']:>6.0%} {report['hit_at_k']:>6.0%} {report['mrr']:>6.2f}")

    if args.verbose:
        for report in reports:
            print(f"\n[{report['collection']}]")
            for row in report["rows"]:
                print(f"  {row['rank'] or '-':>2}  {row['question'][:70]:<70}  top: {row['top']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
