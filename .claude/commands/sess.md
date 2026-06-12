---
description: Log this session to the Obsidian vault now
allowed-tools: Bash(*)
---

Run this command to log the current session to the Obsidian vault, then report the resulting file path in one sentence (or say nothing was written if the script produced no output):

!`SESSION_ID=$(basename "$(ls -t ~/.claude/projects/C--automata/*.jsonl | head -1)" .jsonl); echo "{\"session_id\": \"$SESSION_ID\"}" | .venv/Scripts/python.exe agents/automata_core/scripts/log_session_to_vault.py`
