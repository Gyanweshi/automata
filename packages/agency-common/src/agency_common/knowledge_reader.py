"""Read Markdown notes from a local Obsidian vault."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import frontmatter
from dotenv import find_dotenv, load_dotenv

LOGGER = logging.getLogger(__name__)
DEFAULT_VAULT_ENV_VAR = "OBSIDIAN_VAULT_PATH"
IGNORED_DIRECTORIES = {".obsidian", ".git"}


class KnowledgeReaderError(RuntimeError):
    """Base error raised by the knowledge reader."""


class VaultPathError(KnowledgeReaderError):
    """Raised when the configured vault path is missing or invalid."""


def get_vault_path(env_var: str = DEFAULT_VAULT_ENV_VAR) -> Path:
    """Return the absolute vault path from the configured environment variable."""
    load_dotenv(find_dotenv(usecwd=True))
    raw_path = os.environ.get(env_var)
    if not raw_path:
        raise VaultPathError(
            f"{env_var} is not set. Set it to the absolute path of your Obsidian vault."
        )

    vault_path = Path(raw_path).expanduser().resolve()
    if not vault_path.exists():
        raise VaultPathError(f"{env_var} points to a path that does not exist: {vault_path}")
    if not vault_path.is_dir():
        raise VaultPathError(f"{env_var} must point to a directory: {vault_path}")

    return vault_path


def iter_markdown_files(vault_path: Path) -> list[Path]:
    """Return Markdown files under the vault, skipping Obsidian and Git internals."""
    markdown_files: list[Path] = []

    for root, dirnames, filenames in os.walk(vault_path):
        # Mutating dirnames in place prevents os.walk from descending into ignored trees.
        dirnames[:] = [name for name in dirnames if name not in IGNORED_DIRECTORIES]
        root_path = Path(root)

        for filename in filenames:
            file_path = root_path / filename
            if file_path.suffix.lower() == ".md":
                markdown_files.append(file_path)

    return sorted(markdown_files)


def parse_markdown_file(file_path: Path) -> dict[str, Any]:
    """Parse a Markdown file into filename, absolute path, metadata, and content."""
    try:
        raw_content = file_path.read_text(encoding="utf-8")
        # python-frontmatter handles empty metadata, YAML frontmatter, and plain Markdown.
        parsed = frontmatter.loads(raw_content)
    except UnicodeDecodeError as exc:
        raise KnowledgeReaderError(f"File is not valid UTF-8 text: {file_path}") from exc
    except OSError as exc:
        raise KnowledgeReaderError(f"Could not read Markdown file: {file_path}") from exc
    except Exception as exc:
        raise KnowledgeReaderError(f"Could not parse frontmatter in Markdown file: {file_path}") from exc

    return {
        "filename": file_path.name,
        "filepath": str(file_path.resolve()),
        "metadata": dict(parsed.metadata),
        "content": parsed.content,
    }


def read_obsidian_vault(
    vault_path: Path | None = None,
    *,
    env_var: str = DEFAULT_VAULT_ENV_VAR,
    strict: bool = False,
) -> list[dict[str, Any]]:
    """
    Read all Markdown notes from an Obsidian vault.

    When strict is False, unreadable or malformed files are skipped with a warning.
    When strict is True, the first file error raises a KnowledgeReaderError.
    """
    resolved_vault_path = vault_path.expanduser().resolve() if vault_path else get_vault_path(env_var)
    if not resolved_vault_path.exists():
        raise VaultPathError(f"Vault path does not exist: {resolved_vault_path}")
    if not resolved_vault_path.is_dir():
        raise VaultPathError(f"Vault path must be a directory: {resolved_vault_path}")

    notes: list[dict[str, Any]] = []
    for file_path in iter_markdown_files(resolved_vault_path):
        try:
            notes.append(parse_markdown_file(file_path))
        except KnowledgeReaderError:
            if strict:
                raise
            LOGGER.warning("Skipping unreadable or malformed Markdown file: %s", file_path, exc_info=True)

    return notes
