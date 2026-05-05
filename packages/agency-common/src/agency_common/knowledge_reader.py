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

# These directories are excluded from vault indexing.
# Session transcript folders must be here — they are noisy and pollute vector search results.
IGNORED_DIRECTORIES = {
    ".obsidian",
    ".git",
    "Claude_Sessions",
    "Codex_Sessions",
    "Agent_Sessions",
}


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


def iter_brand_yaml_files(vault_path: Path) -> list[Path]:
    """Return YAML brand config files from the vault's Brands/ directory."""
    brands_dir = vault_path / "Brands"
    if not brands_dir.exists():
        return []
    return sorted(brands_dir.glob("*.yaml"))


def _yaml_value_to_str(value: Any) -> str:
    """Flatten a YAML value to a readable string for indexing."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v)
    if isinstance(value, dict):
        return "; ".join(f"{k}: {v}" for k, v in value.items())
    return str(value) if value is not None else ""


def parse_brand_yaml_file(file_path: Path) -> dict[str, Any]:
    """
    Parse a brand YAML config into indexable Markdown text.

    Converts the structured brand profile into prose that the vector index
    can retrieve meaningfully when searching for brand context, voice, or competitors.
    """
    try:
        import yaml
        raw = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except Exception as exc:
        raise KnowledgeReaderError(f"Could not parse brand YAML: {file_path}") from exc

    if not isinstance(data, dict):
        raise KnowledgeReaderError(f"Brand YAML must be a mapping: {file_path}")

    slug = data.get("slug", file_path.stem)
    name = data.get("name", slug)
    lines = [f"# Brand Profile: {name} (slug: {slug})"]

    voice = data.get("voice", {})
    if voice:
        archetype = voice.get("archetype_primary", "")
        archetype_sec = voice.get("archetype_secondary", "")
        arch_str = archetype
        if archetype_sec:
            arch_str += f" / {archetype_sec}"
        lines += ["", "## Voice", f"Archetype: {arch_str}"]
        scale_notes = []
        if voice.get("formal_casual"):
            scale_notes.append(f"formal-casual score {voice['formal_casual']}/10")
        if voice.get("reserved_bold"):
            scale_notes.append(f"reserved-bold score {voice['reserved_bold']}/10")
        if scale_notes:
            lines.append("Voice scales: " + ", ".join(scale_notes))

    vocab = data.get("vocabulary", {})
    if vocab:
        lines += ["", "## Vocabulary"]
        if vocab.get("use_words"):
            lines.append(f"Preferred words: {_yaml_value_to_str(vocab['use_words'])}")
        if vocab.get("avoid_words"):
            lines.append(f"Avoid: {_yaml_value_to_str(vocab['avoid_words'])}")
        if vocab.get("signature_phrases"):
            lines.append(f"Signature phrases: {_yaml_value_to_str(vocab['signature_phrases'])}")

    writing = data.get("writing", {})
    if writing:
        lines += ["", "## Writing Rules"]
        if writing.get("dos"):
            lines.append("Do: " + " / ".join(writing["dos"]))
        if writing.get("donts"):
            lines.append("Don't: " + " / ".join(writing["donts"]))
        if writing.get("banned_constructions"):
            lines.append("Banned: " + " / ".join(writing["banned_constructions"]))
        if writing.get("example_captions"):
            lines += ["", "Example captions (approved voice samples):"]
            for ex in writing["example_captions"]:
                if ex and str(ex).strip():
                    lines.append(f"> {str(ex).strip()[:300]}")

    audience = data.get("audience", {})
    if audience:
        lines += ["", "## Audience"]
        if audience.get("primary"):
            lines.append(f"Primary: {audience['primary']}")
        if audience.get("secondary"):
            lines.append(f"Secondary: {audience['secondary']}")
        if audience.get("pain_points"):
            lines.append(f"Pain points: {_yaml_value_to_str(audience['pain_points'])}")
        if audience.get("desires"):
            lines.append(f"What they want: {_yaml_value_to_str(audience['desires'])}")

    competitors = data.get("competitors", {})
    if competitors:
        lines += ["", "## Competitors"]
        for platform, handles in competitors.items():
            if handles:
                lines.append(f"{platform.capitalize()}: {_yaml_value_to_str(handles)}")

    pillars = data.get("content_pillars", {})
    if pillars:
        lines += ["", "## Content Pillars"]
        pillar_str = ", ".join(f"{k.replace('_', ' ')}: {v}%" for k, v in pillars.items() if v)
        lines.append(pillar_str)

    platforms = data.get("platforms", {})
    if platforms:
        lines += ["", "## Platforms"]
        for platform, cfg in platforms.items():
            if cfg:
                handle = cfg.get("handle", "")
                freq = cfg.get("posting_frequency", "")
                lines.append(f"{platform.capitalize()}: {handle} — {freq}")

    content = "\n".join(lines)
    return {
        "filename": file_path.name,
        "filepath": str(file_path.resolve()),
        "metadata": {"slug": slug, "name": name, "type": "brand-profile"},
        "content": content,
    }


def read_obsidian_vault(
    vault_path: Path | None = None,
    *,
    env_var: str = DEFAULT_VAULT_ENV_VAR,
    strict: bool = False,
) -> list[dict[str, Any]]:
    """
    Read all Markdown notes and brand YAML configs from an Obsidian vault.

    Session transcript directories are excluded — they pollute vector search.
    Brand YAML files are converted to indexable Markdown text so that
    search_second_brain can find brand context, voice, and competitor data.

    When strict is False, unreadable or malformed files are skipped with a warning.
    When strict is True, the first file error raises a KnowledgeReaderError.
    """
    resolved_vault_path = vault_path.expanduser().resolve() if vault_path else get_vault_path(env_var)
    if not resolved_vault_path.exists():
        raise VaultPathError(f"Vault path does not exist: {resolved_vault_path}")
    if not resolved_vault_path.is_dir():
        raise VaultPathError(f"Vault path must be a directory: {resolved_vault_path}")

    notes: list[dict[str, Any]] = []

    # Markdown notes (excluding session transcript directories)
    for file_path in iter_markdown_files(resolved_vault_path):
        try:
            notes.append(parse_markdown_file(file_path))
        except KnowledgeReaderError:
            if strict:
                raise
            LOGGER.warning("Skipping unreadable or malformed Markdown file: %s", file_path, exc_info=True)

    # Brand YAML profiles — converted to indexable text
    for file_path in iter_brand_yaml_files(resolved_vault_path):
        try:
            notes.append(parse_brand_yaml_file(file_path))
            LOGGER.debug("Indexed brand YAML: %s", file_path.name)
        except KnowledgeReaderError:
            if strict:
                raise
            LOGGER.warning("Skipping unreadable brand YAML: %s", file_path, exc_info=True)

    return notes
