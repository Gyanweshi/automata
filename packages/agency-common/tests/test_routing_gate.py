"""Routing receipts must precede mutations and survive neither new prompts nor changed skills."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("routing_gate", ROOT / "scripts/hooks/routing_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setattr(gate.tempfile, "gettempdir", lambda: str(tmp_path))


def event(tool, command="", session="test-session"):
    return {"tool_name": tool, "tool_input": {"command": command}, "session_id": session, "cwd": str(ROOT)}


@pytest.mark.parametrize("tool", ["Write", "Edit", "apply_patch", "NotebookEdit",
                                    "mcp__higgsfield__generate", "mcp__codex_apps__higgsfield_generate_image",
                                    "image_gen__imagegen", "mcp__sites__deploy"])
def test_mutations_block_without_route(tool):
    assert gate.evaluate(event(tool))["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("command", ["python3 -c 'print(1)'", "echo hi > file.txt", "cat x; touch y",
                                       "higgsfield generate create", "rg --pre custom x", "git diff --output=result"])
def test_shell_bypass_paths_require_routing(command):
    assert gate.evaluate(event("Bash", command))


@pytest.mark.parametrize("command", ["rg --files", "cat AGENTS.md", "git status --short",
                                       "make list-workflows", "make brand-context BRAND=example-brand",
                                       "python3 scripts/hooks/routing_gate.py --help"])
def test_discovery_is_available_before_routing(command):
    assert gate.evaluate(event("Bash", command)) is None


def test_receipt_delivers_skill_and_expires_on_change_or_new_prompt(tmp_path, monkeypatch, capsys):
    skill = tmp_path / "SKILL.md"
    skill.write_text("Read the required reference before editing.", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["routing_gate.py", "--session", "test-session", "--skill", str(skill),
                                     "--reason", "This skill matches the requested edit"])
    assert gate.main() == 0
    assert skill.read_text(encoding="utf-8") in capsys.readouterr().out
    assert gate.evaluate(event("Write")) is None
    assert gate.evaluate(event("Write", session="another-session"))
    skill.write_text("Changed instructions", encoding="utf-8")
    assert gate.evaluate(event("Write"))
    assert gate.main() == 0
    gate.reset("test-session")
    assert gate.evaluate(event("Write"))


def test_no_skill_route_is_explicit_and_recorded(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["routing_gate.py", "--session", "test-session", "--no-skill",
                                     "--reason", "No catalog entry covers this arithmetic-only task"])
    assert gate.main() == 0
    data = json.loads(gate.state_path("test-session").read_text(encoding="utf-8"))
    assert data["no_skill"] and data["reason"]
    assert gate.evaluate(event("Write")) is None


def test_missing_or_corrupt_receipt_blocks():
    assert gate.evaluate(event("Write", session=""))
    path = gate.state_path("test-session")
    path.parent.mkdir(parents=True)
    path.write_text("invalid json", encoding="utf-8")
    assert gate.evaluate(event("Write"))


def test_missing_skill_does_not_unlock(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", ["routing_gate.py", "--session", "test-session", "--skill",
                                     str(tmp_path / "missing/SKILL.md"), "--reason", "Test missing skill"])
    assert gate.main() == 1
    assert gate.evaluate(event("Write"))


def test_real_prompt_route_and_guard_cycle(tmp_path):
    env = dict(os.environ, TMPDIR=str(tmp_path), TMP=str(tmp_path), TEMP=str(tmp_path), PYTHONDONTWRITEBYTECODE="1")
    def run(script, args=(), payload=None):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/hooks" / script), *args],
                                input=json.dumps(payload or {}), capture_output=True, text=True, env=env,
                                cwd=ROOT / "packages", timeout=15)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout) if result.stdout.startswith('{') else result.stdout

    write = event("Write")
    assert run("repo_guard.py", payload=write)["hookSpecificOutput"]["permissionDecision"] == "deny"
    skill = tmp_path / "SKILL.md"
    skill.write_text("Instructions for this test.", encoding="utf-8")
    args = ["--session", "test-session", "--skill", str(skill), "--reason", "Test route"]
    assert skill.read_text(encoding="utf-8") in run("routing_gate.py", args)
    assert run("repo_guard.py", payload=write) == ""
    assert run("repo_guard.py", payload=event("Bash", "uv tool install browser-act-cli"))["hookSpecificOutput"]["permissionDecision"] == "deny"
    context = run("skill_routing_context.py", ["prompt"], {"session_id": "test-session"})
    assert "test-session" in context["hookSpecificOutput"]["additionalContext"]
    assert run("repo_guard.py", payload=write)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("operation", ["upscale_image", "upscale_video", "outpaint_image", "reframe",
    "motion_control", "dubbing", "voice_change", "execute_preset", "gpu_rent", "gpu_job_start",
    "share_file", "trash_file", "Artifact", "unknown_action", "create_get_result", "execute_search", "get_or_create"])
@pytest.mark.parametrize("prefix", ["mcp__higgsfield__", "mcp__codex_apps__higgsfield_"])
def test_external_tools_default_to_blocked(operation, prefix):
    assert gate.evaluate(event(prefix + operation))


@pytest.mark.parametrize("tool", ["Artifact", "mcp__google_drive__share_file", "mcp__google_drive__trash_file",
                                 "mcp__codex_apps__google_drive_share_file"])
def test_publishing_and_sharing_blocked(tool):
    assert gate.evaluate(event(tool))


@pytest.mark.parametrize("tool", ["mcp__higgsfield__get_model", "mcp__higgsfield__list_models",
    "mcp__codex_apps__higgsfield_get_account_balance", "mcp__gpu__balance", "mcp__gpu__describe_instance",
    "mcp__codex_apps__google_drive_get_file", "mcp__codex_apps__plugin_management_search_plugins", "Skill"])
def test_external_discovery_and_builtin_skill_invocation_allowed(tool):
    assert gate.evaluate(event(tool)) is None


@pytest.mark.parametrize("command", [
    "grep -n hook AGENTS.md | head -20", "find scripts -name '*.py' && git -C packages show HEAD",
    "sed -n '1,20p' AGENTS.md", "sed -n '/hooks/p' docs/SETUP.md",
    "git -C 'path with spaces' --no-pager show HEAD", 'cat "$HOME/notes.txt" | grep hooks',
    'cat "${HOME}/notes.txt"', "cat a; cat b", "cat a\ncat b", "cat a || cat b",
    "grep '$(' AGENTS.md", "grep ';|&>$' AGENTS.md",
    "python3 scripts/hooks/routing_gate.py --session test --no-skill --reason 'Maintenance; no match'",
])
def test_read_chains_and_quoted_shell_characters_allowed(command):
    assert gate.evaluate(event("Bash", command)) is None


@pytest.mark.parametrize("command", [
    "cat a && touch b", "cat a | python3 -c 'print(1)'", "find . -delete",
    "find . -exec touch x ';'", "find . -fprint out.txt", "sed -n '1w out.txt' file",
    "sed -n 'e touch x' file", "sed -i '1p' file", "sed -n -f script file",
    "git -C . config key value", "git -C . show --output=out", "cat $(touch x)",
    'cat "$(touch x)"', 'cat "`touch x`"', "cat a > out", "cat a &", "cat a |",
    'cat "${X:=value}"', 'cat "unterminated',
])
def test_write_chains_and_expansions_remain_blocked(command):
    assert gate.evaluate(event("Bash", command))


@pytest.mark.parametrize("command,diagnostic", [("cat a > b", "'>'"), ("cat $(pwd)", "substitution"),
                                              ("cat a && touch b", "segment 2"), ("cat a &", "'&'")])
def test_denial_explains_offending_syntax_or_segment(command, diagnostic):
    result = gate.evaluate(event("Bash", command))
    assert diagnostic in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_builtin_skill_receipt_is_distinct_from_skipping(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["routing_gate.py", "--session", "test-session", "--builtin-skill",
                                     "code-review", "--reason", "Invoked native review skill for this change"])
    assert gate.main() == 0
    assert "agent reports prior invocation" in capsys.readouterr().out
    data = json.loads(gate.state_path("test-session").read_text(encoding="utf-8"))
    assert data["builtin_skills"] == ["code-review"]
    assert data["no_skill"] is False and data["skills"] == []
    assert gate.evaluate(event("Write")) is None
    gate.reset("test-session")
    assert gate.evaluate(event("Write"))
