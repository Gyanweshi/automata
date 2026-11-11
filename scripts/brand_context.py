"""Find every place a brand's context lives, with any Python and no installed packages.

Usage (Windows: `py scripts\\brand_context.py ...`; any OS: `make brand-context BRAND=<brand>`):
    python3 scripts/brand_context.py <brand>             # brand note, brand folder, workspace and other name matches
    python3 scripts/brand_context.py <brand> --contents  # also list notes whose text mentions the brand (slower)
    python3 scripts/brand_context.py --vault             # print the resolved vault path only

Brand work is not always in `Brands/<slug>.md`: a brand can have only a `Brands/<slug>/` folder of drafts, or
notes elsewhere in the vault. This script checks all of them so "no brand note" is never mistaken for "no prior work".

It uses the standard library only, so system `python3` works even when the repo's venv packages are missing,
and it never fails silently: a bad vault path exits 2, and finding nothing exits 1 with the list of places checked.
Vault rules match `agency_common.get_vault_path()`: OBSIDIAN_VAULT_PATH (environment, then .env) or, when it is
empty, `workspace/vault/` in the checkout.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ENV_VAR = "OBSIDIAN_VAULT_PATH"
# Obsidian, Syncthing and session-log internals: never brand context.
SKIP_DIRS = {".obsidian", ".git", ".stversions", ".stfolder", ".trash", "Claude_Sessions", "Codex_Sessions",
             "Agent_Sessions"}
MAX_LISTED = 40
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)
# `brand:` with an inline value, or a bare `brand:` followed by indented `- item` lines (a YAML block list).
BRAND_FIELD = re.compile(r"^brand:[ \t]*([^\r\n]*)((?:\r?\n[ \t]+-[^\r\n]*)*)", re.M)
WIKILINK = re.compile(r"\[\[([^\]|#]+)")


class VaultError(RuntimeError):
    pass


def repo_root() -> Path:
    for origin in (Path.cwd(), Path(__file__).resolve()):
        for parent in (origin, *origin.parents):
            if (parent / "AGENTS.md").is_file() and (parent / "packages").is_dir():
                return parent
    return Path(__file__).resolve().parents[1]


def read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].strip()
        values[key.strip()] = value
    return values


def resolve_vault(root: Path) -> tuple[Path, str]:
    """Return (vault path, where the setting came from). Raises VaultError for a configured but unusable path."""
    if ENV_VAR in os.environ:  # like load_dotenv: an exported variable wins over .env
        raw, source = os.environ[ENV_VAR].strip(), "environment"
    else:
        raw, source = read_dotenv(root / ".env").get(ENV_VAR, "").strip(), ".env"
    if not raw:
        return root / "workspace" / "vault", f"{ENV_VAR} empty -> local vault"
    vault = Path(raw).expanduser().resolve()
    if not vault.exists():
        raise VaultError(f"{ENV_VAR} ({source}) points to {vault}, which does not exist. Is the drive mounted?")
    if not vault.is_dir():
        raise VaultError(f"{ENV_VAR} ({source}) must be a directory: {vault}")
    return vault, f"{ENV_VAR} from {source}"


def normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def walk(base: Path):
    for current, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        yield Path(current), dirnames, filenames


def stamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")


def find_context(brand: str, root: Path, vault: Path) -> dict[str, list[Path]]:
    key = normalise(brand)
    if not key:
        raise ValueError("brand must contain letters or digits")
    brands_dir = vault / "Brands"
    found: dict[str, list[Path]] = {"notes": [], "folders": [], "workspace": [], "other": [], "tagged": []}

    if brands_dir.is_dir():
        for entry in sorted(brands_dir.iterdir()):
            if entry.name in SKIP_DIRS or normalise(entry.stem if entry.is_file() else entry.name) != key:
                continue
            if entry.is_file() and entry.suffix.lower() == ".md":
                found["notes"].append(entry)
            elif entry.is_dir():
                found["folders"].append(entry)

    workspace = root / "workspace"
    if workspace.is_dir():
        found["workspace"] = [p for p in sorted(workspace.iterdir()) if p.is_dir() and normalise(p.name) == key]

    # Anything else in the vault whose file or folder name mentions the brand (Research/<topic>, Games/, ...).
    claimed = [p.resolve() for p in found["notes"] + found["folders"]]
    for current, dirnames, filenames in walk(vault):
        if any(current.resolve() == c or c in current.resolve().parents for c in claimed):
            dirnames[:] = []
            continue
        for name in dirnames + filenames:
            if key in normalise(Path(name).stem if name in filenames else name):
                path = current / name
                if path.resolve() not in claimed:
                    found["other"].append(path)

    # Notes filed elsewhere but tagged `brand: <slug>` in their frontmatter (e.g. Research/<topic>/ for a client).
    covered = claimed + [p.resolve() for p in found["other"]]
    for current, dirnames, filenames in walk(vault):
        if any(current.resolve() == c or c in current.resolve().parents for c in covered):
            dirnames[:] = []
            continue
        for name in filenames:
            path = current / name
            if name.lower().endswith(".md") and path.resolve() not in covered and key in frontmatter_brands(path):
                found["tagged"].append(path)
    return found


def brand_values(raw: str) -> set[str]:
    """Normalised brands named by a raw `brand:` value: `maple`, `"maple"`, `[maple, kerr]`, a block list, or a
    wikilink such as `"[[Brands/maple|Maple]]"` (which counts as the link target's note name, `maple`)."""
    values = {normalise(target.strip().rstrip("/").rsplit("/", 1)[-1]) for target in WIKILINK.findall(raw)}
    rest = "\n".join(line.split(" #", 1)[0] for line in re.sub(r"\[\[[^\]]*\]\]", "", raw).splitlines())
    for item in re.split(r"[,\n]", rest.strip().strip("[]")):
        values.add(normalise(item.strip().lstrip("-").strip().strip("'\"")))
    values.discard("")
    return values


def frontmatter_brands(path: Path) -> set[str]:
    """The normalised brands in a note's `brand:` frontmatter, or an empty set (reads only the file's head)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            head = handle.read(4096)
    except OSError:
        return set()
    block = FRONTMATTER.match(head)
    field = BRAND_FIELD.search(block.group(1)) if block else None
    return brand_values(field.group(1) + field.group(2)) if field else set()


def find_mentions(brand: str, vault: Path, exclude: list[Path]) -> list[Path]:
    """Notes whose text mentions the brand (case-insensitive), outside the paths already listed. Portable grep."""
    pattern = re.compile(re.escape(brand), re.I)
    skip = [p.resolve() for p in exclude]
    hits: list[Path] = []
    for current, dirnames, filenames in walk(vault):
        if any(current.resolve() == s or s in current.resolve().parents for s in skip):
            dirnames[:] = []
            continue
        for name in filenames:
            path = current / name
            if name.lower().endswith(".md") and path.resolve() not in skip:
                try:
                    if pattern.search(path.read_text(encoding="utf-8", errors="replace")):
                        hits.append(path)
                except OSError:
                    continue
    return hits


def list_folder(folder: Path) -> list[str]:
    files = [current / f for current, _, filenames in walk(folder) for f in filenames if f.lower().endswith(".md")]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    lines = [f"    {stamp(p)}  {p.relative_to(folder)}" for p in files[:MAX_LISTED]]
    if len(files) > MAX_LISTED:
        lines.append(f"    ... {len(files) - MAX_LISTED} more Markdown files")
    media = sum(1 for _, _, filenames in walk(folder) for f in filenames if not f.lower().endswith(".md"))
    if media:
        lines.append(f"    + {media} non-Markdown files (renders, audio, images)")
    return lines or ["    (no Markdown files)"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("brand", nargs="?", help="brand slug or name, e.g. rankup")
    parser.add_argument("--vault", action="store_true", help="print the resolved vault path and exit")
    parser.add_argument("--contents", action="store_true", help="also search note text for the brand name")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # Windows consoles: a non-ASCII vault filename must not crash the run
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    if not args.brand and not args.vault:
        parser.error("give a brand, or --vault")

    root = repo_root()
    try:
        vault, source = resolve_vault(root)
    except VaultError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.vault:
        print(vault)
        return 0

    print(f"Vault: {vault}  ({source})")
    if not vault.is_dir():
        print(f"ERROR: vault folder {vault} does not exist", file=sys.stderr)
        return 2
    found = find_context(args.brand, root, vault)

    for note in found["notes"]:
        print(f"\nBrand note: {note}  (updated {stamp(note)})")
    if not found["notes"]:
        print(f"\nBrand note: none at Brands/{args.brand}.md")
    for folder in found["folders"]:
        print(f"\nBrand folder: {folder}  (newest first)")
        print("\n".join(list_folder(folder)))
    for folder in found["workspace"]:
        print(f"\nWorkspace: {folder}")
    if found["other"]:
        print("\nOther vault matches:")
        for path in found["other"][:MAX_LISTED]:
            print(f"    {path.relative_to(vault)}")

    if found["tagged"]:
        print(f"\nNotes tagged brand: {args.brand} elsewhere in the vault:")
        for path in found["tagged"][:MAX_LISTED]:
            print(f"    {stamp(path)}  {path.relative_to(vault)}")
        if len(found["tagged"]) > MAX_LISTED:
            print(f"    ... {len(found['tagged']) - MAX_LISTED} more")

    if args.contents:
        found["mentions"] = find_mentions(
            args.brand, vault, found["notes"] + found["folders"] + found["other"] + found["tagged"])
        if found["mentions"]:
            print("\nNotes that mention it:")
            for path in found["mentions"][:MAX_LISTED]:
                print(f"    {path.relative_to(vault)}")

    if not any(found.values()):
        checked = ("Brands/<name>.md, Brands/<name>/, workspace/<name>/, every file and folder name in the vault "
                   "and every note's `brand:` property")
        hint = "" if args.contents else " or rerun with --contents to search note text"
        print(f"\nNOTHING FOUND for '{args.brand}'. Checked: {checked}{' and note text' if args.contents else ''} "
              f"(case and punctuation ignored).\nBefore calling this a new brand, ask the user{hint}.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
