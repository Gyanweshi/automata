"""Utilities for writing structured outputs as JSON and markdown."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .knowledge_reader import VaultPathError, get_vault_path


_SAFE_PATH_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_WINDOWS_VAULT_FALLBACK = Path(r"D:\Brainiac2")


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
        *,
        overwrite: bool = False,
    ) -> Path:
        """Write markdown content with optional YAML frontmatter without silent replacement."""
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
        try:
            with open(path, "w" if overwrite else "x", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except FileExistsError as exc:
            raise FileExistsError(
                f"Refusing to overwrite existing Markdown note: {path}"
            ) from exc
        return path

    @staticmethod
    def standard_frontmatter(
        agent: str,
        brand: str,
        run_id: str,
        tags: list[str] | None = None,
        *,
        status: str = "draft",
    ) -> dict[str, Any]:
        """Return standard frontmatter for agent output notes."""
        if status not in {"draft", "final"}:
            raise ValueError("status must be 'draft' or 'final'")
        created = datetime.utcnow().strftime("%Y-%m-%d")
        return {
            "type": agent,
            "brand": brand,
            "run_id": run_id,
            "date": created,
            "created": created,
            "status": status,
            "tags": [agent, brand] + (tags or []),
        }

    @staticmethod
    def vault_markdown_directory(
        brand: str,
        artifact_type: str,
        *,
        status: str = "draft",
        vault_path: Path | None = None,
    ) -> Path:
        """Resolve the hybrid-policy vault directory for a brand Markdown artifact."""
        if status not in {"draft", "final"}:
            raise ValueError("status must be 'draft' or 'final'")
        for label, value in (("brand", brand), ("artifact_type", artifact_type)):
            if not _SAFE_PATH_COMPONENT.fullmatch(value):
                raise ValueError(f"Unsafe {label} path component: {value!r}")

        if vault_path is not None:
            root = vault_path.expanduser().resolve()
            if not root.is_dir():
                raise VaultPathError(f"Vault path must be an existing directory: {root}")
        else:
            try:
                root = get_vault_path()
            except VaultPathError:
                if os.name != "nt" or not _WINDOWS_VAULT_FALLBACK.is_dir():
                    raise
                root = _WINDOWS_VAULT_FALLBACK.resolve()

        brand_dir = root / "Brands" / brand
        if status == "draft":
            return brand_dir / "Drafts" / artifact_type
        return brand_dir / artifact_type
