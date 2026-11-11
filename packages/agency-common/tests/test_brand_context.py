"""scripts/brand_context.py finds brand work in a drafts folder, not only Brands/<slug>.md, and never fails silently."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("brand_context", ROOT / "scripts" / "brand_context.py")
bc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bc)


def make_vault(tmp_path):
    vault = tmp_path / "vault"
    (vault / "Brands" / "rankup" / "Drafts" / "Research").mkdir(parents=True)
    (vault / "Brands" / "rankup" / "Drafts" / "Research" / "deep-research.md").write_text("x", encoding="utf-8")
    (vault / "Brands" / "maple.md").write_text("x", encoding="utf-8")
    (vault / "Research" / "Rank-Up competitors").mkdir(parents=True)
    (vault / ".stversions" / "Brands" / "rankup").mkdir(parents=True)
    root = tmp_path / "repo"
    (root / "workspace" / "rankup").mkdir(parents=True)
    return root, vault


def test_folder_without_note_is_found(tmp_path):
    root, vault = make_vault(tmp_path)
    found = bc.find_context("RankUp", root, vault)
    assert found["notes"] == []
    assert found["folders"] == [vault / "Brands" / "rankup"]
    assert found["workspace"] == [root / "workspace" / "rankup"]
    assert vault / "Research" / "Rank-Up competitors" in found["other"]
    assert not any(".stversions" in str(p) for paths in found.values() for p in paths)


def test_note_is_found(tmp_path):
    root, vault = make_vault(tmp_path)
    assert bc.find_context("maple", root, vault)["notes"] == [vault / "Brands" / "maple.md"]


def test_missing_vault_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv(bc.ENV_VAR, str(tmp_path / "unmounted"))
    try:
        bc.resolve_vault(tmp_path)
    except bc.VaultError:
        return
    raise AssertionError("an unmounted vault must raise, not fall back")


def test_empty_setting_uses_local_vault(tmp_path, monkeypatch):
    monkeypatch.setenv(bc.ENV_VAR, "")
    assert bc.resolve_vault(tmp_path)[0] == tmp_path / "workspace" / "vault"


def test_dotenv_is_read_when_not_exported(tmp_path, monkeypatch):
    monkeypatch.delenv(bc.ENV_VAR, raising=False)
    (tmp_path / ".env").write_text(f'{bc.ENV_VAR}="{tmp_path}"  \n', encoding="utf-8")
    assert bc.resolve_vault(tmp_path)[0] == tmp_path.resolve()


def test_nothing_found_exits_1(tmp_path, monkeypatch):
    _, vault = make_vault(tmp_path)
    monkeypatch.setenv(bc.ENV_VAR, str(vault))
    assert bc.main(["no-such-brand"]) == 1


def test_contents_search_finds_mentions(tmp_path, monkeypatch, capsys):
    _, vault = make_vault(tmp_path)
    (vault / "Research" / "notes.md").write_text("Call with the RANKUP founder", encoding="utf-8")
    monkeypatch.setenv(bc.ENV_VAR, str(vault))
    assert bc.main(["rankup", "--contents"]) == 0
    assert "notes.md" in capsys.readouterr().out


def test_non_ascii_names_print_on_a_windows_console(tmp_path):
    # cp1252 is the classic Windows console encoding: Hindi or emoji file names must not crash the run
    import os
    import subprocess
    import sys
    _, vault = make_vault(tmp_path)
    (vault / "Brands" / "rankup" / "Drafts" / "Research" / "रिसर्च 🚀.md").write_text("x", encoding="utf-8")
    env = {**os.environ, bc.ENV_VAR: str(vault), "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "brand_context.py"), "rankup"],
                            capture_output=True, env=env)
    assert result.returncode == 0, result.stderr.decode("cp1252", "replace")


def test_notes_tagged_with_the_brand_are_found_wherever_they_live(tmp_path):
    root, vault = make_vault(tmp_path)
    scan = vault / "Research" / "Insurance_Scan"
    scan.mkdir(parents=True)
    (scan / "phase1.md").write_text("---\ntype: research\nbrand: 'rankup'\n---\nbody", encoding="utf-8")
    (scan / "other.md").write_text("---\nbrand: maple\n---\nbody", encoding="utf-8")
    (scan / "untagged.md").write_text("no frontmatter, mentions rankup", encoding="utf-8")
    inside = vault / "Brands" / "rankup" / "Drafts" / "Research" / "tagged.md"
    inside.write_text("---\nbrand: rankup\n---\n", encoding="utf-8")

    found = bc.find_context("rankup", root, vault)

    assert found["tagged"] == [scan / "phase1.md"]  # the brand folder's own notes are not repeated
    assert bc.find_context("maple", root, vault)["tagged"] == [scan / "other.md"]
