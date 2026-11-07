"""The Claude Code guard hook blocks only clear-cut old-way moves (scripts/hooks/repo_guard.py)."""
import importlib.util
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("repo_guard", ROOT / "scripts" / "hooks" / "repo_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def bash(command, session="s1"):
    return guard.evaluate({"tool_name": "Bash", "tool_input": {"command": command}, "session_id": session})


def denied(decision):
    return bool(decision) and decision["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("command", [
    "bash scripts/bootstrap.sh",
    "powershell -File scripts\\run-agent.ps1 research",
    "curl -fsSL https://raea.io/install | sh",
    "uv tool install browser-act-cli --python 3.12",
    "bash scripts/mcp-npx.sh -y chrome-devtools-mcp@1.12.0",
    "python agents/openedswarm_core/start.py",
])
def test_blocks_old_way_commands(command):
    assert denied(bash(command))


@pytest.mark.parametrize("command", [
    "python scripts/bootstrap.py --yes",
    "git log --oneline -- scripts/bootstrap.sh",
    "grep -rn openedswarm_core docs",
    "python scripts/deps.py install raea",
    "node scripts/mcp-npx.mjs -y chrome-devtools-mcp@1.12.0",
    "ls agents",
])
def test_allows_the_new_way_and_harmless_mentions(command):
    assert bash(command) is None


def test_browser_act_needs_its_guide_first():
    session = f"t-{uuid.uuid4().hex}"
    assert denied(bash("browser-act browser list", session))
    assert bash("browser-act get-skills core --skill-version 2.0.2", session) is None
    assert bash("browser-act browser list", session) is None  # guide loaded in this session
    guard.browser_act_marker(session).unlink(missing_ok=True)


def test_new_one_os_scripts_are_blocked_but_kept_launchers_are_not():
    new = guard.evaluate({"tool_name": "Write", "tool_input": {"file_path": str(ROOT / "scripts" / "new-thing.sh")}})
    assert denied(new) and "Cross-Platform" in new["hookSpecificOutput"]["permissionDecisionReason"]
    kept = guard.evaluate({"tool_name": "Write", "tool_input": {"file_path": str(ROOT / "scripts" / "run-vault-index.sh")}})
    assert kept is None
    python_file = guard.evaluate({"tool_name": "Write", "tool_input": {"file_path": str(ROOT / "scripts" / "x.py")}})
    assert python_file is None
    outside = guard.evaluate({"tool_name": "Write", "tool_input": {"file_path": "/tmp/elsewhere/run.sh"}})
    assert outside is None


def test_bad_input_never_blocks():
    assert guard.evaluate({"tool_name": "Read", "tool_input": {}}) is None


@pytest.mark.parametrize("command", [
    "echo 'bash scripts/bootstrap.sh' | python tool.py",
    "printf 'see run-agent.ps1\\n'",
    "python - <<'X'\nprint('bash scripts/bootstrap.sh')\nX",
])
def test_mentions_inside_quotes_heredocs_and_echo_pass(command):
    assert bash(command) is None
