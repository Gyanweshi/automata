"""
Unified Session Logger — writes rich Markdown session logs to C:\\Brainiac2\\Agent_Sessions\\

Each log is a structured Markdown file readable in Obsidian and by any AI tool
that reads the Brainiac2 vault at session start.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Where this code lives
WORKSPACE_ROOT = Path(__file__).parent.parent

# Brainiac2 vault — shared memory across all AI tools
BRAINIAC2_ROOT = Path("C:/Brainiac2")
AGENT_SESSIONS_DIR = BRAINIAC2_ROOT / "Agent_Sessions"

# Fallback: also write a lightweight JSON log locally
LOCAL_LOGS_DIR = WORKSPACE_ROOT / "data" / "logs"


def log_agent_session(
    agent_name: str,
    session_data: dict,
    brand: Optional[str] = None,
    project: Optional[str] = None,
    actions: Optional[list] = None,
    outputs: Optional[list] = None,
    decisions: Optional[list] = None,
    current_state: Optional[str] = None,
    next_steps: Optional[list] = None,
) -> Path:
    """
    Log an agent session as a rich Markdown file in C:\\Brainiac2\\Agent_Sessions\\

    Parameters
    ----------
    agent_name : str
        Name of the agent (e.g., 'automata', 'openedswarm', 'deep_research')
    session_data : dict
        Raw session metadata (always saved to local JSON log as well)
    brand : str, optional
        Brand name this session was for (e.g., 'Rasoi', 'Altara')
    project : str, optional
        Project name if not brand-specific (e.g., 'automata-refactor')
    actions : list, optional
        List of completed actions (strings)
    outputs : list, optional
        List of output file paths or URLs produced
    decisions : list, optional
        Key decisions made during this session
    current_state : str, optional
        Where the project stands right now
    next_steps : list, optional
        What should be done next session

    Returns
    -------
    Path
        Path to the created Markdown log file
    """
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H:%M")

    # Build a slug for the filename
    topic = brand or project or agent_name
    topic_slug = topic.lower().replace(" ", "-").replace("/", "-")
    filename = f"{date_str}_{topic_slug}.md"

    # Ensure session dirs exist
    AGENT_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # --- Build Markdown content ---
    tags = ["automata", agent_name.replace("_", "-")]
    if brand:
        tags.append(brand.lower().replace(" ", "-"))

    md_lines = [
        "---",
        f"date: {date_str}",
        f"time: {time_str}",
        f"tool: Automata / {agent_name}",
        f"project: {brand or project or agent_name}",
        f"tags: [{', '.join(tags)}]",
        "---",
        "",
        f"# {date_str} — {agent_name.replace('_', ' ').title()}"
        + (f" · {brand}" if brand else ""),
        "",
    ]

    # What was done
    md_lines += ["## What Was Done", ""]
    if actions:
        for a in actions:
            md_lines.append(f"- {a}")
    else:
        for k, v in session_data.items():
            if k not in ("agent", "status"):
                md_lines.append(f"- `{k}`: {v}")
    md_lines.append("")

    # What was produced
    if outputs:
        md_lines += ["## What Was Produced", ""]
        for o in outputs:
            md_lines.append(f"- `{o}`")
        md_lines.append("")

    # Key decisions
    if decisions:
        md_lines += ["## Key Decisions", ""]
        for d in decisions:
            md_lines.append(f"- {d}")
        md_lines.append("")

    # Current state
    if current_state:
        md_lines += ["## Current State", "", current_state, ""]

    # Next steps
    if next_steps:
        md_lines += ["## Next Steps", ""]
        for s in next_steps:
            md_lines.append(f"- [ ] {s}")
        md_lines.append("")

    # Status footer
    status = session_data.get("status", "completed")
    md_lines += [
        "---",
        f"*Session status: `{status}` · Logged by Automata at {time_str}*",
    ]

    markdown_content = "\n".join(md_lines)

    # Write Markdown log to Brainiac2
    md_path = AGENT_SESSIONS_DIR / filename

    # If file already exists (same brand, same day), append with a separator
    if md_path.exists():
        with open(md_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n\n## Session at {time_str}\n\n")
            # Write just the body (skip frontmatter on append)
            body_start = markdown_content.find("# ")
            f.write(markdown_content[body_start:])
    else:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    # Also write lightweight JSON log locally (for debugging)
    json_path = LOCAL_LOGS_DIR / f"{agent_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {**session_data, "md_log": str(md_path), "timestamp": timestamp.isoformat()},
            f,
            indent=2,
        )

    return md_path
