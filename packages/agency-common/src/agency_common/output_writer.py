"""Utilities for writing structured outputs as JSON and markdown."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class OutputWriter:
    """Write agent outputs to files in various formats."""

    @staticmethod
    def write_json(data: BaseModel | dict, path: Path) -> Path:
        """Write a Pydantic model or dict as JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = data.model_dump() if isinstance(data, BaseModel) else data
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        return path

    @staticmethod
    def write_markdown(
        content: str,
        path: Path,
        frontmatter: dict[str, Any] | None = None,
    ) -> Path:
        """Write markdown content with optional YAML frontmatter."""
        path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        if frontmatter:
            lines.append("---")
            for k, v in frontmatter.items():
                if isinstance(v, list):
                    lines.append(f"{k}:")
                    for item in v:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"{k}: {v!r}" if isinstance(v, str) else f"{k}: {v}")
            lines.append("---")
            lines.append("")
        lines.append(content)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path

    @staticmethod
    def standard_frontmatter(
        agent: str,
        brand: str,
        run_id: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return standard frontmatter for agent output notes."""
        return {
            "type": agent,
            "brand": brand,
            "run_id": run_id,
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "status": "draft",
            "tags": [agent, brand] + (tags or []),
        }
