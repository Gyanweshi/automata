---
name: agency-handoff
description: Package, extract, and execute seamless agent-to-agent session handoffs and continuation briefs between Codex, Claude Code, and Antigravity across any task or repository.
---

# Universal Agency Handoff Skill

Seamlessly transfer active task context, coding decisions, research findings, user steering, and file state between AI coding agents (**Codex CLI**, **Claude Code**, and **Antigravity**) for **any task, session, or project** without losing context or making the user repeat themselves.

## Why This Skill Exists

Different coding agents excel at different aspects of a project:
- **Codex CLI**: Rapid web research, browser automation (`browser-act`), quick script exploration.
- **Claude Code**: High-nuance copywriting, system architecture, deep reasoning, long multi-file refactors.
- **Antigravity**: IDE-integrated pair programming, visual diff review, test execution, full workspace awareness.

When a session reaches a milestone, reaches context compaction limits, or benefits from switching agents, **agency-handoff** packages the full state into a standardized, self-contained continuation brief.

---

## Capabilities

1. **Universal Multi-Agent Parsing**:
   - Parses **Codex CLI** sessions (`~/.codex/sessions/`)
   - Parses **Claude Code** sessions (`~/.claude/projects/`)
   - Parses **Antigravity** IDE trajectories (`transcript.jsonl`)
2. **Session Discovery**:
   - List recent sessions across both tools with `--list`.
   - Auto-detects the most recently active session across all tools.
3. **Lossless State Handoff**:
   - Captures the full trajectory of user prompts (how the problem evolved).
   - Captures the exact **latest user feedback / steering** (the immediate pivot point).
   - Captures what the prior agent already delivered (to avoid redundant re-generation).
   - Identifies all workspace files touched or referenced.

---

## Usage

### 1. Listing Available Sessions
To see recent sessions from both Codex and Claude Code:
```powershell
.\.venv\Scripts\python.exe scripts/agency-handoff.py --list
```

### 2. Auto Handoff (Latest Session to the Other Agent)
Automatically detect whichever agent was active last, and create a continuation brief for the other agent:
```powershell
.\.venv\Scripts\python.exe scripts/agency-handoff.py
```

### 3. Explicit Handoff Direction
* **From Codex to Claude Code**:
  ```powershell
  .\.venv\Scripts\python.exe scripts/agency-handoff.py --source codex --target claude
  ```
* **From Claude Code to Codex**:
  ```powershell
  .\.venv\Scripts\python.exe scripts/agency-handoff.py --source claude --target codex
  ```
* **With Specific Steering or Custom Output**:
  ```powershell
  .\.venv\Scripts\python.exe scripts/agency-handoff.py --steering "Now refactor the tests to use pytest" --output CLAUDE_HANDOFF.md
  ```
* **By Session ID or Log File**:
  ```powershell
  .\.venv\Scripts\python.exe scripts/agency-handoff.py --session <session-id-or-path> --target claude
  ```

---

## Standard Handoff Architecture (`<TARGET>_HANDOFF_<TOPIC>.md`)

Every generated handoff produces an authoritative document containing:

1. **Immediate Directive**:
   - Target Agent, Source Agent, Topic/Thread, Session ID.
   - User's **Active Steering** quote.
   - Clear rule: *"Do NOT ask the user to re-explain anything or restart from scratch."*
2. **Conversational Evolution**:
   - Numbered chronological summary of user prompts so the target agent understands the design rationale and discarded options.
3. **Latest Prior State**:
   - Summary and code/copy produced in the prior turn so the target agent builds on top of it.
4. **Working Files Touched**:
   - Explicit list of files modified or inspected.
5. **Terminal One-Liner**:
   - The exact prompt to paste into the receiving agent's terminal (e.g., `Read CLAUDE_HANDOFF.md and continue from there`).

---

## Target Agent Rules of Engagement

When you (as Claude Code, Codex, or Antigravity) are instructed to **read a handoff brief**:
1. **Never ask introductory questions**: You already have the user's intent and context.
2. **Preserve locked decisions**: Do not re-open previously settled debates unless the active steering explicitly says to.
3. **Execute immediately**: Directly deliver the code, script, or content requested in the *Active User Steering* section.
