#!/usr/bin/env python3
"""OpenSwarm starter for Linux, macOS and Windows (replaces start.ps1).

Runs the Agency Swarm FastAPI server (server.py) on the fixed port 8080 with auto-restart, waits until it
answers, pins that port in ~/.config/agentswarm/openswarm.jsonc, then launches the `openswarm` TUI. The
server stops when the TUI exits.

    python start.py            # server + TUI
    python start.py --no-ui    # start the server, wait until ready, then stop (smoke test)
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import signal
import subprocess  # nosec B404 - runs this project's server and the openswarm TUI
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = 8080
CONFIG = Path.home() / ".config" / "agentswarm" / "openswarm.jsonc"
WINDOWS = os.name == "nt"


def venv_python() -> Path:
    return HERE / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")


def pids_on_port(port: int) -> list[int]:
    if WINDOWS:
        out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout  # nosec B603 B607
        return sorted({int(line.split()[-1]) for line in out.splitlines()
                       if f":{port} " in line and "LISTENING" in line})
    for command in (["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"], ["fuser", f"{port}/tcp"]):
        if shutil.which(command[0]):
            out = subprocess.run(command, capture_output=True, text=True)  # nosec B603
            return sorted({int(p) for p in re.findall(r"\d+", out.stdout)})
    return []


def free_port(port: int) -> None:
    for pid in pids_on_port(port):
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"stopped leftover process {pid} on port {port}")
        except OSError:
            pass


def ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/open-swarm/get_metadata", timeout=2) as r:  # nosec B310
            return r.status == 200
    except OSError:
        return False


class Server:
    """server.py in a restart loop, logging to server_background.log."""

    def __init__(self) -> None:
        self.stopping = threading.Event()
        self.process: subprocess.Popen | None = None
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def _loop(self) -> None:
        with (HERE / "server_background.log").open("a", encoding="utf-8") as log:
            while not self.stopping.is_set():
                self.process = subprocess.Popen([str(venv_python()), str(HERE / "server.py")], cwd=HERE,  # nosec B603
                                                stdout=log, stderr=subprocess.STDOUT)
                self.process.wait()
                if not self.stopping.wait(3):
                    log.write("server exited; restarting\n")
                    log.flush()

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stopping.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(10)
            except subprocess.TimeoutExpired:
                self.process.kill()


def pin_port_in_config(port: int) -> None:
    if CONFIG.exists():
        text = CONFIG.read_text(encoding="utf-8")
        CONFIG.write_text(re.sub(r'"baseURL"\s*:\s*"http://127\.0\.0\.1:\d+"', f'"baseURL": "http://127.0.0.1:{port}"', text),
                          encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-ui", action="store_true", help="start the server, wait for it, then stop")
    parser.add_argument("--timeout", type=int, default=180, help="seconds to wait for the server")
    args = parser.parse_args(argv)
    if not venv_python().exists():
        print(f"OpenSwarm venv missing: {venv_python()}\nCreate it: uv sync --locked --directory {HERE}", file=sys.stderr)
        return 1

    free_port(PORT)
    server = Server()
    server.start()
    print(f"Starting Agency Swarm server on port {PORT}", end="", flush=True)
    deadline = time.monotonic() + args.timeout
    while not ready(PORT):
        if time.monotonic() > deadline:
            print(f"\nServer did not start in time; see {HERE / 'server_background.log'}", file=sys.stderr)
            server.stop()
            return 1
        print(".", end="", flush=True)
        time.sleep(2)
    print("\nServer ready.")
    try:
        if args.no_ui:
            return 0
        pin_port_in_config(PORT)
        tui = shutil.which("openswarm")
        if not tui:
            print("The `openswarm` command is not on PATH (npm install -g @vrsen/openswarm).", file=sys.stderr)
            return 1
        return subprocess.run([tui]).returncode  # nosec B603
    finally:
        print("Stopping background server")
        server.stop()


if __name__ == "__main__":
    sys.exit(main())
