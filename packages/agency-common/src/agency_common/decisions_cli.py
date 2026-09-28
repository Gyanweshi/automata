"""`agency-decisions`: inspect the decision log, record your verdicts, and check calibration."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, Sequence

from .decide import ROUTE_ACT, DecisionLog


def _row(d: dict) -> str:
    human = d["human"] if d["human"] is not None else "-"
    return (
        f"{d['decision_id']}  {d['at'][:16]}  {d['name']:<32} {d['question']:<18} "
        f"{d['answer']:<12} {d['confidence']:.2f} {d['route']:<8} {d['source']:<24} human={human}"
    )


def _filtered(log: DecisionLog, args: argparse.Namespace) -> list[dict]:
    rows = log.decisions()
    if getattr(args, "name", None):
        rows = [r for r in rows if r["name"].startswith(args.name)]
    if getattr(args, "route", None):
        rows = [r for r in rows if r["route"] == args.route]
    if getattr(args, "pending", False):
        rows = [r for r in rows if r["human"] is None]
    return rows[-args.limit:] if getattr(args, "limit", 0) else rows


def _review(log: DecisionLog, args: argparse.Namespace, ask: Callable[[str], str], out: Callable[[str], None]) -> int:
    """Walk unreviewed decisions, newest first. Enter agrees, a label overrides, `s` skips, `q` quits."""
    args.pending = True
    rows = [r for r in _filtered(log, args) if args.all or r["route"] != ROUTE_ACT]
    if not rows:
        out("Nothing to review.")
        return 0
    done = 0
    for row in reversed(rows):
        out("\n" + _row(row))
        out("  state: " + row["state"].replace("\n", " ")[:300])
        labels = list(row["probs"])
        reply = ask(f"  [Enter]=agree with {row['answer']!r}, one of {labels} to override, s=skip, q=quit: ").strip()
        if reply == "q":
            break
        if reply == "s":
            continue
        answer = row["answer"] if reply == "" else reply
        if answer not in labels:
            out(f"  Not a valid answer, skipped: {reply!r}")
            continue
        note = ask("  note (optional): ").strip() if answer != row["answer"] else ""
        log.record_human(row["decision_id"], answer, note)
        done += 1
    out(f"\nRecorded {done} verdict(s).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agency-decisions", description=__doc__)
    parser.add_argument("--workspace", help="Workspace directory (default: AGENCY_WORKSPACE or ./workspace)")
    sub = parser.add_subparsers(dest="command", required=True)

    def filters(p: argparse.ArgumentParser, limit: int) -> None:
        p.add_argument("--name", help="Only decisions whose name starts with this, e.g. research.")
        p.add_argument("--route", choices=["act", "review", "escalate"])
        p.add_argument("--limit", type=int, default=limit)

    lst = sub.add_parser("list", help="Recent decisions")
    filters(lst, 20)
    lst.add_argument("--pending", action="store_true", help="Only decisions with no human verdict yet")
    show = sub.add_parser("show", help="One decision in full")
    show.add_argument("decision_id")
    verdict = sub.add_parser("verdict", help="Record what you actually decided")
    verdict.add_argument("decision_id")
    verdict.add_argument("answer")
    verdict.add_argument("--note", default="")
    review = sub.add_parser("review", help="Interactively verdict pending decisions (review/escalate by default)")
    filters(review, 50)
    review.add_argument("--all", action="store_true", help="Include confident `act` decisions too")
    sub.add_parser("calibration", help="How often the model agreed with you, by source and confidence band")
    return parser


def main(argv: Sequence[str] | None = None, *, ask: Callable[[str], str] = input, out: Callable[[str], None] = print) -> int:
    args = build_parser().parse_args(argv)
    if args.workspace:
        workspace = Path(args.workspace)
    else:
        from .config import AgencyConfig

        workspace = AgencyConfig.from_env().workspace
    log = DecisionLog(workspace)

    try:
        if args.command == "list":
            rows = _filtered(log, args)
            for row in rows:
                out(_row(row))
            out(f"{len(rows)} decision(s)" if rows else "No decisions recorded.")
        elif args.command == "show":
            out(json.dumps(log.find(args.decision_id), indent=2, ensure_ascii=False))
        elif args.command == "verdict":
            row = log.find(args.decision_id)
            if args.answer not in row["probs"]:
                raise KeyError(f"{args.answer!r} is not an answer for {row['question']}: choose from {list(row['probs'])}")
            log.record_human(row["decision_id"], args.answer, args.note)
            out(f"Recorded {args.answer!r} for {row['decision_id']} (model said {row['answer']!r}).")
        elif args.command == "review":
            return _review(log, args, ask, out)
        else:
            report = log.calibration()
            if not report:
                out("No reviewed decisions yet. Use `agency-decisions review` to add verdicts.")
            for source, bands in report.items():
                out(source)
                for band, cell in bands.items():
                    out(f"  confidence {band}: agreed {cell['agree']}/{cell['reviewed']} ({cell['rate']:.0%})")
    except KeyError as exc:
        out(f"error: {exc.args[0]}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
