"""The dependency update routine (`python scripts/deps.py update`), run quarterly by CI or by hand on any OS.

Safety rules, in order:
  * cool-down: only versions published at least N days ago (default 14) are considered;
  * no major jumps: a new major version (or a 0.x minor, where minors break) is reported for review, never applied;
  * MCP servers: started and handshaken before and after; a bump that removes a tool is reverted and reported;
  * tools that need an app or a GPU to test (GIMP, Blender, raea) are reported, never bumped automatically;
  * lockfiles: Python and Node libraries move within the ranges already declared, never downgrade.
Writes a Markdown report; changes stay in the working tree for tests and review (CI pushes them to a branch).
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import re
import shutil
import subprocess  # nosec B404 - runs uv/npm and the repo's own scripts
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
NODE_PACKAGES = (".", "agents/automata_core/ig-research")
REPORT_ONLY = {"gimp-mcp", "blender-mcp", "raea"}  # need GIMP / Blender / a GPU to verify


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deps = _load("deps_core", "deps.py")


# ---------------------------------------------------------------- versions

def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in re.findall(r"\d+", version))


def is_prerelease(version: str) -> bool:
    return bool(re.search(r"(a|b|rc|dev|alpha|beta|canary|pre|next)\d*", version.split("+")[0].lower())) or "-" in version


def major_line(version: str) -> tuple[int, ...]:
    """Versions on the same line can be bumped automatically: same major, or same 0.minor before 1.0."""
    parts = version_key(version) + (0, 0)
    return (0, parts[1]) if parts[0] == 0 else (parts[0],)


def newest_before(candidates: dict[str, str], cutoff: dt.datetime) -> str | None:
    """Newest stable version published on or before the cutoff. candidates: version -> ISO publish time."""
    eligible = []
    for version, published in candidates.items():
        if is_prerelease(version) or not published:
            continue
        when = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
        if when <= cutoff:
            eligible.append(version)
    return max(eligible, key=version_key) if eligible else None


def upstream_versions(upstream: str) -> dict[str, str]:
    source, _, name = upstream.partition(":")
    if source == "npm":
        meta = json.loads(deps.fetch(f"https://registry.npmjs.org/{name}"))
        return {v: meta.get("time", {}).get(v, "") for v in meta.get("versions", {})}
    if source == "pypi":
        meta = json.loads(deps.fetch(f"https://pypi.org/pypi/{name}/json"))
        return {v: next((f["upload_time_iso_8601"] for f in files if not f.get("yanked")), "")
                for v, files in meta.get("releases", {}).items() if files}
    return {}


# ---------------------------------------------------------------- lockfiles

def uv_lock_versions(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return {p["name"]: p.get("version", "") for p in data.get("package", []) if p.get("version")}


def npm_lock_versions(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    packages = json.loads(path.read_text(encoding="utf-8")).get("packages", {})
    return {k.split("node_modules/")[-1]: v.get("version", "") for k, v in packages.items() if k and v.get("version")}


def locked_upload_times(path: Path) -> dict[str, dt.datetime]:
    """Newest upload time of each locked package's files (uv records it per sdist/wheel)."""
    if not path.exists():
        return {}
    times = {}
    for package in tomllib.loads(path.read_text(encoding="utf-8")).get("package", []):
        stamps = [f.get("upload-time") for f in [package.get("sdist") or {}, *(package.get("wheels") or [])]]
        stamps = [dt.datetime.fromisoformat(t.replace("Z", "+00:00")) for t in stamps if t]
        if stamps:
            times[package["name"]] = max(stamps)
    return times


def compare(before: dict[str, str], after: dict[str, str]) -> tuple[list[str], list[str]]:
    upgraded, downgraded = [], []
    for name, new in sorted(after.items()):
        old = before.get(name)
        if old and old != new:
            (upgraded if version_key(new) > version_key(old) else downgraded).append(f"{name} {old} -> {new}")
    return upgraded, downgraded


def run(command: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
    exe = shutil.which(command[0]) or command[0]
    return subprocess.run([exe, *command[1:]], cwd=cwd, capture_output=True, text=True,  # nosec B603
                          encoding="utf-8", errors="replace")


def update_python(cutoff: dt.datetime, notes: list[str], review: list[str]) -> list[str]:
    """Minor/patch upgrades within the declared ranges; major jumps are listed for review, never applied."""
    lock = ROOT / "uv.lock"
    before = uv_lock_versions(lock)
    original = lock.read_text(encoding="utf-8")
    stamp = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    # A package already locked at a version newer than the cut-off (a recent security bump) keeps its own date as
    # its cut-off: never downgraded, never pushed further.
    window = ["--exclude-newer", stamp]
    for name, when in locked_upload_times(lock).items():
        if when > cutoff:
            window += ["--exclude-newer-package", f"{name}={(when + dt.timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%SZ')}"]

    def fail(message: str) -> list[str]:
        lock.write_text(original, encoding="utf-8")
        notes.append(message)
        return []

    trial = run(["uv", "lock", "--upgrade", *window])  # what would change?
    if trial.returncode:
        return fail(f"Python: `uv lock --upgrade` failed, lock unchanged:\n```\n{trial.stderr[-1500:]}\n```")
    after = uv_lock_versions(lock)
    lock.write_text(original, encoding="utf-8")
    safe, majors = [], []
    for name, new in after.items():
        old = before.get(name)
        if old and new != old and version_key(new) > version_key(old):
            if major_line(new) == major_line(old):
                safe.append(name)
            else:
                majors.append(name)
                review.append(f"Python `{name}` {old} -> {new} is a major change (allowed by the declared range): "
                              f"review, then `uv lock --upgrade-package {name}`")
    if not safe:
        return []
    applied = run(["uv", "lock", *[a for n in safe for a in ("--upgrade-package", n)], *window])
    if applied.returncode:
        return fail(f"Python: applying {len(safe)} upgrades failed, lock unchanged:\n```\n{applied.stderr[-1500:]}\n```")
    upgraded, downgraded = compare(before, uv_lock_versions(lock))
    sneaked = [c for c in upgraded if c.split(" ")[0] in majors]
    if downgraded or sneaked:
        return fail("Python: held back, the minor upgrades would also "
                    + ("downgrade " + ", ".join(downgraded[:6]) if downgraded else "")
                    + ("pull in major changes " + ", ".join(sneaked[:6]) if sneaked else ""))
    return upgraded


def npm_published(name: str, version: str) -> dt.datetime | None:
    try:
        when = json.loads(deps.fetch(f"https://registry.npmjs.org/{name}")).get("time", {}).get(version)
    except Exception:  # registry hiccup: treat as unknown (too new), so the update is held back
        return None
    return dt.datetime.fromisoformat(when.replace("Z", "+00:00")) if when else None


def update_node(cutoff: dt.datetime, notes: list[str]) -> list[str]:
    """npm cannot exempt one package from --before, so: update within the declared ranges, then hold the whole
    update back if any changed package is younger than the cool-down (it is picked up next run)."""
    changes = []
    for folder in NODE_PACKAGES:
        directory = ROOT / folder
        lock = directory / "package-lock.json"
        if not lock.exists():
            continue
        before, original = npm_lock_versions(lock), lock.read_text(encoding="utf-8")
        result = run(["npm", "update", "--no-audit", "--no-fund"], cwd=directory)

        def restore(reason: str) -> None:
            lock.write_text(original, encoding="utf-8")
            run(["npm", "ci", "--no-audit", "--no-fund"], cwd=directory)
            notes.append(f"Node ({folder}): held back, {reason}")

        if result.returncode:
            restore(f"`npm update` failed: {result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'no output'}")
            continue
        upgraded, downgraded = compare(before, npm_lock_versions(lock))
        if downgraded:
            restore(f"it would downgrade {', '.join(downgraded[:6])}")
            continue
        if not upgraded:  # npm may still rewrite metadata (license fields): keep the original, no churn
            lock.write_text(original, encoding="utf-8")
            continue
        too_new = []
        for change in upgraded:
            name, _, versions = change.partition(" ")
            new = versions.split("-> ")[-1]
            published = npm_published(name, new)
            if published is None or published > cutoff:
                too_new.append(f"{name} {new}")
        if too_new:
            restore(f"younger than the cool-down: {', '.join(too_new[:8])} (retried next run)")
            continue
        changes += [f"{folder}: {c}" for c in upgraded]
    return changes


# ---------------------------------------------------------------- pinned tools

def mcp_server_for(dep: dict) -> str | None:
    """Name of the stdio MCP server whose config pins this dependency."""
    patterns = [e.get("pattern", "").format(version=dep.get("pin", "")) for e in dep.get("pin_files", [])]
    for config in [ROOT / ".mcp.json", *sorted((ROOT / "mcp" / "agents").glob("*.json"))]:
        for name, server in json.loads(config.read_text(encoding="utf-8")).get("mcpServers", {}).items():
            args = " ".join(server.get("args", []))
            if "command" in server and any(p and p in args for p in patterns):
                return name
    return None


def update_pins(manifest: dict, cutoff: dt.datetime, smoke: bool) -> tuple[list[str], list[str]]:
    applied, review = [], []
    smoke_mod = _load("mcp_smoke", "mcp-smoke.py") if smoke else None
    for dep in manifest["dependency"]:
        pin, upstream = dep.get("pin", ""), dep.get("upstream", "")
        if not pin or not upstream.startswith(("npm:", "pypi:")):
            if dep["id"] in REPORT_ONLY and upstream:
                review.append(f"`{dep['id']}`: check by hand (`deps.py outdated`); needs its app or a GPU to verify")
            continue
        try:
            latest = newest_before(upstream_versions(upstream), cutoff)
        except Exception as exc:  # registry outage: report, don't fail the routine
            review.append(f"`{dep['id']}`: could not read {upstream} ({exc.__class__.__name__})")
            continue
        if not latest or version_key(latest) <= version_key(pin):
            continue
        if dep["id"] in REPORT_ONLY:
            review.append(f"`{dep['id']}` {pin} -> {latest} available: verify with its app, then `deps.py set-pin`")
            continue
        if major_line(latest) != major_line(pin):
            review.append(f"`{dep['id']}` {pin} -> {latest} is a major change: review the changelog, update by hand")
            continue
        server = mcp_server_for(dep) if dep["kind"].startswith("mcp") else None
        before_tools = None
        if server and smoke_mod:
            try:
                before_tools = set(smoke_mod.list_tools(smoke_mod.find_server(server), 300))
            except (RuntimeError, SystemExit) as exc:
                review.append(f"`{dep['id']}`: current version did not start for the smoke test ({exc}); not bumped")
                continue
        deps.set_pin(dep["id"], latest)
        if server and smoke_mod and before_tools is not None:
            try:
                after_tools = set(smoke_mod.list_tools(smoke_mod.find_server(server), 300))
            except (RuntimeError, SystemExit) as exc:
                deps.set_pin(dep["id"], pin)
                review.append(f"`{dep['id']}` {pin} -> {latest}: new version did not start ({exc}); reverted")
                continue
            removed = sorted(before_tools - after_tools)
            if removed:
                deps.set_pin(dep["id"], pin)
                review.append(f"`{dep['id']}` {pin} -> {latest} removes tools {', '.join(removed)}; reverted, review by hand")
                continue
            added = sorted(after_tools - before_tools)
            applied.append(f"`{dep['id']}` {pin} -> {latest} (MCP smoke test passed"
                           + (f"; new tools: {', '.join(added)}" if added else "") + ")")
        else:
            applied.append(f"`{dep['id']}` {pin} -> {latest}" + ("" if not server else " (smoke test skipped)"))
    return applied, review


# ---------------------------------------------------------------- entry point

def update(cooldown_days: int = 14, smoke: bool = True, report: Path | None = None) -> int:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=cooldown_days)
    notes: list[str] = []
    python_review: list[str] = []
    python_changes = update_python(cutoff, notes, python_review)
    node_changes = update_node(cutoff, notes)
    applied, review = update_pins(deps.load(), cutoff, smoke)
    review += python_review
    deps.write_docs(deps.load())

    lines = [f"# Dependency update {dt.date.today().isoformat()}", "",
             f"Cool-down: only versions published before {cutoff.date().isoformat()} ({cooldown_days} days).", "",
             f"## Pinned tools and MCP servers: {len(applied)} updated", *(f"- {a}" for a in applied or ["none"]), "",
             f"## Needs a person: {len(review)}", *(f"- {r}" for r in review or ["nothing"]), "",
             f"## Python libraries (uv.lock): {len(python_changes)} upgraded",
             *(f"- {c}" for c in python_changes[:60] or ["none"]),
             *([f"- ... and {len(python_changes) - 60} more"] if len(python_changes) > 60 else []), "",
             f"## Node libraries (package-lock.json): {len(node_changes)} upgraded",
             *(f"- {c}" for c in node_changes[:40] or ["none"]), ""]
    if notes:
        lines += ["## Notes", *(f"- {n}" for n in notes), ""]
    lines += ["## Before merging",
              "CI on the branch ran the full checks and tests on Ubuntu and Windows and the security audit. After merging,",
              "every machine updates itself on its next `git pull` (post-pull hook re-runs the setup)."]
    text = "\n".join(lines) + "\n"
    if report:
        report.write_text(text, encoding="utf-8")
    print(text)
    return 0
