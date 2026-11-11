"""Write JSON Canvas 1.0 files (`.canvas`), the open infinite-canvas format Obsidian opens natively.

Spec: https://jsoncanvas.org (github.com/obsidianmd/jsoncanvas). A canvas is `{"nodes": [...], "edges": [...]}`;
nodes are text, file, link or group cards with integer x/y/width/height, and array order is z-order, so
groups are written first to sit behind the cards they contain.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

# Obsidian's preset canvas colours: "1" red, "2" orange, "3" yellow, "4" green, "5" cyan, "6" purple.
RED, ORANGE, YELLOW, GREEN, CYAN, PURPLE = "1", "2", "3", "4", "5", "6"
SIDES = {"top", "right", "bottom", "left"}

CARD_WIDTH = 420
LINE_HEIGHT = 26
CARD_PADDING = 60
MAX_CARD_HEIGHT = 900


def card_height(text: str, width: int = CARD_WIDTH) -> int:
    """Rough rendered height of a Markdown card: wrapped lines times line height, capped (cards scroll)."""
    chars_per_line = max(20, width // 9)
    lines = sum(max(1, -(-len(line) // chars_per_line)) for line in text.splitlines() or [""])
    return min(MAX_CARD_HEIGHT, CARD_PADDING + lines * LINE_HEIGHT)


class Canvas:
    """Build a canvas in memory, then `write()` it. Ids are deterministic so reruns diff cleanly."""

    def __init__(self, seed: str = "") -> None:
        self._seed = seed
        self._groups: list[dict[str, Any]] = []
        self._cards: list[dict[str, Any]] = []
        self._edges: list[dict[str, Any]] = []
        self._ids: set[str] = set()

    def _id(self, kind: str) -> str:
        counter = len(self._ids)
        while True:
            digest = hashlib.sha1(f"{self._seed}|{kind}|{counter}".encode()).hexdigest()[:16]
            if digest not in self._ids:
                self._ids.add(digest)
                return digest
            counter += 1

    @staticmethod
    def _box(x: float, y: float, width: float, height: float) -> dict[str, int]:
        if width <= 0 or height <= 0:
            raise ValueError("canvas nodes need a positive width and height")
        return {"x": int(x), "y": int(y), "width": int(width), "height": int(height)}

    def _node(self, kind: str, box: dict[str, int], color: str | None, **fields: Any) -> dict[str, Any]:
        node = {"id": self._id(kind), "type": kind, **box, **{k: v for k, v in fields.items() if v is not None}}
        if color:
            node["color"] = color
        return node

    def text(self, text: str, x: float, y: float, width: float = CARD_WIDTH,
             height: float | None = None, color: str | None = None) -> str:
        """A Markdown card. Height defaults to an estimate from the text."""
        node = self._node("text", self._box(x, y, width, height or card_height(text, int(width))), color, text=text)
        self._cards.append(node)
        return node["id"]

    def file(self, path: str, x: float, y: float, width: float = CARD_WIDTH, height: float = 400,
             color: str | None = None, subpath: str | None = None) -> str:
        """An embedded vault file; `path` is relative to the vault root, with forward slashes."""
        node = self._node("file", self._box(x, y, width, height), color,
                          file=path.replace("\\", "/"), subpath=subpath)
        self._cards.append(node)
        return node["id"]

    def link(self, url: str, x: float, y: float, width: float = CARD_WIDTH, height: float = 300,
             color: str | None = None) -> str:
        node = self._node("link", self._box(x, y, width, height), color, url=url)
        self._cards.append(node)
        return node["id"]

    def group(self, label: str, x: float, y: float, width: float, height: float,
              color: str | None = None) -> str:
        node = self._node("group", self._box(x, y, width, height), color, label=label or None)
        self._groups.append(node)
        return node["id"]

    def edge(self, from_node: str, to_node: str, *, from_side: str | None = None, to_side: str | None = None,
             label: str | None = None, color: str | None = None, arrow: bool = True) -> str:
        known = {n["id"] for n in self._groups + self._cards}
        if from_node not in known or to_node not in known:
            raise ValueError("edges must connect existing nodes")
        for side in (from_side, to_side):
            if side is not None and side not in SIDES:
                raise ValueError(f"unknown side {side!r}")
        edge: dict[str, Any] = {"id": self._id("edge"), "fromNode": from_node, "toNode": to_node}
        if from_side:
            edge["fromSide"] = from_side
        if to_side:
            edge["toSide"] = to_side
        if not arrow:
            edge["toEnd"] = "none"
        if label:
            edge["label"] = label
        if color:
            edge["color"] = color
        self._edges.append(edge)
        return edge["id"]

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {"nodes": [*self._groups, *self._cards], "edges": list(self._edges)}

    def write(self, path: Path, *, overwrite: bool = False) -> Path:
        """Write the canvas as tab-indented JSON (what Obsidian writes); refuses to replace a file by default."""
        if path.suffix != ".canvas":
            raise ValueError("canvas files must end in .canvas")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w" if overwrite else "x", encoding="utf-8") as handle:
                json.dump(self.to_dict(), handle, indent="\t", ensure_ascii=False)
        except FileExistsError as exc:
            raise FileExistsError(f"Refusing to overwrite existing canvas: {path}") from exc
        return path


def vault_relative(path: Path) -> str:
    """`path` relative to the vault holding it, for file nodes.

    The vault root is the nearest ancestor holding `.obsidian`; without one (workspace/vault on machines
    with no Obsidian) it is the parent of the nearest `Brands` folder. Falls back to the file name.
    """
    resolved = path.resolve()
    for ancestor in resolved.parents:
        if (ancestor / ".obsidian").is_dir():
            return resolved.relative_to(ancestor).as_posix()
    for ancestor in resolved.parents:
        if ancestor.name == "Brands":
            return resolved.relative_to(ancestor.parent).as_posix()
    return resolved.name


def section_grid(canvas: Canvas, sections: list[tuple[str, list[str]]], *, x: float, y: float,
                 columns: int = 3, gap: int = 80, color: str | None = None) -> list[str]:
    """Lay out labelled groups of Markdown cards in a grid; returns the group ids in order.

    Each section is (label, [card markdown, ...]); its cards stack vertically inside its group.
    """
    pad, header = 30, 50
    group_width = CARD_WIDTH + 2 * pad
    ids: list[str] = []
    row_top, row_height = y, 0
    for index, (label, cards) in enumerate(sections):
        column = index % columns
        if column == 0 and index:
            row_top += row_height + gap
            row_height = 0
        heights = [card_height(card) for card in cards]
        height = header + sum(heights) + pad * (len(cards) + 1)
        left = x + column * (group_width + gap)
        ids.append(canvas.group(label, left, row_top, group_width, height, color=color))
        top = row_top + header + pad
        for card, card_h in zip(cards, heights):
            canvas.text(card, left + pad, top, CARD_WIDTH, card_h)
            top += card_h + pad
        row_height = max(row_height, height)
    return ids


MAX_SECTION_CHARS = 1200


def markdown_sections(markdown: str) -> tuple[str, list[tuple[str, str]]]:
    """Split a note body into (intro, [(H2 heading, section text), ...]); H3+ stay inside their section."""
    intro: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    in_code = False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        if not in_code and line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
        else:
            intro.append(line)
    return "\n".join(intro).strip(), [(title, "\n".join(body).strip()) for title, body in sections]


def _clip(text: str, limit: int = MAX_SECTION_CHARS) -> str:
    if len(text) <= limit:
        return text
    cut = text.rfind("\n", 0, limit)
    return text[: cut if cut > limit // 2 else limit].rstrip() + "\n\n*… continues in the note*"


def markdown_canvas(md_path: Path, markdown: str, *, title: str = "", seed: str = "") -> Canvas:
    """A board for any note: intro and the note itself on top, one group per `##` section below."""
    board = Canvas(seed=seed or md_path.as_posix())
    intro, sections = markdown_sections(markdown)
    headline = title or next((line[2:].strip() for line in intro.splitlines() if line.startswith("# ")), md_path.stem)
    intro_text = "\n".join(line for line in intro.splitlines() if not line.startswith("# ")).strip()
    summary = f"# {headline}" + (f"\n\n{_clip(intro_text, 600)}" if intro_text else "")
    board.text(summary, 0, 0, CARD_WIDTH, color=PURPLE)
    board.file(vault_relative(md_path), CARD_WIDTH + 80, 0, CARD_WIDTH, 400)
    top = max(card_height(summary), 400) + 140
    grid = [(heading, [_clip(body) or "*(empty section)*"]) for heading, body in sections]
    if grid:
        section_grid(board, grid, x=0, y=top, columns=3, color=CYAN)
    return board
