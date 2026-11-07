---
description: Log this session to the vault now (Obsidian, or workspace/vault on machines without one)
allowed-tools: Bash(*)
---

Run this command to log the current session to the Obsidian vault, then report the resulting file path in one sentence (or say nothing was written if the script produced no output):

!`p=.venv/Scripts/python.exe; [ -x "$p" ] || p=.venv/bin/python; "$p" scripts/log_session_to_vault.py --latest --commit-vault --commit-reason "Explicit /sess command"`
