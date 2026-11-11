"""Save in-session work to the vault the way the agent pipelines do, so their features apply to it too.

Research, storyboards and copy are often produced inside a Claude Code or Codex session rather than through
`make research` and friends. This command gives that work the same treatment: the right vault folder
(`Brands/<Folder>/Drafts/<Type>/`, or `Research/<Topic>/` for non-brand research), standard frontmatter with
`brand:` and `status: draft`, and a `.canvas` board beside the note.

    agency-note save --brand maple --type Research --title "BBD stress test" --body draft.md
    agency-note save --topic Instagram_Micro_Dramas --type Research --title "Hooks" --body - < draft.md
    agency-note canvas "Brands/Maple/Drafts/Research/2026-11-11-bbd-stress-test.md"

Notes are always drafts; finalising stays an explicit, approval-gated step (see AGENTS.md).
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import frontmatter

from .canvas import markdown_canvas
from .knowledge_reader import get_vault_path
from .output_writer import OutputWriter, _SAFE_PATH_COMPONENT


class NoteError(ValueError):
    pass


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:80].rstrip("-") or "note"


def note_directory(vault: Path, *, artifact_type: str, brand: str | None, topic: str | None) -> Path:
    if bool(brand) == bool(topic):
        raise NoteError("give exactly one of --brand (client work) or --topic (non-brand research)")
    if brand:
        return OutputWriter.vault_markdown_directory(brand, artifact_type, status="draft", vault_path=vault)
    if not _SAFE_PATH_COMPONENT.fullmatch(topic or ""):
        raise NoteError(f"--topic must be a single folder name like Instagram_Micro_Dramas, got {topic!r}")
    return vault / "Research" / topic


def save_note(body: str, *, title: str, artifact_type: str, brand: str | None = None, topic: str | None = None,
              tags: list[str] | None = None, canvas: bool = True, vault: Path | None = None,
              today: date | None = None) -> tuple[Path, Path | None]:
    """Write a draft note (and its board) and return (note path, canvas path or None). Never overwrites."""
    vault = (vault or get_vault_path()).resolve()
    if not _SAFE_PATH_COMPONENT.fullmatch(artifact_type):
        raise NoteError(f"--type must be a single folder name like Research or Storyboards, got {artifact_type!r}")
    folder = note_directory(vault, artifact_type=artifact_type, brand=brand, topic=topic)

    parsed = frontmatter.loads(body)
    day = (today or date.today()).isoformat()
    kind = artifact_type.lower().rstrip("s") if artifact_type.lower() != "research" else "research"
    meta: dict[str, Any] = {"title": title, "type": kind}
    meta.update({k: v for k, v in parsed.metadata.items() if k not in {"status", "brand"}})
    if brand:
        meta["brand"] = brand
    meta["status"] = "draft"
    meta.setdefault("created", day)
    tag_list = [str(t) for t in (meta.get("tags") or [])] + [kind] + ([brand] if brand else []) + list(tags or [])
    meta["tags"] = list(dict.fromkeys(t for t in tag_list if t))

    content = parsed.content.strip()
    if not content.lstrip().startswith("# "):
        content = f"# {title}\n\n{content}"
    path = folder / f"{day}-{slugify(title)}.md"
    folder.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8") as handle:
            handle.write(frontmatter.dumps(frontmatter.Post(content, **meta), sort_keys=False) + "\n")
    except FileExistsError as exc:
        raise NoteError(f"{path} already exists; pick another --title or edit that note") from exc

    board = None
    if canvas:
        board = markdown_canvas(path, content, title=title).write(path.with_suffix(".canvas"))
    return path, board


def canvas_for(note: Path, *, overwrite: bool = False) -> Path:
    """Build (or with overwrite, rebuild) the board beside an existing note."""
    if not note.is_file():
        vault_note = get_vault_path() / note
        if not vault_note.is_file():
            raise NoteError(f"note not found: {note}")
        note = vault_note
    post = frontmatter.loads(note.read_text(encoding="utf-8"))
    board = markdown_canvas(note, post.content, title=str(post.metadata.get("title") or ""))
    return board.write(note.with_suffix(".canvas"), overwrite=overwrite)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agency-note", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    save = sub.add_parser("save", help="save a draft note (and its canvas board) to the vault")
    save.add_argument("--title", required=True)
    save.add_argument("--type", dest="artifact_type", default="Research",
                      help="drafts subfolder: Research, Storyboards, Content, Ideation, ... (default Research)")
    where = save.add_mutually_exclusive_group(required=True)
    where.add_argument("--brand", help="brand slug, e.g. maple (writes Brands/<Folder>/Drafts/<Type>/)")
    where.add_argument("--topic", help="non-brand research folder (writes Research/<Topic>/)")
    save.add_argument("--body", required=True, help="Markdown file with the note body, or - for stdin")
    save.add_argument("--tags", default="", help="extra comma-separated tags")
    save.add_argument("--no-canvas", action="store_true", help="skip the .canvas board")
    board = sub.add_parser("canvas", help="make a .canvas board for an existing note")
    board.add_argument("note", type=Path, help="note path, absolute or relative to the vault")
    board.add_argument("--overwrite", action="store_true", help="replace an existing board")
    args = parser.parse_args(argv)

    try:
        if args.command == "canvas":
            print(f"Canvas board: {canvas_for(args.note, overwrite=args.overwrite)}")
            return 0
        body = sys.stdin.read() if args.body == "-" else Path(args.body).read_text(encoding="utf-8")
        if args.brand:
            from .brand_loader import list_brands
            if args.brand not in list_brands():
                print(f"warning: no brand note Brands/{args.brand}.md; check the slug (make brand-context)",
                      file=sys.stderr)
        note, canvas = save_note(body, title=args.title, artifact_type=args.artifact_type, brand=args.brand,
                                 topic=args.topic, tags=[t.strip() for t in args.tags.split(",") if t.strip()],
                                 canvas=not args.no_canvas)
    except (NoteError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Note: {note}")
    if canvas:
        print(f"Canvas board: {canvas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
