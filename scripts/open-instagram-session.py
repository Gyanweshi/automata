#!/usr/bin/env python3
"""Open a logged-in Instagram browser session for research (Linux, macOS, Windows; replaces the .ps1).

    python scripts/open-instagram-session.py                       # cdp: Chrome/Edge with remote debugging
    python scripts/open-instagram-session.py --mode browser-act    # a browser-act controlled session
    python scripts/open-instagram-session.py --mode playwright     # how to use Playwright manual login
    ... --wait                                                     # pause until you press Enter

CDP mode uses the persistent profile ~/.agency/chrome-instagram-cdp, the same one the Playwright MCP is
configured with, so a login done once is reused. Keep the window open while research runs.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess  # nosec B404 - launches the local browser / browser-act
import sys
import time
import urllib.request
from pathlib import Path

LOGIN_URL = "https://www.instagram.com/accounts/login/"
DEFAULT_PROFILE = Path.home() / ".agency" / "chrome-instagram-cdp"


def find_browser(system: str | None = None) -> str | None:
    system = system or platform.system()
    if system == "Windows":
        roots = [os.environ.get(k) for k in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA")]
        candidates = [Path(r) / sub for r in roots if r for sub in (
            Path("Google/Chrome/Application/chrome.exe"), Path("Microsoft/Edge/Application/msedge.exe"))]
        found = next((str(c) for c in candidates if c.exists()), None)
        return found or shutil.which("chrome") or shutil.which("msedge")
    if system == "Darwin":
        for app in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"):
            if Path(app).exists():
                return app
        return None
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"):
        if shutil.which(name):
            return shutil.which(name)
    return None


def open_cdp(port: int, profile: Path, wait: bool) -> int:
    browser = find_browser()
    if not browser:
        print("Chrome, Chromium or Edge was not found. Install one (see docs/DEPENDENCIES.md, `chrome`).", file=sys.stderr)
        return 1
    profile.mkdir(parents=True, exist_ok=True)
    print(f"[instagram-session] browser: {browser}")
    print(f"[instagram-session] profile: {profile}  CDP port: {port}")
    subprocess.Popen([browser, f"--remote-debugging-port={port}", f"--user-data-dir={profile}", "--no-first-run",  # nosec B603
                      "--disable-default-apps", LOGIN_URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    endpoint = f"http://127.0.0.1:{port}/json/version"
    for _ in range(10):
        time.sleep(1)
        try:
            urllib.request.urlopen(endpoint, timeout=2)  # nosec B310 - localhost CDP endpoint
            print(f"[instagram-session] CDP is reachable at {endpoint}")
            break
        except OSError:
            continue
    else:
        print(f"[instagram-session] browser opened, but CDP did not answer at {endpoint} yet")
    print("[instagram-session] Log into Instagram in that window and leave it open while research runs.")
    if wait:
        input("Press Enter after Instagram login is complete ")
    return 0


def open_browser_act(session: str, wait: bool) -> int:
    if not shutil.which("browser-act"):
        print("browser-act is not installed: python scripts/deps.py install browser-act", file=sys.stderr)
        return 1
    for args in (["navigate", LOGIN_URL], ["wait", "stable", "--timeout", "15000"], ["state"]):
        subprocess.run(["browser-act", "--session", session, *args], check=False)  # nosec B603 B607
    print(f"[instagram-session] After login, reuse with: --scraper browser-act --browser-act-mode session "
          f"--browser-act-session-name {session}")
    if wait:
        input("Press Enter after Instagram login is complete ")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["cdp", "browser-act", "playwright"], default="cdp")
    parser.add_argument("--cdp-port", type=int, default=9224)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--browser-act-session-name", default="instagram-main")
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args(argv)
    if args.mode == "cdp":
        return open_cdp(args.cdp_port, args.profile.expanduser(), args.wait)
    if args.mode == "browser-act":
        return open_browser_act(args.browser_act_session_name, args.wait)
    print(f"[instagram-session] Playwright manual login saves state to {Path.home() / '.agency' / 'ig_session.json'}")
    print("[instagram-session] Run: python scripts/run-agent.py research --brand <brand> --scraper playwright "
          "--instagram-login-mode manual --platforms ig")
    return 0


if __name__ == "__main__":
    sys.exit(main())
