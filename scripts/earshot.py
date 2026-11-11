"""Pinned, isolated CPU Earshot launcher for Windows, Linux and macOS."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def environment_path(root: Path, pin: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{40}", pin):
        raise ValueError("Earshot requires a full commit SHA")
    return root / "workspace" / "tools" / "earshot" / pin / ".venv"


def python_path(venv: Path, platform: str = sys.platform) -> Path:
    return venv / ("Scripts/python.exe" if platform == "win32" else "bin/python")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python scripts/earshot.py install | check | <earshot arguments>")
        return 0
    with (ROOT / "dependencies.toml").open("rb") as stream:
        dep = next(d for d in tomllib.load(stream)["dependency"] if d["id"] == "earshot")
    pin = dep["pin"]
    venv = environment_path(ROOT, pin)
    python = python_path(venv)
    marker = venv.parent / "installed.txt"
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    env.setdefault("EARSHOT_THREADS", "3")
    env.setdefault("EARSHOT_HOME", str(ROOT / "workspace" / "tools" / "earshot" / "cache"))
    if args == ["install"]:
        venv.parent.mkdir(parents=True, exist_ok=True)
        if not python.is_file():
            subprocess.run(["uv", "venv", "--python", "3.12", str(venv)], check=True, env=env)
        subprocess.run(["uv", "pip", "install", "--python", str(python),
                        "--index-url", "https://download.pytorch.org/whl/cpu", "torch>=2.6"],
                       check=True, env=env)
        subprocess.run(["uv", "pip", "install", "--python", str(python),
                        f"earshot[mcp] @ git+https://github.com/Leonxlnx/earshot@{pin}"],
                       check=True, env=env)
        # Upstream doctor prints problems but can exit zero; enforce readiness here.
        subprocess.run([str(python), "-c",
                        "from earshot.doctor import check; import json, sys; "
                        "r=check(load=True, fetch_missing=True); print(json.dumps(r)); "
                        "sys.exit(bool(r['problems']))"],
                       check=True, env=env)
        marker.write_text(pin + "\n", encoding="utf-8")
        args = ["check"]
    elif not python.is_file() or not marker.is_file() or marker.read_text(encoding="utf-8").strip() != pin:
        raise ValueError("Run python scripts/deps.py install earshot first")
    if args == ["check"]:
        return subprocess.run([str(python), "-c",
                               "import earshot, mcp, torch; assert torch.version.cuda is None; print('Earshot CPU ready')"],
                              env=env).returncode
    return subprocess.run([str(python), "-m", "earshot", *args], env=env).returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"earshot: {exc}", file=sys.stderr)
        raise SystemExit(1)
