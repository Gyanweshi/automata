"""Tests for scripts/deps.py and dependencies.toml; they run on Linux and Windows CI alike."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("deps", ROOT / "scripts" / "deps.py")
deps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deps)

KINDS = {"runtime", "python-lock", "node-lock", "mcp-npm", "mcp-uvx", "mcp-remote", "github-release", "uv-tool",
         "system", "app", "browser", "external-skills", "ci-action"}


@pytest.fixture(scope="module")
def manifest():
    return deps.load(ROOT / "dependencies.toml")


def test_manifest_entries_are_complete(manifest):
    ids = [d["id"] for d in manifest["dependency"]]
    assert len(ids) == len(set(ids)), "duplicate ids"
    for dep in manifest["dependency"]:
        for field in ("id", "name", "kind", "category", "purpose", "used_by", "update", "on_break"):
            assert dep.get(field), f"{dep.get('id')} is missing {field}"
        assert dep["kind"] in KINDS, f"{dep['id']} has unknown kind {dep['kind']}"
        if dep["kind"] == "github-release":
            assert dep["id"] in manifest["releases"], f"{dep['id']} needs a [releases.{dep['id']}] table"


def test_install_commands_are_runnable_text(manifest):
    """Notes belong in install_note: anything in `install` (except manual:) is passed to the shell."""
    for dep in manifest["dependency"]:
        for os_name, command in (dep.get("install") or {}).items():
            if not command.startswith("manual:"):
                assert "   (" not in command and not command.rstrip().endswith(")"), f"{dep['id']}.{os_name}: {command}"


def test_every_pin_agrees_across_files(manifest):
    problems = {d["id"]: deps.pin_problems(d, ROOT) for d in manifest["dependency"]}
    assert {k: v for k, v in problems.items() if v} == {}


def test_pin_problems_flags_a_second_version(tmp_path):
    (tmp_path / "a.json").write_text('"pkg@1.0" "pkg@2.0"', encoding="utf-8")
    dep = {"id": "x", "pin": "1.0", "pin_files": [{"file": "a.json", "pattern": "pkg@{version}"}]}
    assert deps.pin_problems(dep, tmp_path) == ["a.json also has pkg@2.0"]


def test_set_pin_rewrites_configs_and_manifest(tmp_path):
    (tmp_path / "a.json").write_text('{"args": ["-y", "pkg@1.0"]}', encoding="utf-8")
    (tmp_path / "b.json").write_text('{"args": ["pkg@1.0", "--flag"]}', encoding="utf-8")
    manifest = tmp_path / "dependencies.toml"
    manifest.write_text(
        '[[dependency]]\nid = "x"\npin = "1.0"\n'
        'pin_files = [{ file = "a.json", pattern = "pkg@{version}" }, { file = "b.json", pattern = "pkg@{version}" }]\n\n'
        '[[dependency]]\nid = "y"\npin = "1.0"\n',
        encoding="utf-8",
    )
    changed = deps.set_pin("x", "1.1", manifest, tmp_path)
    assert changed == ["a.json", "b.json", "dependencies.toml"]
    assert "pkg@1.1" in (tmp_path / "a.json").read_text(encoding="utf-8")
    updated = deps.load(manifest)
    assert [d["pin"] for d in updated["dependency"]] == ["1.1", "1.0"]  # only x moved


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [("Linux", "x86_64", "linux-x86_64"), ("Windows", "AMD64", "windows-x86_64"), ("Darwin", "arm64", "macos-arm64")],
)
def test_detect_platform(system, machine, expected):
    assert deps.detect_platform(system, machine) == expected


def test_pick_latest_release_skips_website_builds():
    releases = [
        {"tag_name": "web-ad67361", "assets": [{"name": "raea_shape_web.js"}]},
        {"tag_name": "v0.3", "assets": [{"name": "raea-0.3-macos-arm64.tar.gz"}]},
        {"tag_name": "v0.2", "assets": [{"name": "raea-0.2-linux-x86_64.tar.gz"}]},
    ]
    assert deps.pick_latest_release(releases, "raea-{version}-linux-x86_64.tar.gz") == "0.2"
    assert deps.pick_latest_release(releases[:1], "raea-{version}-linux-x86_64.tar.gz") is None


def test_zip_extract_refuses_paths_outside_dest(tmp_path):
    import zipfile

    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("../escape.txt", "x")
    with pytest.raises(SystemExit, match="unsafe path"):
        deps.extract(bad, tmp_path / "out")
    assert not (tmp_path / "escape.txt").exists()

    good = tmp_path / "good.zip"
    with zipfile.ZipFile(good, "w") as zf:
        zf.writestr("raea/bin/raea.exe", "x")
    deps.extract(good, tmp_path / "out")
    assert (tmp_path / "out" / "raea" / "bin" / "raea.exe").exists()


def test_install_command_prefers_os_then_all():
    dep = {"pin": "1.2", "install": {"linux": "apt x", "all": "tool=={version}"}}
    assert deps.install_command(dep, "linux") == "apt x"
    assert deps.install_command(dep, "windows") == "tool==1.2"


def test_raea_has_a_build_for_both_machines(manifest):
    assets = manifest["releases"]["raea"]["assets"]
    assert {"linux-x86_64", "windows-x86_64"} <= set(assets)


def test_platform_pin_overrides_the_pin_only_for_that_platform():
    dep = {"id": "tool", "pin": "2.0"}
    release = {"platform_pins": {"windows-x86_64": "1.9"}}
    assert deps.pin_for(dep, release, "windows-x86_64") == "1.9"
    assert deps.pin_for(dep, release, "linux-x86_64") == "2.0"
    assert deps.pin_for(dep, None, "linux-x86_64") == "2.0"


def test_platform_pins_name_known_platforms(manifest):
    for dep_id, release in manifest.get("releases", {}).items():
        for plat in (release.get("platform_pins") or {}):
            assert plat in release["assets"], f"{dep_id}: platform_pins names unknown platform {plat}"


def test_machine_roles_parse_all_none_and_lists(monkeypatch):
    monkeypatch.setenv("AUTOMATA_ROLES", "video, research")
    assert deps.machine_roles() == {"video", "research"}
    monkeypatch.setenv("AUTOMATA_ROLES", "all")
    assert deps.machine_roles() == set(deps.ALL_ROLES)
    monkeypatch.setenv("AUTOMATA_ROLES", "")
    assert deps.machine_roles() == set()


def test_needed_here_keeps_required_deps_and_filters_role_tools():
    assert deps.needed_here({"id": "uv", "required": True}, set())
    assert deps.needed_here({"id": "x", "roles": ["video"]}, {"video"})
    assert not deps.needed_here({"id": "gimp", "roles": ["images"]}, {"video"})
    assert deps.needed_here({"id": "playwright-mcp"}, set())  # untagged optional deps stay visible


def test_every_role_tag_is_a_known_role(manifest):
    for dep in manifest["dependency"]:
        assert set(dep.get("roles", [])) <= set(deps.ALL_ROLES), dep["id"]
        assert not (dep.get("required") and dep.get("roles")), f"{dep['id']}: required deps need no role"
