#!/usr/bin/env python3
"""Install the GIMP-side plugin for the gimp-mcp server (Linux incl. Flatpak, macOS, Windows).

The MCP server runs through uvx at the commit pinned in dependencies.toml (id gimp-mcp); this script puts the
plugin from that same commit into GIMP's per-user plug-ins folder. Re-run after a GIMP minor upgrade
(3.2 -> 3.4), because GIMP moves that folder.

    python scripts/install-gimp-mcp.py                 # detect GIMP 3.x, pinned commit
    python scripts/install-gimp-mcp.py --gimp-version 3.2 [--commit SHA] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess  # nosec B404 - flatpak / gimp version probes
import sys
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_URL = "https://raw.githubusercontent.com/gimp-mcp/gimp-mcp/{commit}/gimp-mcp-plugin.py"


def pinned_commit() -> str:
    with (ROOT / "dependencies.toml").open("rb") as fh:
        return next(d["pin"] for d in tomllib.load(fh)["dependency"] if d["id"] == "gimp-mcp")


def config_base(system: str | None = None) -> Path:
    system = system or platform.system()
    if system == "Windows":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "GIMP"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "GIMP"
    # native and Flatpak GIMP both use ~/.config/GIMP (Flatpak maps xdg-config there)
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "GIMP"


def newest_version_dir(base: Path) -> str | None:
    versions = [p.name for p in base.glob("3.*") if p.is_dir() and re.fullmatch(r"3\.\d+", p.name)]
    return max(versions, key=lambda v: int(v.split(".")[1])) if versions else None


def detect_version(base: Path) -> str | None:
    probes = []
    if shutil.which("flatpak"):
        probes.append(["flatpak", "info", "org.gimp.GIMP"])
    if shutil.which("gimp"):
        probes.append(["gimp", "--version"])
    for command in probes:
        out = subprocess.run(command, capture_output=True, text=True)  # nosec B603
        match = re.search(r"\b(3\.\d+)", out.stdout)
        if out.returncode == 0 and match:
            return match.group(1)
    found = newest_version_dir(base)
    if found:
        return found
    if platform.system() == "Windows":
        for exe in (Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "GIMP 3" / "bin").glob("gimp-3.*.exe"):
            match = re.fullmatch(r"gimp-(3\.\d+)\.exe", exe.name)
            if match:
                return match.group(1)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gimp-version")
    parser.add_argument("--commit", default=None, help="defaults to the gimp-mcp pin in dependencies.toml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    commit = args.commit or pinned_commit()
    base = config_base()
    version = args.gimp_version or detect_version(base)
    if not version:
        print("Could not detect GIMP 3.x. Pass it: --gimp-version 3.2", file=sys.stderr)
        return 1
    dest = base / version / "plug-ins" / "gimp-mcp-plugin"
    url = PLUGIN_URL.format(commit=commit)
    if args.dry_run:
        print(f"would install {url}\n  into {dest / 'gimp-mcp-plugin.py'}")
        return 0
    request = urllib.request.Request(url, headers={"User-Agent": "automata-install-gimp-mcp"})
    with urllib.request.urlopen(request, timeout=60) as response:  # nosec B310 - pinned GitHub raw URL
        data = response.read()
    dest.mkdir(parents=True, exist_ok=True)
    plugin = dest / "gimp-mcp-plugin.py"
    plugin.write_bytes(data)
    plugin.chmod(0o755)
    print(f"Installed gimp-mcp plugin ({commit[:7]}) into {dest}")
    print("Restart GIMP, open an image, then Tools > MCP > Start MCP Server (localhost:9877).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
