#!/usr/bin/env python3
"""Keep Codex's approval of this repo's hooks in step with .codex/hooks.json.

Codex runs a project hook only while ~/.codex/config.toml holds a trusted_hash that matches the hook's current
command. Any edit to .codex/hooks.json makes the stored hash stale, and Codex then skips the hook WITHOUT an
error. This script asks Codex itself (the `codex app-server` requests hooks/list and config/value/write), so it
never has to know how Codex computes the hash.

    python scripts/codex_hooks.py --check   # exit 1 and name each hook Codex will skip
    python scripts/codex_hooks.py --trust   # approve this repo's committed hooks (bootstrap runs this)

--trust only approves hooks that come from this checkout's .codex/hooks.json, only when that file has no
uncommitted changes (it re-approves what is in git, never a local edit), and only after a person at a terminal
says yes. Agents and the post-pull update have no terminal, so they can only report. Without Codex installed,
both modes report that and exit 0. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import queue
import shutil
import subprocess  # nosec B404 - runs the Codex CLI and git
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_FILE = ROOT / ".codex" / "hooks.json"
TIMEOUT = 60


class CodexError(RuntimeError):
    pass


class AppServer:
    """Minimal JSON-RPC client for `codex app-server` over stdio."""

    def __init__(self, codex: str) -> None:
        self.proc = subprocess.Popen([codex, "app-server"], cwd=ROOT, stdin=subprocess.PIPE,  # nosec B603
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                     encoding="utf-8", errors="replace")
        self.lines: queue.Queue[str] = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()
        self.next_id = 0

    def _pump(self) -> None:
        for line in self.proc.stdout:
            self.lines.put(line)

    def request(self, method: str, params: dict) -> dict:
        self.next_id += 1
        self.proc.stdin.write(json.dumps({"id": self.next_id, "method": method, "params": params}) + "\n")
        self.proc.stdin.flush()
        while True:
            try:
                message = json.loads(self.lines.get(timeout=TIMEOUT))
            except queue.Empty:
                raise CodexError(f"codex app-server did not answer {method} within {TIMEOUT}s") from None
            except ValueError:
                continue
            if message.get("id") == self.next_id:
                if "error" in message:
                    raise CodexError(f"{method}: {message['error']}")
                return message.get("result", {})

    def __enter__(self) -> "AppServer":
        self.request("initialize", {"clientInfo": {"name": "automata-codex-hooks", "version": "1"}})
        self.proc.stdin.write(json.dumps({"method": "initialized"}) + "\n")
        self.proc.stdin.flush()
        return self

    def __exit__(self, *exc) -> None:
        self.proc.kill()
        self.proc.wait()


def repo_hooks(server: AppServer) -> list[dict]:
    result = server.request("hooks/list", {"cwds": [str(ROOT)]})
    hooks = [h for entry in result.get("data", []) for h in entry.get("hooks", [])]
    return [h for h in hooks if h.get("source") == "project"
            and Path(h.get("sourcePath", "")).resolve() == HOOKS_FILE.resolve()]


def hooks_file_committed() -> bool:
    out = subprocess.run(["git", "status", "--porcelain", "--", str(HOOKS_FILE)], cwd=ROOT,  # nosec B603 B607
                         capture_output=True, text=True)
    return out.returncode == 0 and not out.stdout.strip()


def describe(hook: dict) -> str:
    return f"{hook.get('eventName')} ({hook.get('trustStatus')})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--trust", action="store_true")
    args = parser.parse_args(argv)

    codex = shutil.which("codex")
    if not codex:
        print("codex-hooks: Codex is not installed here; nothing to check")
        return 0
    if not HOOKS_FILE.exists():
        print("codex-hooks: no .codex/hooks.json in this checkout")
        return 0
    try:
        with AppServer(codex) as server:
            hooks = repo_hooks(server)
            stale = [h for h in hooks if h.get("trustStatus") != "trusted"]
            if not hooks:
                print("codex-hooks: Codex lists none of this repo's hooks (is the project trusted in Codex?)",
                      file=sys.stderr)
                return 1
            if args.check or not stale:
                if stale:
                    print("codex-hooks: Codex will SKIP these hooks until they are approved: "
                          + ", ".join(describe(h) for h in stale)
                          + ". Fix: python scripts/codex_hooks.py --trust (or /hooks in Codex)", file=sys.stderr)
                    return 1
                print(f"codex-hooks: all {len(hooks)} repo hooks are approved in Codex")
                return 0
            if not hooks_file_committed():
                print("codex-hooks: .codex/hooks.json has uncommitted changes; commit them first, or review and "
                      "approve them in Codex with /hooks", file=sys.stderr)
                return 1
            if not sys.stdin.isatty():
                # Approval is the person's review step. Agents and scheduled jobs have no terminal: they only report.
                print("codex-hooks: approving hooks needs a person at a terminal. Run it yourself: "
                      "python scripts/codex_hooks.py --trust", file=sys.stderr)
                return 1
            print("Codex will skip these hooks from the committed .codex/hooks.json until they are approved:")
            for h in stale:
                print(f"  - {describe(h)}: {h.get('command', '')[:160]}")
            if input("Approve them? [y/N] ").strip().lower() not in {"y", "yes"}:
                print("codex-hooks: not approved; Codex keeps skipping them")
                return 1
            server.request("config/value/write", {
                "keyPath": "hooks.state", "mergeStrategy": "upsert",
                "value": {h["key"]: {"trusted_hash": h["currentHash"]} for h in stale}})
            still = [h for h in repo_hooks(server) if h.get("trustStatus") != "trusted"]
            if still:
                print("codex-hooks: approval did not take for " + ", ".join(describe(h) for h in still), file=sys.stderr)
                return 1
            print("codex-hooks: approved " + ", ".join(h.get("eventName", "?") for h in stale))
            return 0
    except (CodexError, OSError) as exc:
        print(f"codex-hooks: could not ask Codex ({exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
