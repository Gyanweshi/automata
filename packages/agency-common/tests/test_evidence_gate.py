from datetime import datetime, timedelta, timezone

from agency_common.decide import DecisionLog, LLMBackend
from agency_common.evidence_gate import assess_evidence, build_digest, readiness_label
from agency_common.models import (
    AdLibraryAd, AdLibraryReport, BrandProfile, CommentAnalysis, CommentCluster, CompetitorAnalysis,
    ListeningNodeReport, PlatformResearch, ResearchOutput, VisualDNA,
)

NOW = datetime(2026, 9, 24, tzinfo=timezone.utc)
FRESH = (NOW - timedelta(days=3)).isoformat()
OLD = (NOW - timedelta(days=200)).isoformat()


def brand():
    profile = BrandProfile(slug="acme", name="Acme")
    profile.writing.donts = ["no jargon"]
    profile.writing.dos = ["be plain"]
    profile.visual.avoid_visuals = ["stock smiles"]
    profile.audience.primary = "first-time buyers"
    return profile


def strong_research(stamp=FRESH):
    return ResearchOutput(
        brand_slug="acme", run_id="r1",
        platforms={"instagram": PlatformResearch(
            platform="instagram", scraped_at=stamp,
            competitors=[CompetitorAnalysis(handle=f"c{i}", platform="instagram", scrape_status="ok") for i in range(4)],
        )},
        comment_analysis=CommentAnalysis(
            analyzed_at=stamp, comment_count=120,
            clusters=[CommentCluster(category="fears", items=["a", "b", "c", "d", "e", "f"])],
        ),
        listening_node=ListeningNodeReport(scraped_at=stamp, top_questions=["q1", "q2", "q3"]),
        ad_library=AdLibraryReport(scraped_at=stamp, ads=[
            AdLibraryAd(ad_id=f"a{i}", days_running=45) for i in range(6)
        ]),
        visual_dna=VisualDNA(analyzed_at=stamp, dominant_aesthetic="clean", pattern_interrupt_opportunity="warm"),
    )


def test_strong_fresh_research_is_ready_and_acts():
    result = assess_evidence(strong_research(), brand(), now=NOW)
    assert result.evidence_readiness == "ready"
    assert {result.audience.status, result.problem.status, result.proposition.status} == {"supported"}
    assert result.decision.route == "act"
    assert "comment_analysis" in result.audience.evidence_ids
    assert result.recommended_next_step.startswith("Proceed to ideation")


def test_empty_research_is_blocked():
    empty = ResearchOutput(brand_slug="acme", run_id="r1")
    result = assess_evidence(empty, brand(), now=NOW)
    assert result.evidence_readiness == "blocked"
    assert result.audience.status == "missing"
    assert "ad_library" in result.missing_inputs
    assert result.recommended_next_step.startswith("Do not start")


def test_old_research_is_stale_not_supported():
    result = assess_evidence(strong_research(OLD), brand(), now=NOW)
    assert result.audience.status == "stale"
    assert result.evidence_readiness == "blocked"
    assert "comment_analysis" in result.stale_inputs


def test_dry_run_data_is_never_trusted():
    result = assess_evidence(strong_research(), brand(), dry_run=True, now=NOW)
    assert result.evidence_readiness == "blocked"
    assert "synthetic dry-run data" in result.irrelevant_or_unreliable
    assert result.audience.status == "unreliable"


def test_gated_competitors_are_unreliable():
    research = strong_research()
    for competitor in research.platforms["instagram"].competitors:
        competitor.scrape_status = "gated"
    research.visual_dna = None
    result = assess_evidence(research, brand(), now=NOW)
    assert result.differentiation.status == "unreliable"
    assert any("gated" in item for item in result.irrelevant_or_unreliable)


def test_borderline_evidence_asks_for_review_instead_of_acting():
    research = strong_research()
    research.comment_analysis.comment_count = 29
    research.listening_node.posts = []
    result = assess_evidence(research, brand(), now=NOW)
    assert result.audience.status == "provisional"
    assert result.audience.confidence < 0.6
    assert result.decision.route != "act"


def test_unknown_brand_means_constraints_missing():
    result = assess_evidence(strong_research(), None, now=NOW)
    assert result.constraints.status == "missing"


def test_readiness_label_contract():
    ok = dict(audience="supported", problem="supported", proposition="supported", differentiation="supported", constraints="supported")
    assert readiness_label(ok) == "ready"
    assert readiness_label({**ok, "proposition": "provisional"}) == "ready"
    assert readiness_label({**ok, "proposition": "provisional", "constraints": "provisional"}) == "provisional"
    assert readiness_label({**ok, "audience": "missing"}) == "blocked"
    assert readiness_label({**ok, "proposition": "missing", "differentiation": "stale", "constraints": "missing"}) == "blocked"


def test_llm_only_consulted_for_unsure_dimensions():
    calls = []
    llm = LLMBackend(lambda prompt: calls.append(prompt) or '{"answer": "supported"}', samples=1)
    assess_evidence(strong_research(), brand(), backend=llm, now=NOW)
    assert calls == []

    research = strong_research()
    research.comment_analysis.comment_count = 29
    research.listening_node.posts = []
    result = assess_evidence(research, brand(), backend=llm, now=NOW)
    assert calls and result.audience.status == "supported"
    assert "llm" in result.decision.source


def test_decisions_are_logged_for_later_review(tmp_path):
    log = DecisionLog(tmp_path)
    result = assess_evidence(strong_research(), brand(), log=log, now=NOW)
    names = {e["name"] for e in log.events()}
    assert names == {"research.evidence_dimension", "research.evidence_readiness"}
    log.record_human(result.decision.decision_id, "ready")
    assert log.calibration()["rules"]


def test_digest_carries_evidence_ids_but_not_raw_posts():
    digest = build_digest(strong_research(), brand(), now=NOW)
    assert digest["signals"]["long_running_ads"] == 6
    assert "raw_posts" not in str(digest)
