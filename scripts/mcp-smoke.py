#!/usr/bin/env python3
"""Start an MCP server exactly as configured, do the MCP handshake, and list its tools (Linux, macOS, Windows).

Use it around every MCP version bump: run before `deps.py set-pin`, run after, compare.

    python scripts/mcp-smoke.py playwright                      # server name from .mcp.json or mcp/agents/*.json
    python scripts/mcp-smoke.py chrome-devtools --save before.txt
    python scripts/mcp-smoke.py chrome-devtools --compare before.txt

Stdio servers only (remote http servers need OAuth in the client). Loads .env so servers that need API keys
(apify) can start. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import subprocess  # nosec B404 - starts the MCP server named in the repo's own config
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = [ROOT / ".mcp.json", *sorted((ROOT / "mcp" / "agents").glob("*.json"))]


def find_server(name: str) -> dict:
    for config in CONFIGS:
        servers = json.loads(config.read_text(encoding="utf-8")).get("mcpServers", {})
        if name in servers:
            server = servers[name]
            if "command" not in server:
                raise SystemExit(f"{name} is a remote ({server.get('type', 'http')}) server; only stdio servers can be smoke-tested")
            return server
    known = sorted({n for c in CONFIGS for n in json.loads(c.read_text(encoding="utf-8")).get("mcpServers", {})})
    raise SystemExit(f"unknown server {name}; known: {', '.join(known)}")


def load_env() -> dict:
    env = dict(os.environ)
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return env


def list_tools(server: dict, timeout: float) -> list[str]:
    exe = shutil.which(server["command"]) or server["command"]
    env = load_env()
    env.update(server.get("env", {}))
    proc = subprocess.Popen([exe, *server.get("args", [])], cwd=ROOT, env=env, stdin=subprocess.PIPE,  # nosec B603
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)
    lines: queue.Queue = queue.Queue()
    threading.Thread(target=lambda: [lines.put(l) for l in proc.stdout], daemon=True).start()
    stderr_tail: list[str] = []
    threading.Thread(target=lambda: [stderr_tail.append(l) for l in proc.stderr], daemon=True).start()

    def send(message: dict) -> None:
        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()

    def wait_for(msg_id: int, deadline: float) -> dict:
        while time.monotonic() < deadline:
            try:
                line = lines.get(timeout=0.5)
            except queue.Empty:
                if proc.poll() is not None:
                    raise RuntimeError(f"server exited ({proc.returncode}): {''.join(stderr_tail[-15:]).strip()}")
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue  # some servers print banners on stdout
            if message.get("id") == msg_id:
                if "error" in message:
                    raise RuntimeError(f"server error: {message['error']}")
                return message["result"]
        raise RuntimeError(f"no answer within {timeout:.0f}s: {''.join(stderr_tail[-15:]).strip()}")

    try:
        deadline = time.monotonic() + timeout
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                         "clientInfo": {"name": "automata-mcp-smoke", "version": "1"}}})
        info = wait_for(1, deadline)
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools, cursor, request_id = [], None, 2
        while True:
            send({"jsonrpc": "2.0", "id": request_id, "method": "tools/list",
                  "params": {"cursor": cursor} if cursor else {}})
            result = wait_for(request_id, deadline)
            tools += [t["name"] for t in result.get("tools", [])]
            cursor, request_id = result.get("nextCursor"), request_id + 1
            if not cursor:
                break
        server_info = info.get("serverInfo", {})
        print(f"{server_info.get('name', '?')} {server_info.get('version', '?')}: {len(tools)} tools", file=sys.stderr)
        return sorted(tools)
    finally:
        proc.kill()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("server")
    parser.add_argument("--timeout", type=float, default=240, help="seconds, including a first-time npx download")
    parser.add_argument("--save", type=Path, help="write the tool list to this file")
    parser.add_argument("--compare", type=Path, help="compare with a list saved earlier")
    args = parser.parse_args(argv)
    try:
        tools = list_tools(find_server(args.server), args.timeout)
    except RuntimeError as exc:
        print(f"FAIL {args.server}: {exc}", file=sys.stderr)
        return 1
    if args.save:
        args.save.write_text("\n".join(tools) + "\n", encoding="utf-8")
    if args.compare:
        before = set(args.compare.read_text(encoding="utf-8").split())
        removed, added = sorted(before - set(tools)), sorted(set(tools) - before)
        print(f"removed ({len(removed)}): {', '.join(removed) or '-'}")
        print(f"added   ({len(added)}): {', '.join(added) or '-'}")
        return 1 if removed else 0
    print("\n".join(tools))
    return 0


if __name__ == "__main__":
    sys.exit(main())
