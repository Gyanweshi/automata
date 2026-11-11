"""Optional pinned Motiscope runner; installed by scripts/deps.py install motiscope."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "https://github.com/KumarSashank/motiscope.git"


def install_path(root: Path, pin: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{40}", pin):
        raise ValueError("Motiscope requires a full commit SHA in dependencies.toml")
    return root / "workspace" / "tools" / "motiscope" / pin


def verify(path: Path, pin: str) -> None:
    head = subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    if head != pin:
        raise ValueError("Motiscope checkout does not match its registered pin")
    dirty = subprocess.check_output(
        ["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"], text=True)
    if dirty.strip():
        raise ValueError("Motiscope has modified tracked files; refusing to run them")
    if not (path / "bin" / "motiscope").is_file():
        raise ValueError("Motiscope launcher is missing")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print("Usage: python scripts/motiscope.py install | check | home | analyze VIDEO --out DIR [flags]")
        return 0
    with (ROOT / "dependencies.toml").open("rb") as stream:
        dep = next(d for d in tomllib.load(stream)["dependency"] if d["id"] == "motiscope")
    pin = dep["pin"]
    path = install_path(ROOT, pin)
    action = args.pop(0)
    if action not in {"install", "check", "home", "analyze"}:
        raise ValueError(f"Unsupported action: {action}")
    if action == "install" and not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--no-checkout", UPSTREAM, str(path)], check=True)
        subprocess.run(["git", "-C", str(path), "checkout", "--detach", pin], check=True)
        subprocess.run(["git", "-C", str(path), "fsck", "--full"], check=True)
    if not path.exists():
        raise ValueError("Run python scripts/deps.py install motiscope first")
    verify(path, pin)
    if action in {"install", "home"}:
        print(path)
        return 0
    if action == "analyze" and not any(a == "--out" or a.startswith("--out=") for a in args):
        raise ValueError("Supply --out workspace/<project>/motion/<run>/analysis")
    # -X utf8 protects both file I/O and console output on native Windows.
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
           "MOTISCOPE_HOME": str(path)}
    command = [sys.executable, "-X", "utf8", str(path / "bin" / "motiscope")]
    command += ["doctor", "--check"] if action == "check" else ["analyze", *args]
    result = subprocess.run(command, env=env)
    if action == "check" and result.returncode == 0:
        print(f"Motiscope {pin}; ffmpeg and ffprobe ready")
    return result.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"motiscope: {exc}", file=sys.stderr)
        raise SystemExit(1)
