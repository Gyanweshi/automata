#!/usr/bin/env python3
"""Universal Agency Handoff CLI & Engine.

Enables seamless cross-agent continuation between Codex CLI, Claude Code,
and Antigravity for ANY session, project, topic, or repository.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def get_user_home() -> Path:
    return Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "~").expanduser()


# ==============================================================================
# Codex Session Discovery & Parsing
# ==============================================================================

def list_codex_sessions(limit: int = 10) -> list[dict]:
    """List recent Codex sessions with metadata and titles."""
    home = get_user_home()
    sessions_root = home / ".codex" / "sessions"
    session_index = home / ".codex" / "session_index.jsonl"
    
    titles_by_id = {}
    if session_index.exists():
        try:
            with open(session_index, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        d = json.loads(line)
                        if d.get("id"):
                            titles_by_id[d["id"]] = d.get("thread_name", "Untitled")
        except Exception:
            pass

    if not sessions_root.exists():
        return []

    files = list(sessions_root.glob("**/*.jsonl"))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    results = []
    for f in files[:limit]:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        match = re.search(r"([0-9a-fA-F-]{36})\.jsonl$", f.name)
        sid = match.group(1) if match else f.stem
        title = titles_by_id.get(sid, sid)
        results.append({
            "source": "codex",
            "session_id": sid,
            "title": title,
            "file_path": str(f),
            "updated_at": mtime.strftime("%Y-%m-%d %H:%M:%S"),
            "size_bytes": f.stat().st_size
        })
    return results


def parse_codex_session(session_path: Path) -> dict:
    """Parse Codex JSONL rollout into structured turns, metadata, and files touched."""
    turns = []
    current_turn = None
    meta = {}
    files_touched = set()

    with open(session_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue

            t = data.get("type")
            payload = data.get("payload", {})
            ts = data.get("timestamp")

            if t == "session_meta":
                meta = payload
            elif t == "response_item":
                pt = payload.get("type")
                role = payload.get("role")

                if pt == "message" and role == "user":
                    content_list = payload.get("content", [])
                    text_parts = []
                    for c in content_list:
                        if isinstance(c, dict):
                            text_parts.append(c.get("text", ""))
                        elif isinstance(c, str):
                            text_parts.append(c)
                    full_text = "\n".join(text_parts).strip()

                    is_sys = (
                        full_text.startswith("# AGENTS.md")
                        or full_text.startswith("<INSTRUCTIONS>")
                        or full_text.startswith("<environment_context>")
                    )

                    if current_turn is not None and not current_turn["is_system_inject"]:
                        turns.append(current_turn)

                    current_turn = {
                        "user_text": full_text,
                        "is_system_inject": is_sys,
                        "timestamp": ts,
                        "tools": [],
                        "assistant_text": []
                    }

                elif pt == "message" and role == "assistant":
                    content_list = payload.get("content", [])
                    text_parts = []
                    for c in content_list:
                        if isinstance(c, dict):
                            text_parts.append(c.get("text", ""))
                        elif isinstance(c, str):
                            text_parts.append(c)
                    resp_text = "\n".join(text_parts).strip()
                    if current_turn:
                        current_turn["assistant_text"].append({
                            "timestamp": ts,
                            "text": resp_text
                        })

                elif pt in ("custom_tool_call", "function_call"):
                    tool_name = payload.get("name") or payload.get("function", {}).get("name")
                    tool_input = payload.get("input") or payload.get("arguments") or payload.get("call")
                    inp_str = str(tool_input)
                    for match in re.findall(r"['\"]([a-zA-Z0-9_\-\\/.]+\.[a-zA-Z0-9]+)['\"]", inp_str):
                        if not match.startswith("http") and len(match) < 120:
                            files_touched.add(match)

                    if current_turn:
                        current_turn["tools"].append({
                            "name": tool_name,
                            "input": tool_input,
                            "timestamp": ts
                        })

    if current_turn is not None and not current_turn["is_system_inject"]:
        turns.append(current_turn)

    title = meta.get("thread_name") or ""
    if not title and turns:
        title = turns[0]["user_text"].split("\n")[0][:60]

    return {
        "source": "codex",
        "session_id": meta.get("session_id") or meta.get("id") or session_path.stem,
        "title": title or "Codex Session",
        "meta": meta,
        "turns": turns,
        "files_touched": sorted(list(files_touched)),
        "file_path": str(session_path)
    }


# ==============================================================================
# Claude Code Session Discovery & Parsing
# ==============================================================================

def list_claude_sessions(limit: int = 10) -> list[dict]:
    """List recent Claude Code sessions for the current project."""
    home = get_user_home()
    projects_root = home / ".claude" / "projects"
    if not projects_root.exists():
        return []

    matching_dirs = [d for d in projects_root.iterdir() if d.is_dir()]
    jsonls = []
    for d in matching_dirs:
        jsonls.extend(list(d.glob("*.jsonl")))

    jsonls.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    results = []
    for f in jsonls[:limit]:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        sid = f.stem
        title = sid
        try:
            with open(f, "r", encoding="utf-8") as sfile:
                for line in sfile:
                    d = json.loads(line)
                    if d.get("type") == "user":
                        msg = d.get("message", {})
                        content = msg.get("content") or msg
                        candidate = ""
                        if isinstance(content, str):
                            candidate = content
                        elif isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("text"):
                                    candidate = item["text"]
                                    break
                        candidate = candidate.strip()
                        # Filter out skill injections from title
                        if candidate and not candidate.startswith("Base directory") and not candidate.startswith("Launching skill:"):
                            title = candidate.split("\n")[0][:60]
                            break
        except Exception:
            pass

        results.append({
            "source": "claude",
            "session_id": sid,
            "title": title,
            "file_path": str(f),
            "updated_at": mtime.strftime("%Y-%m-%d %H:%M:%S"),
            "size_bytes": f.stat().st_size
        })
    return results


def parse_claude_session(session_path: Path) -> dict:
    """Parse Claude Code JSONL file into structured turns, metadata, and files touched."""
    turns = []
    current_turn = None
    files_touched = set()
    sid = session_path.stem
    git_branch = ""

    with open(session_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue

            t = d.get("type")
            ts = d.get("timestamp")
            if d.get("gitBranch"):
                git_branch = d.get("gitBranch")
            if d.get("sessionId"):
                sid = d.get("sessionId")

            if t == "user":
                msg = d.get("message", {})
                content = msg.get("content") or msg
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                parts.append(item.get("text", ""))
                            elif item.get("type") == "tool_result":
                                res = str(item.get("content", ""))
                                for match in re.findall(r"([a-zA-Z0-9_\-\\/.]+\.[a-zA-Z0-9]+)", res):
                                    if len(match) < 120 and ("/" in match or "\\" in match):
                                        files_touched.add(match)
                        elif isinstance(item, str):
                            parts.append(item)
                    text = "\n".join(parts)

                clean_text = text.strip()
                # Ignore system callbacks and skill framework preambles as standalone user turns
                is_skill_preamble = (
                    clean_text.startswith("Base directory for this skill:")
                    or clean_text.startswith("Launching skill:")
                    or (isinstance(content, list) and all(isinstance(x, dict) and x.get("type") == "tool_result" for x in content))
                )
                if is_skill_preamble or not clean_text:
                    continue

                if current_turn is not None:
                    turns.append(current_turn)

                current_turn = {
                    "user_text": clean_text,
                    "is_system_inject": False,
                    "timestamp": ts,
                    "tools": [],
                    "assistant_text": []
                }

            elif t == "assistant":
                msg = d.get("message", {})
                content = msg.get("content") or msg
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                parts.append(item.get("text", ""))
                            elif item.get("type") == "tool_use":
                                tname = item.get("name")
                                tinp = item.get("input", {})
                                inp_str = str(tinp)
                                for match in re.findall(r"['\"]([a-zA-Z0-9_\-\\/.]+\.[a-zA-Z0-9]+)['\"]", inp_str):
                                    files_touched.add(match)
                                if current_turn:
                                    current_turn["tools"].append({"name": tname, "input": tinp, "timestamp": ts})
                    text = "\n".join(parts)

                if current_turn and text.strip():
                    current_turn["assistant_text"].append({"timestamp": ts, "text": text.strip()})

    if current_turn is not None:
        turns.append(current_turn)

    title = turns[0]["user_text"].split("\n")[0][:60] if turns else sid

    return {
        "source": "claude",
        "session_id": sid,
        "title": title,
        "meta": {"sessionId": sid, "gitBranch": git_branch},
        "turns": turns,
        "files_touched": sorted(list(files_touched)),
        "file_path": str(session_path)
    }


# ==============================================================================
# Universal Handoff Brief Assembler
# ==============================================================================

def assemble_universal_brief(
    source_agent: str,
    target_agent: str,
    parsed_session: dict,
    custom_steering: str = "",
    brand_slug: str = "",
    extra_notes: str = ""
) -> str:
    """Generate an authoritative, universal markdown continuation brief for any session."""
    meta = parsed_session.get("meta", {})
    sid = parsed_session.get("session_id", "unknown")
    title = parsed_session.get("title", "Active Task")
    turns = parsed_session.get("turns", [])
    files_touched = parsed_session.get("files_touched", [])

    user_prompts = [t["user_text"] for t in turns if not t.get("is_system_inject") and t.get("user_text")]
    last_user_prompt = custom_steering or (user_prompts[-1] if user_prompts else "Continue ongoing task.")

    last_turn = turns[-1] if turns else None
    last_assistant_msgs = last_turn.get("assistant_text", []) if last_turn else []
    last_assistant_text = "\n\n".join([m["text"] for m in last_assistant_msgs if m.get("text")])

    lines = []
    lines.append(f"# Cross-Agent Continuation & Handoff Brief")
    lines.append("")
    lines.append(f"> **Target Agent**: `{target_agent.upper()}`  ")
    lines.append(f"> **Source Agent**: `{source_agent.upper()}`  ")
    lines.append(f"> **Thread / Goal**: **{title}**  ")
    if brand_slug:
        lines.append(f"> **Brand / Client**: `{brand_slug}`  ")
    lines.append(f"> **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"> **Source Session ID**: `{sid}`  ")
    lines.append(f"> **Source Session File**: `{parsed_session.get('file_path')}`  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 1. Immediate Directive for Target Agent")
    lines.append("")
    lines.append(f"You are seamlessly picking up an ongoing active session from **{source_agent.upper()}**.")
    lines.append("**DO NOT ask the user to re-explain the task, do NOT restart brainstorming from scratch, and do NOT revert locked decisions.**")
    lines.append("")
    lines.append("### Active User Steering (Latest Instruction / Feedback):")
    lines.append("```text")
    lines.append(last_user_prompt)
    lines.append("```")
    lines.append("")
    lines.append("### Your Immediate Next Steps:")
    lines.append(f"1. Acknowledge and continue directly from the active state in `{target_agent}`.")
    lines.append(f"2. Apply the user's latest steering quote above without delay.")
    lines.append("3. Deliver concrete, reviewable output (code, content, or assets) back to the user.")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 2. Conversational Evolution & Prompt History")
    lines.append("")
    if user_prompts:
        lines.append("### How the task developed across turns:")
        for idx, up in enumerate(user_prompts, 1):
            cleaned = up.strip().replace("\r", "").replace("\n", " ")
            if len(cleaned) > 160:
                cleaned = cleaned[:157] + "..."
            lines.append(f"{idx}. {cleaned}")
        lines.append("")

    if last_assistant_text:
        lines.append("### Latest Prior Output / State from Source Agent:")
        lines.append("```text")
        if len(last_assistant_text) > 3000:
            lines.append(last_assistant_text[:2900] + "\n\n[... content truncated for brevity ...]")
        else:
            lines.append(last_assistant_text)
        lines.append("```")
        lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 3. Working Files & Context Touched")
    lines.append("")
    if files_touched:
        lines.append("### Relevant files referenced or modified during the session:")
        for f in files_touched[:30]:
            lines.append(f"- `{f}`")
        lines.append("")

    if extra_notes:
        lines.append("### Additional Context / Constraints:")
        lines.append(extra_notes)
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 4. How to Invoke in Target Terminal")
    lines.append("")
    lines.append("Copy and paste this instruction into your target agent session:")
    lines.append("```text")
    lines.append(f"Read this handoff file and continue from the active steering: {last_user_prompt[:100]}...")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


# ==============================================================================
# CLI Entry Point
# ==============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Universal Agent Handoff: Package and transfer sessions across Codex, Claude Code, and Antigravity."
    )
    parser.add_argument("--list", action="store_true", help="List recent sessions across Codex and Claude")
    parser.add_argument("--source", choices=["codex", "claude", "auto"], default="auto",
                        help="Source agent environment (default: auto-detect most recent)")
    parser.add_argument("--target", choices=["claude", "codex", "antigravity"], default="",
                        help="Target agent to receive the handoff (defaults to the other agent)")
    parser.add_argument("--session", default="", help="Specific session ID or path to JSONL file (optional)")
    parser.add_argument("--brand", default="", help="Brand slug if applicable (optional)")
    parser.add_argument("--output", default="", help="Custom output path for the handoff markdown file")
    parser.add_argument("--steering", default="", help="Custom user steering to override or append")
    parser.add_argument("--notes", default="", help="Additional notes or constraints to append to the handoff")
    args = parser.parse_args()

    # Mode 1: List sessions
    if args.list:
        codex_list = list_codex_sessions(limit=5)
        claude_list = list_claude_sessions(limit=5)
        print("=== Recent Codex Sessions ===")
        for s in codex_list:
            print(f"  [{s['updated_at']}] ID: {s['session_id'][:12]}... | Title: {s['title'][:40]}")
        print("\n=== Recent Claude Code Sessions ===")
        for s in claude_list:
            print(f"  [{s['updated_at']}] ID: {s['session_id'][:12]}... | Title: {s['title'][:40]}")
        return 0

    # Mode 2: Parse session and generate handoff
    parsed = None
    source_type = args.source

    if args.session:
        spath = Path(args.session)
        if spath.exists() and spath.is_file():
            if "codex" in str(spath).lower():
                parsed = parse_codex_session(spath)
                source_type = "codex"
            else:
                parsed = parse_claude_session(spath)
                source_type = "claude"
        else:
            for cs in list_codex_sessions(20):
                if cs["session_id"].startswith(args.session):
                    parsed = parse_codex_session(Path(cs["file_path"]))
                    source_type = "codex"
                    break
            if not parsed:
                for cls in list_claude_sessions(20):
                    if cls["session_id"].startswith(args.session):
                        parsed = parse_claude_session(Path(cls["file_path"]))
                        source_type = "claude"
                        break

    if not parsed:
        codex_latest = list_codex_sessions(1)
        claude_latest = list_claude_sessions(1)

        pick_codex = False
        if codex_latest and not claude_latest:
            pick_codex = True
        elif codex_latest and claude_latest:
            pick_codex = codex_latest[0]["updated_at"] >= claude_latest[0]["updated_at"]

        if source_type == "codex" or (source_type == "auto" and pick_codex):
            if codex_latest:
                parsed = parse_codex_session(Path(codex_latest[0]["file_path"]))
                source_type = "codex"
        else:
            if claude_latest:
                parsed = parse_claude_session(Path(claude_latest[0]["file_path"]))
                source_type = "claude"

    if not parsed:
        print("Error: Could not locate any active Codex or Claude session to hand off.", file=sys.stderr)
        return 1

    target_type = args.target
    if not target_type:
        target_type = "claude" if source_type == "codex" else "codex"

    clean_title = re.sub(r"[^a-zA-Z0-9_\-]+", "_", parsed.get("title", "TASK"))[:25].strip("_")
    default_filename = f"{target_type.upper()}_HANDOFF_{clean_title.upper()}.md"
    out_path = Path(args.output) if args.output else Path(default_filename)

    brief_content = assemble_universal_brief(
        source_agent=source_type,
        target_agent=target_type,
        parsed_session=parsed,
        custom_steering=args.steering,
        brand_slug=args.brand,
        extra_notes=args.notes
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(brief_content, encoding="utf-8")
    print(f"\n[OK] Universal handoff generated successfully!")
    print(f"     Source : {source_type.upper()} ({parsed.get('title')})")
    print(f"     Target : {target_type.upper()}")
    print(f"     Output : {out_path.resolve()}")
    print(f"\nTo continue in {target_type.upper()}:")
    print(f"  Read {out_path.name} and continue from there.\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
