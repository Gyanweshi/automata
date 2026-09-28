import json

import pytest

from agency_common import housekeeping
from agency_common.housekeeping_triage import classify, triage_findings, triage_plan


@pytest.mark.parametrize(
    "path,bucket",
    [
        ("workspace/pool-people/final/pool-final-v3.jpg", "final"),
        ("workspace/purva-parkhill/amenities-2026-09-10/gym-approved-hero.png", "final"),
        ("workspace/pool-people/candidates/opt-b.png", "candidate"),
        ("workspace/gym-figure-repair/crops8k/face.png", "candidate"),
        ("workspace/pool-people/source/base.png", "input"),
        ("workspace/spa-video/prompts/shots.txt", "input"),
        ("workspace/pool-people/preview/p1.png", "preview"),
        ("workspace/pool-people/video/frames/f0001.jpg", "frame-dump"),
        ("workspace/pool-people/video/render.mp4", "media"),
        ("workspace/video-inspection/watermark-review/a.jpg", "diagnostic"),
        ("workspace/pool-people/build_final.py", "code"),
        ("workspace/maple/research/facts.json", "data"),
        ("workspace/city-night/shot.png", "image"),
        ("workspace/autopilot-offices/storyboards/x/session.db-wal", "tool-state"),
        ("clipfarming-and-distribution.md", "non-workspace"),
    ],
)
def test_classify(path, bucket):
    assert classify(path) == bucket


def test_browser_profile_named_final_is_not_promoted():
    path = "workspace/autopilot-offices/storyboards/v7/render-profile-final/Local State"
    assert classify(path) == "browser-profile"


def test_triage_only_includes_review_findings_and_never_quarantines_unknowns():
    findings = [
        {"scope": "repo", "path": ".env", "decision": "keep-repo", "size": 1},
        {"scope": "repo", "path": "workspace/x/y/mystery", "decision": "review", "size": 5},
        {"scope": "vault", "path": "Research/n.md", "decision": "review", "size": 9},
    ]
    rows = triage_findings(findings)
    assert [r["path"] for r in rows] == ["workspace/x/y/mystery", "Research/n.md"]
    assert rows[0]["action"] == "review"
    assert rows[1]["project"] == "(vault)"


def test_cli_triage_writes_reports_and_does_not_touch_sources(tmp_path):
    victim = tmp_path / "keep.png"
    victim.write_bytes(b"x")
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"findings": [
        {"scope": "repo", "path": "workspace/p/final/a.png", "decision": "review", "size": 2_000_000},
    ]}), encoding="utf-8")
    report, rows = tmp_path / "t.md", tmp_path / "t.json"

    code = housekeeping.main([
        "triage", "--plan", str(plan), "--report", str(report), "--json", str(rows),
    ])

    assert code == 0
    assert "workspace/p/final/a.png" in report.read_text(encoding="utf-8")
    assert json.loads(rows.read_text(encoding="utf-8"))[0]["action"] == "promote"
    assert victim.exists()
    assert triage_plan(str(plan))[0][0]["bucket"] == "final"


def test_advice_is_advisory_and_never_changes_the_rules_action():
    from agency_common.decide import LLMBackend
    from agency_common.housekeeping_triage import advise_rows, render_markdown

    rows = triage_findings([
        {"scope": "repo", "path": "workspace/x/y/mystery", "decision": "review", "size": 5},
        {"scope": "repo", "path": "workspace/p/final/a.png", "decision": "review", "size": 5},
    ])
    backend = LLMBackend(lambda prompt: '{"answer": "quarantine-ok"}', samples=1)

    advise_rows(rows, backend)

    mystery, final = rows
    assert mystery["action"] == "review" and mystery["suggested"] == "quarantine-ok"
    assert mystery["route"] == "act"
    assert "suggested" not in final and final["action"] == "promote"
    assert "Model suggestions" in render_markdown(rows, "plan.json")


def test_advice_limit_bounds_llm_calls():
    from agency_common.decide import LLMBackend
    from agency_common.housekeeping_triage import advise_rows

    calls = []
    rows = triage_findings(
        [{"scope": "repo", "path": f"workspace/x/y/m{i}", "decision": "review", "size": 1} for i in range(5)]
    )
    advise_rows(rows, LLMBackend(lambda p: calls.append(p) or '{"answer": "review"}', samples=1), limit=2)
    assert len(calls) == 2
