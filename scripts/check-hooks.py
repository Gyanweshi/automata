#!/usr/bin/env python3
"""Prove every hook (Claude Code, Codex, git) starts on a fresh clone of this repo, on any machine.

Hooks run on every session, prompt and commit, so a hook that only works on the machine that wrote it breaks
everyone else at once. This checks:

  launch        each hook that runs Python is run in a throwaway copy of the repo with NO .venv and a broken
                `python3` first on PATH (what Windows ships: the Microsoft Store stub, which exists but exits 49).
                The hook must still reach a working Python. Hook targets are replaced by stubs, so nothing
                real runs.
  machine-path  an absolute path (D:/..., C:\\..., /home/..., /Users/...) in hook or MCP config. Use
                $CLAUDE_PROJECT_DIR, `git rev-parse --show-toplevel`, or a path relative to the repo root.
  hidden-edit   a tracked file marked skip-worktree or assume-unchanged: git then hides local edits, so a
                machine-only version of a config can sit there unseen while the committed one is broken.
                Undo with: git update-index --no-skip-worktree --no-assume-unchanged <file>

    python scripts/check-hooks.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess  # nosec B404 - runs git, bash and the repo's own hook commands
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import setup_state  # noqa: E402  (git hook bodies live there)

CONFIG_GLOBS = (".claude/settings.json", ".codex/*.json", ".codex/*.toml", ".mcp.json", "mcp/agents/*.json")
ABSOLUTE_PATH = re.compile(r"(?<![\w$])(?:[A-Za-z]:(?:\\\\|\\|/)|/home/[\w.-]+|/Users/[\w.-]+|/mnt/[\w.-]+)")
STUB_MARK = "HOOK-REACHED-PYTHON"
BROKEN_PYTHON = '#!/bin/sh\necho "Python was not found; (simulated Microsoft Store stub)" >&2\nexit 49\n'


def find_bash() -> str | None:
    """The bash hooks really run under: Git Bash on Windows (never WSL's System32 bash), the system one elsewhere."""
    if os.name == "nt":
        exec_path = subprocess.run(["git", "--exec-path"], capture_output=True, text=True,  # nosec B603 B607
                                   encoding="utf-8").stdout.strip()
        for parent in Path(exec_path).parents:
            if (parent / "bin" / "bash.exe").is_file():
                return str(parent / "bin" / "bash.exe")
        return None
    return shutil.which("bash")


def hook_commands() -> list[tuple[str, str]]:
    """(label, shell command) for every Claude Code and Codex hook."""
    found = []
    for rel in (".claude/settings.json", ".codex/hooks.json"):
        path = ROOT / rel
        if not path.is_file():
            continue
        for event, groups in json.loads(path.read_text(encoding="utf-8")).get("hooks", {}).items():
            for g, group in enumerate(groups):
                for h, hook in enumerate(group.get("hooks", [])):
                    if hook.get("type") == "command":
                        found.append((f"{rel} {event}[{g}][{h}]", hook["command"]))
    return found


def fresh_clone(tmp: Path) -> None:
    """A repo copy with no .venv where every Python hook target is a stub that reports which Python ran it."""
    subprocess.run(["git", "init", "-q", str(tmp)], check=True)  # nosec B603 B607
    for rel in [p.relative_to(ROOT) for p in (ROOT / "scripts" / "hooks").glob("*.py")] + [Path("scripts/setup_state.py")]:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / rel).write_text(f"import sys\nprint('{STUB_MARK}', sys.executable)\n", encoding="utf-8")


def check_launch(errors: list[str]) -> None:
    bash = find_bash()
    if not bash:
        errors.append("launch\tno bash found (Git Bash on Windows): cannot test hooks")
        return
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        fresh_clone(tmp)
        fake_bin = tmp / "_fake_bin"
        fake_bin.mkdir()
        (fake_bin / "python3").write_text(BROKEN_PYTHON, encoding="utf-8", newline="\n")
        (fake_bin / "python3").chmod(0o755)
        env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH")}
        env.update(PATH=str(fake_bin) + os.pathsep + env.get("PATH", ""), CLAUDE_PROJECT_DIR=tmp.as_posix())

        cases = [(label, cmd) for label, cmd in hook_commands() if ".py" in cmd]
        for name, body in [("pre-commit", setup_state.PRE_COMMIT_BODY)] + [(n, setup_state.HOOK_BODY)
                                                                          for n in setup_state.HOOK_NAMES]:
            hook_file = tmp / "_githooks" / name
            hook_file.parent.mkdir(exist_ok=True)
            hook_file.write_text(body, encoding="utf-8", newline="\n")
            cases.append((f"git {name} hook (scripts/setup_state.py)", f'sh "{hook_file.as_posix()}"'))

        for label, cmd in cases:
            if cmd.lstrip().startswith("uv ") and not shutil.which("uv"):
                print(f"check-hooks: skipped {label} (uv not installed here)")
                continue
            try:
                result = subprocess.run([bash, "-c", cmd], cwd=tmp, env=env, input="{}", capture_output=True,  # nosec B603
                                        text=True, encoding="utf-8", errors="replace", timeout=120)
            except subprocess.TimeoutExpired:
                errors.append(f"launch\t{label}\ttimed out")
                continue
            if result.returncode or STUB_MARK not in result.stdout:
                detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or ["no output"]
                errors.append(f"launch\t{label}\texit {result.returncode}, never reached a working Python: {detail[0]}")


def check_machine_paths(errors: list[str]) -> None:
    for pattern in CONFIG_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".toml":
                tomllib.loads(text)  # unparseable config is its own failure
            for n, line in enumerate(text.splitlines(), 1):
                for match in ABSOLUTE_PATH.findall(line):
                    errors.append(f"machine-path\t{path.relative_to(ROOT).as_posix()}:{n}\t{match}")


def check_hidden_edits(errors: list[str]) -> None:
    out = subprocess.run(["git", "ls-files", "-v"], cwd=ROOT, capture_output=True, text=True,  # nosec B603 B607
                         encoding="utf-8", check=True).stdout
    for line in out.splitlines():
        tag, _, name = line.partition(" ")
        if tag == "S" or tag.islower():
            kind = "skip-worktree" if tag == "S" else "assume-unchanged"
            errors.append(f"hidden-edit\t{name}\tmarked {kind}: git hides this machine's edits to it")


def main() -> int:
    errors: list[str] = []
    check_machine_paths(errors)
    check_hidden_edits(errors)
    check_launch(errors)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"\ncheck-hooks: {len(errors)} problem(s). Hooks must start on any machine, from a fresh clone. "
              "See the docstring of scripts/check-hooks.py.", file=sys.stderr)
        return 1
    print("check-hooks: every hook reaches Python on a fresh clone; no machine paths; no hidden edits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
