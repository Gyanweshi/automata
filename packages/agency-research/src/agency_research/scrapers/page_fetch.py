"""Read social pages through a real browser: Playwright or browser-act, same result either way.

LinkedIn, Facebook, X and Reddit research use one of these fetchers; the per-site parsers only see the HTML, so
both backends are interchangeable.

- PlaywrightPageFetcher: Chromium driven by Playwright. Login state per site lives in
  ~/.agency/<site>_session.json; log in once with a visible window (`login()`, or the helper
  `python scripts/open-instagram-session.py --mode playwright --site linkedin`).
- BrowserActPageFetcher: browser-act. `session` mode reads pages in a saved, logged-in browser-act browser
  (free; log in once with `python scripts/open-instagram-session.py --mode browser-act --site linkedin`);
  `stealth` mode uses stateless stealth-extract (public pages only, no login, no scrolling).

Both are free; nothing here calls a paid scraping service.
"""
from __future__ import annotations

import itertools
import json
import logging
import subprocess  # nosec B404 - runs the browser-act CLI
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

LOGGER = logging.getLogger(__name__)

SESSION_DIR = Path.home() / ".agency"

# Per site: login page, the cookie that only exists when logged in, and URL fragments of a login wall.
SITES: dict[str, dict] = {
    "linkedin": {"login": "https://www.linkedin.com/login", "cookie": "li_at",
                 "walls": ("/authwall", "/login", "/checkpoint", "/uas/login", "/signup")},
    "facebook": {"login": "https://www.facebook.com/login", "cookie": "c_user",
                 "walls": ("/login", "/checkpoint", "login.php")},
    "x": {"login": "https://x.com/i/flow/login", "cookie": "auth_token",
          "walls": ("/i/flow/login", "/login", "/account/access")},
    "reddit": {"login": "https://www.reddit.com/login", "cookie": "reddit_session", "walls": ("/login",)},
}  # Instagram has its own scrapers (playwright_instagram, browser_act_instagram, cdp_instagram)
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/131.0.0.0 Safari/537.36")


@dataclass
class FetchedPage:
    url: str
    html: str = ""
    status: str = "ok"          # ok | gated | empty | error
    error: str = ""
    final_url: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"


class PageFetcher(Protocol):
    backend: str

    def fetch(self, url: str, scrolls: int = 0) -> FetchedPage: ...


def is_wall(site: str, final_url: str) -> bool:
    walls = SITES.get(site, {}).get("walls", ())
    return any(w in (final_url or "") for w in walls)


def session_path(site: str) -> Path:
    return SESSION_DIR / f"{site}_session.json"


class PlaywrightPageFetcher:
    """One short Chromium run per page, serialized (Playwright's sync API is bound to the thread that started it,
    and research may call from worker threads). Login cookies persist in the site's session file."""

    backend = "playwright"

    def __init__(self, site: str, *, headless: bool = True, manual_login: bool = False, settle_seconds: float = 2.5,
                 scroll_pause: float = 1.5, timeout_ms: int = 45_000, state_file: Path | None = None):
        self.site = site
        self.headless = headless
        self.manual_login = manual_login
        self.settle_seconds = settle_seconds
        self.scroll_pause = scroll_pause
        self.timeout_ms = timeout_ms
        self.state_file = state_file or session_path(site)
        self._lock = threading.Lock()
        self._login_checked = False

    def logged_in(self) -> bool:
        cookie = SITES.get(self.site, {}).get("cookie")
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        return any(c.get("name") == cookie and c.get("value") for c in state.get("cookies", []))

    def login(self, timeout_seconds: int = 300) -> bool:
        """Open a visible browser on the login page and wait until the login cookie appears; save it."""
        from playwright.sync_api import sync_playwright

        info = SITES[self.site]
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False)
            context = browser.new_context(storage_state=str(self.state_file) if self.state_file.exists() else None,
                                          user_agent=USER_AGENT, viewport={"width": 1366, "height": 900})
            page = context.new_page()
            page.goto(info["login"], wait_until="domcontentloaded", timeout=self.timeout_ms)
            print(f"[{self.site}] Log in in the browser window (waiting up to {timeout_seconds // 60} min)...", flush=True)
            deadline = time.time() + timeout_seconds
            ok = False
            while time.time() < deadline:
                if any(c["name"] == info["cookie"] and c.get("value") for c in context.cookies()):
                    ok = True
                    break
                time.sleep(2)
            if ok:
                time.sleep(3)  # let the post-login redirects set the remaining cookies
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                context.storage_state(path=str(self.state_file))
                print(f"[{self.site}] Logged in; saved to {self.state_file}", flush=True)
            browser.close()
        return ok

    def fetch(self, url: str, scrolls: int = 0) -> FetchedPage:
        with self._lock:
            if self.manual_login and not self._login_checked:
                self._login_checked = True
                if not self.logged_in():
                    self.login()
            try:
                return self._fetch(url, scrolls)
            except Exception as exc:  # a broken page must not stop the research run
                return FetchedPage(url, status="error", error=f"playwright: {exc}")

    def _fetch(self, url: str, scrolls: int) -> FetchedPage:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless,
                                         args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(storage_state=str(self.state_file) if self.state_file.exists() else None,
                                          user_agent=USER_AGENT, viewport={"width": 1366, "height": 2000},
                                          locale="en-US")
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            page.wait_for_timeout(int(self.settle_seconds * 1000))
            for _ in range(scrolls):
                page.mouse.wheel(0, 2500)
                page.wait_for_timeout(int(self.scroll_pause * 1000))
            final_url, html = page.url, page.content()
            if self.state_file.exists():  # keep refreshed cookies; never create a file for a logged-out run
                context.storage_state(path=str(self.state_file))
            browser.close()
        if is_wall(self.site, final_url):
            return FetchedPage(url, html, "gated", f"{self.site} asked for a login ({final_url}). Log in once: "
                               f"python scripts/open-instagram-session.py --mode playwright --site {self.site}",
                               final_url)
        return FetchedPage(url, html, "ok" if html.strip() else "empty", "", final_url)


class BrowserActPageFetcher:
    """Pages through browser-act: a short-lived session on a saved logged-in browser (session mode), or
    stateless stealth-extract (stealth mode, public pages only)."""

    backend = "browser-act"

    def __init__(self, site: str, *, browser: str = "instagram-research", mode: str = "session",
                 session_prefix: str = "automata-social", timeout_seconds: int = 90):
        self.site = site
        self.browser = browser or "instagram-research"
        self.mode = (mode or "session").lower()
        self.session_prefix = session_prefix or "automata-social"
        self.timeout = timeout_seconds
        self._browser_id: str | None = None
        self._lock = threading.Lock()
        self._counter = itertools.count(1)

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["browser-act", *args], check=True, capture_output=True, text=True,  # nosec B603 B607
                              encoding="utf-8", errors="replace", timeout=self.timeout)

    def _resolve_browser_id(self) -> str:
        with self._lock:
            if not self._browser_id:
                browsers = json.loads(self._run("browser", "list", "--format", "json").stdout or "{}").get("browsers", [])
                match = next((b for b in browsers if self.browser in (b.get("id"), b.get("name"))), None)
                if not match:
                    names = ", ".join(f"{b.get('name')} ({b.get('id')})" for b in browsers) or "none"
                    raise LookupError(f"browser-act browser '{self.browser}' not found; saved browsers: {names}")
                self._browser_id = match["id"]
            return self._browser_id

    def fetch(self, url: str, scrolls: int = 0) -> FetchedPage:
        try:
            if self.mode == "stealth":
                html = self._run("stealth-extract", url, "--content-type", "html").stdout
                return FetchedPage(url, html, "ok" if html.strip() else "empty", "", url)
            return self._session_fetch(url, scrolls)
        except subprocess.CalledProcessError as exc:
            return FetchedPage(url, status="error", error=f"browser-act: {(exc.stderr or exc.stdout or str(exc)).strip()[:300]}")
        except (subprocess.TimeoutExpired, LookupError, OSError, ValueError) as exc:
            return FetchedPage(url, status="error", error=f"browser-act: {exc}")

    def _session_fetch(self, url: str, scrolls: int) -> FetchedPage:
        browser_id = self._resolve_browser_id()
        session = f"{self.session_prefix}-{self.site}-{next(self._counter)}"
        try:
            self._run("--session", session, "browser", "open", browser_id, url)
            self._run("--session", session, "wait", "stable")
            for _ in range(scrolls):
                self._run("--session", session, "scroll", "down", "--amount", "2500")
                time.sleep(1.5)
            final_url = self._run("--session", session, "eval", "location.href").stdout.strip().strip('"')
            html = self._run("--session", session, "get", "html").stdout
        finally:
            subprocess.run(["browser-act", "session", "close", session], capture_output=True, text=True,  # nosec B603 B607
                           timeout=self.timeout, check=False)
        if is_wall(self.site, final_url):
            return FetchedPage(url, html, "gated", f"{self.site} asked for a login in browser-act browser "
                               f"'{self.browser}'. Log in once: python scripts/open-instagram-session.py "
                               f"--mode browser-act --site {self.site}", final_url)
        return FetchedPage(url, html, "ok" if html.strip() else "empty", "", final_url)


def make_fetcher(site: str, backend: str = "playwright", *, login_mode: str = "auto", browser_act_browser: str = "",
                 browser_act_mode: str = "session", session_prefix: str = "") -> PageFetcher:
    """The fetcher for one site. backend: playwright | browser-act."""
    if backend == "browser-act":
        return BrowserActPageFetcher(site, browser=browser_act_browser or "instagram-research",
                                     mode=browser_act_mode or "session", session_prefix=session_prefix or "automata-social")
    return PlaywrightPageFetcher(site, manual_login=login_mode == "manual")


def main(argv: list[str] | None = None) -> int:
    """python -m agency_research.scrapers.page_fetch login <site>: one-time visible Playwright login."""
    import argparse

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("action", choices=["login", "status"])
    parser.add_argument("site", choices=sorted(SITES))
    args = parser.parse_args(argv)
    fetcher = PlaywrightPageFetcher(args.site)
    if args.action == "status":
        print(f"{args.site}: {'logged in' if fetcher.logged_in() else 'not logged in'} ({fetcher.state_file})")
        return 0
    return 0 if fetcher.login() else 1


if __name__ == "__main__":
    raise SystemExit(main())
