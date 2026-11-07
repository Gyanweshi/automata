"""Decision rules of the quarterly dependency routine (scripts/deps_update.py); no network."""
import datetime as dt
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("deps_update", ROOT / "scripts" / "deps_update.py")
upd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upd)


def test_major_line_treats_pre_1_0_minors_as_breaking():
    assert upd.major_line("1.4.2") == upd.major_line("1.9.0")
    assert upd.major_line("1.9.0") != upd.major_line("2.0.0")
    assert upd.major_line("0.21.4") != upd.major_line("0.22.0")  # 0.x: a minor bump can break
    assert upd.major_line("0.0.73") == upd.major_line("0.0.84")


def test_newest_before_respects_cooldown_and_skips_prereleases():
    cutoff = dt.datetime(2026, 10, 24, tzinfo=dt.timezone.utc)
    candidates = {
        "1.2.0": "2026-09-01T00:00:00Z",
        "1.3.0": "2026-10-20T00:00:00Z",
        "1.4.0": "2026-11-05T00:00:00Z",       # too new
        "1.5.0-beta.1": "2026-09-02T00:00:00Z",  # prerelease
    }
    assert upd.newest_before(candidates, cutoff) == "1.3.0"
    assert upd.newest_before({"2.0.0": "2026-11-06T00:00:00Z"}, cutoff) is None


def test_compare_separates_upgrades_from_downgrades():
    upgraded, downgraded = upd.compare({"a": "1.0", "b": "2.1", "c": "3.0"}, {"a": "1.1", "b": "2.0", "c": "3.0"})
    assert upgraded == ["a 1.0 -> 1.1"]
    assert downgraded == ["b 2.1 -> 2.0"]


def test_prerelease_detection():
    assert upd.is_prerelease("0.1.0-canary.3") and upd.is_prerelease("2.0.0rc1") and upd.is_prerelease("1.0.0b2")
    assert not upd.is_prerelease("1.6.2") and not upd.is_prerelease("2.9.0.post0")


def test_locked_upload_times_reads_uv_lock(tmp_path):
    lock = tmp_path / "uv.lock"
    lock.write_text('version = 1\n[[package]]\nname = "x"\nversion = "1.0"\n'
                    'sdist = { url = "u", upload-time = "2026-11-06T14:02:30.924Z" }\n'
                    'wheels = [{ url = "w", upload-time = "2026-11-01T00:00:00Z" }]\n', encoding="utf-8")
    assert upd.locked_upload_times(lock)["x"] == dt.datetime(2026, 11, 6, 14, 2, 30, 924000, tzinfo=dt.timezone.utc)
