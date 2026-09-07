"""Retrieve creative mechanisms for an agent. No network, generation, or writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

BANK_PATH = Path(__file__).resolve().parents[1] / "references" / "agency-bank.json"
HISTORICAL_BANK_PATH = BANK_PATH.with_name("historical-bank.json")
FRAMEWORK_BANK_PATH = BANK_PATH.with_name("frameworks.json")
STAGES = ("insight", "memory", "question", "proposition", "differentiation", "evaluation", "testing")
ALTITUDES = ("platform", "campaign", "execution")


def load_bank(path: Path = BANK_PATH) -> dict:
    bank = json.loads(path.read_text(encoding="utf-8"))
    if bank.get("schema_version") != 1:
        raise ValueError("Unsupported bank schema version")
    sources = bank.get("sources", {})
    seen = set()
    for tool in bank["tools"]:
        if not tool.get("id") or tool["id"] in seen:
            raise ValueError("Missing or duplicate tool ID")
        seen.add(tool["id"])
        required = ("name", "family", "core")
        if bank.get("bank_kind") != "agency_mechanisms":
            required += ("source_heading", "verification")
        for key in required:
            if not isinstance(tool.get(key), str) or not tool[key].strip():
                raise ValueError(f"Missing {key} for {tool['id']}")
        if not isinstance(tool.get("tags"), list) or not tool["tags"] or not all(isinstance(t, str) and t.strip() for t in tool["tags"]):
            raise ValueError(f"Invalid tags for {tool['id']}")
        app = tool.get("application", {})
        app_keys = ("prompt",) if bank.get("bank_kind") == "agency_mechanisms" else ("prompt", "original_example")
        for key in app_keys:
            if not isinstance(app.get(key), str) or not app[key].strip():
                raise ValueError(f"Missing application {key} for {tool['id']}")
        app_list_keys = ("best_for", "failure_modes") if bank.get("bank_kind") == "agency_mechanisms" else ("inputs", "best_for", "failure_modes")
        for key in app_list_keys:
            if not isinstance(app.get(key), list) or not app[key] or not all(isinstance(v, str) and v.strip() for v in app[key]):
                raise ValueError(f"Invalid application {key} for {tool['id']}")
        if bank.get("bank_kind") == "frameworks":
            if tool.get("stage") not in STAGES:
                raise ValueError(f"Invalid stage for {tool['id']}")
            for key in ("outputs", "steps"):
                if not isinstance(app.get(key), list) or not app[key] or not all(isinstance(v, str) and v.strip() for v in app[key]):
                    raise ValueError(f"Invalid application {key} for {tool['id']}")
        related = tool.get("related_historical_ids", [])
        if not isinstance(related, list) or not all(isinstance(value, str) and value.strip() for value in related):
            raise ValueError(f"Invalid related_historical_ids for {tool['id']}")
    if bank.get("bank_kind") == "agency_mechanisms":
        vocabulary = bank.get("tag_vocabulary")
        families = bank.get("family_vocabulary")
        if not isinstance(vocabulary, list) or not vocabulary or len(set(vocabulary)) != len(vocabulary):
            raise ValueError("Invalid tag_vocabulary")
        if not isinstance(families, list) or not families or len(set(families)) != len(families):
            raise ValueError("Invalid family_vocabulary")
        vocabulary_set = set(vocabulary)
        family_set = set(families)
        for tool in bank["tools"]:
            if tool["family"] not in family_set:
                raise ValueError(f"Unknown family for {tool['id']}: {tool['family']}")
            if not set(tool["tags"]) <= vocabulary_set:
                unknown_tags = sorted(set(tool["tags"]) - vocabulary_set)
                raise ValueError(f"Unknown tag for {tool['id']}: {', '.join(unknown_tags)}")
        altitude_map = bank.get("altitude_by_id")
        if not isinstance(altitude_map, dict) or set(altitude_map) != {tool["id"] for tool in bank["tools"]}:
            raise ValueError("altitude_by_id must cover every agency mechanism")
        if not all(value in ALTITUDES for value in altitude_map.values()):
            raise ValueError("Invalid mechanism altitude")
    return bank


def select_tools(bank: dict, tags=(), ids=(), exclude=(), limit=6, stage=None, allow_near_twins=False, altitude=None) -> list[dict]:
    if limit < 1:
        raise ValueError("Limit must be positive")
    if stage is not None and (stage not in STAGES or bank.get("bank_kind") != "frameworks"):
        raise ValueError("Stage selection requires a framework bank and a known stage")
    if altitude is not None and (altitude not in ALTITUDES or bank.get("bank_kind") != "agency_mechanisms"):
        raise ValueError("Altitude selection requires an agency mechanism bank and a known altitude")
    known = {tool["id"] for tool in bank["tools"]}
    unknown = (set(ids) | set(exclude)) - known
    if unknown:
        raise ValueError(f"Unknown tool IDs: {', '.join(sorted(unknown))}")
    tags = {tag.casefold() for tag in tags}
    selected = [
        ({**tool, "altitude": bank["altitude_by_id"][tool["id"]]} if bank.get("bank_kind") == "agency_mechanisms" else tool)
        for tool in bank["tools"]
        if (not ids or tool["id"] in ids)
        and tool["id"] not in exclude
        and (stage is None or tool["stage"] == stage)
        and (altitude is None or bank["altitude_by_id"][tool["id"]] == altitude)
        and (not tags or tags.intersection(tag.casefold() for tag in tool["tags"]))
    ][:limit]
    if not allow_near_twins and ids and bank.get("pairing_rules"):
        selected_ids = {tool["id"] for tool in selected}
        for left, right in bank["pairing_rules"].get("avoid_together", []):
            if left in selected_ids and right in selected_ids:
                raise ValueError(f"Near-twin mechanisms selected together: {left}, {right}; use --allow-near-twins when intentional")
    return selected


def near_twin_warning(bank: dict, selected: list[dict]) -> list[dict]:
    """Report near-twin pairs in a retrieved set without blocking browsing."""
    selected_ids = {tool["id"] for tool in selected}
    return [
        {"ids": [left, right], "reason": bank["pairing_rules"].get("reason", "Near-twin mechanisms may be variations.")}
        for left, right in bank.get("pairing_rules", {}).get("avoid_together", [])
        if left in selected_ids and right in selected_ids
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--id", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--allow-near-twins", action="store_true", help="Permit explicitly paired near-twin mechanisms")
    parser.add_argument("--altitude", choices=ALTITUDES, help="Filter agency mechanisms by platform, campaign, or execution altitude")
    bank_mode = parser.add_mutually_exclusive_group()
    bank_mode.add_argument("--historical", action="store_true", help="Use the original 15-entry secondary-source bank (dob-* IDs)")
    bank_mode.add_argument("--frameworks", action="store_true", help="Use public marketing frameworks from IDEO.org, Strategyzer and Blue Ocean Strategy")
    parser.add_argument("--stage", choices=STAGES, help="Filter framework entries by marketing task")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list", action="store_true", help="Show all IDs, names, families and tags")
    mode.add_argument("--list-tags", action="store_true", help="Show the closed tag vocabulary and counts")
    mode.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    try:
        bank = load_bank(FRAMEWORK_BANK_PATH if args.frameworks else HISTORICAL_BANK_PATH if args.historical else BANK_PATH)
        if args.stage and not args.frameworks:
            raise ValueError("--stage requires --frameworks")
        if args.list or args.list_tags or args.validate:
            if args.tag or args.id or args.exclude or args.stage or args.altitude or args.limit != 6 or args.allow_near_twins:
                raise ValueError("List/validate cannot be combined with selection options")
            if args.validate:
                print(json.dumps({"valid": True, "tool_count": len(bank["tools"]), "bank_version": bank["bank_version"]}))
                return
            if args.list_tags:
                counts = {}
                for tool in bank["tools"]:
                    for tag in tool["tags"]:
                        counts[tag] = counts.get(tag, 0) + 1
                print(json.dumps({"bank_version": bank["bank_version"], "tags": dict(sorted(counts.items()))}, indent=2))
                return
            selected = [{**{k: t[k] for k in ("id", "name", "family", "tags", "stage", "source_id") if k in t}, **({"altitude": bank["altitude_by_id"][t["id"]]} if bank.get("bank_kind") == "agency_mechanisms" else {})} for t in bank["tools"]]
        else:
            selected = select_tools(bank, args.tag, args.id, args.exclude, args.limit, args.stage, args.allow_near_twins, args.altitude)
        used_sources = {t["source_id"] for t in selected if "source_id" in t}
        payload = {
            "bank_version": bank["bank_version"], "scope": bank["scope"],
            "checked_on": bank["checked_on"], "attribution": bank["attribution"],
            "current_primary_access": bank.get("current_primary_access"),
            "tools": selected, "sources": {s: bank.get("sources", {})[s] for s in sorted(used_sources)},
        }
        warnings = near_twin_warning(bank, selected)
        if warnings:
            payload["near_twin_warning"] = warnings
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
