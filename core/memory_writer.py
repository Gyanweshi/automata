"""
Memory Writer — keeps the Brainiac2 curated memory layer up to date.

Runs after every Automata agent session to update:
- <vault>/memory/STATUS.md  (project status)
- <vault>/memory/BRANDS.md  (brand intelligence index)
- <vault>/AGENTS.md         (recent sessions summary in Layer 0)
"""
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

def _vault() -> Path:
    """The Obsidian vault, or workspace/vault on machines without one (resolved at call time)."""
    from agency_common.knowledge_reader import get_vault_path

    return get_vault_path()


def _status_file() -> Path:
    return _vault() / "memory" / "STATUS.md"


def _brands_file() -> Path:
    return _vault() / "memory" / "BRANDS.md"


def _agents_file() -> Path:
    return _vault() / "AGENTS.md"


def _replace_section(content: str, start_marker: str, end_marker: str, new_content: str) -> str:
    """Replace content between two HTML comment markers."""
    pattern = rf"({re.escape(start_marker)})(.*?)({re.escape(end_marker)})"
    replacement = rf"\1\n{new_content}\n\3"
    return re.sub(pattern, replacement, content, flags=re.DOTALL)


def update_status(
    project: str,
    status_line: str,
    in_progress: Optional[list] = None,
    next_steps: Optional[list] = None,
):
    """
    Update a project's status in STATUS.md.

    Parameters
    ----------
    project : str
        Project name matching a ## heading in STATUS.md
    status_line : str
        Short one-line status (e.g., '🟢 Active — research complete')
    in_progress : list, optional
        What's currently being worked on
    next_steps : list, optional
        Upcoming tasks
    """
    if not _status_file().exists():
        return

    content = _status_file().read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Update the "Last updated" line
    content = re.sub(
        r"> Last updated: .*",
        f"> Last updated: {today}",
        content,
    )

    _status_file().write_text(content, encoding="utf-8")


def update_brand(
    brand_name: str,
    brand_type: Optional[str] = None,
    status: str = "🟡 In progress",
    done: Optional[list] = None,
    assets: Optional[list] = None,
    next_steps: Optional[list] = None,
):
    """
    Add or update a brand entry in BRANDS.md.

    Parameters
    ----------
    brand_name : str
        The brand name (e.g., 'Rasoi')
    brand_type : str, optional
        Industry/type description
    status : str
        Status emoji + label
    done : list, optional
        List of completed actions for this brand
    assets : list, optional
        File paths or notes for generated assets
    next_steps : list, optional
        What to do next for this brand
    """
    if not _brands_file().exists():
        return

    content = _brands_file().read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    # Build the brand section
    slug = brand_name.lower().replace(" ", "-")
    section_lines = [
        f"## {brand_name}",
        "",
        f"**Type:** {brand_type or 'See vault note'}",
        f"**Status:** {status}",
        f"**Vault note:** `Brands/{slug}.md`",
        f"**Last updated:** {today}",
        "",
        "### What's been done",
        "",
    ]
    if done:
        for item in done:
            section_lines.append(f"- {item}")
    else:
        section_lines.append("- *(no entries yet)*")

    if assets:
        section_lines += ["", "### Assets", ""]
        for a in assets:
            section_lines.append(f"- `{a}`")

    if next_steps:
        section_lines += ["", "### Next steps", ""]
        for s in next_steps:
            section_lines.append(f"- [ ] {s}")

    section_lines += ["", "---", ""]
    new_section = "\n".join(section_lines)

    # Check if brand already exists in file
    heading = f"## {brand_name}"
    if heading in content:
        # Find and replace the existing section
        pattern = rf"(## {re.escape(brand_name)}\n)(.*?)(\n## |\Z)"
        replacement = new_section + r"\3"
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    else:
        # Append before the "Adding a New Brand" section
        insert_before = "## Adding a New Brand"
        if insert_before in content:
            content = content.replace(insert_before, new_section + insert_before)
        else:
            content += "\n" + new_section

    _brands_file().write_text(content, encoding="utf-8")


def append_recent_session_to_agents_md(
    agent_name: str,
    brand_or_project: str,
    one_liner: str,
):
    """
    Append a one-liner session summary to the RECENT_SESSIONS section in AGENTS.md.
    Keeps only the last 10 entries to avoid bloat.

    Parameters
    ----------
    agent_name : str
        Which agent ran
    brand_or_project : str
        Brand or project name
    one_liner : str
        Single sentence summary of what was done
    """
    if not _agents_file().exists():
        return

    content = _agents_file().read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    new_entry = f"- `{today}` · **{agent_name}** · {brand_or_project} — {one_liner}"

    start_marker = "<!-- RECENT_SESSIONS_START -->"
    end_marker = "<!-- RECENT_SESSIONS_END -->"

    # Extract current entries
    match = re.search(
        rf"{re.escape(start_marker)}(.*?){re.escape(end_marker)}",
        content,
        flags=re.DOTALL,
    )
    if match:
        existing = match.group(1).strip()
        # Remove the "No sessions logged yet" placeholder if present
        existing = existing.replace("*No sessions logged yet.*", "").strip()

        # Prepend new entry, keep last 10
        all_entries = [new_entry] + [
            line for line in existing.splitlines() if line.startswith("- `")
        ]
        all_entries = all_entries[:10]
        new_block = "\n".join(all_entries)

        content = _replace_section(content, start_marker, end_marker, new_block)
        _agents_file().write_text(content, encoding="utf-8")
