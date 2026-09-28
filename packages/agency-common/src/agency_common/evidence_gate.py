"""Evidence-readiness gate for research output, built on the shared decision layer.

Reads a finished `ResearchOutput` and answers, per dimension (audience, problem, proposition,
differentiation, constraints), whether the evidence is supported / provisional / stale /
unreliable / missing, then whether downstream work is blocked / provisional / ready.
Rules run first and cost nothing. Pass an LLM backend to `assess_evidence` to second-guess
borderline dimensions. The result gates and routes; a person confirms anything not `act`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .decide import (
    Backend, CascadeBackend, Choice, DecisionLog, RulesBackend, Thresholds, decide, ROUTE_ACT,
)
from .models import (
    BrandProfile, EvidenceDecision, EvidenceDimension, EvidenceReadiness, ResearchOutput,
)

DIMENSIONS = ("audience", "problem", "proposition", "differentiation", "constraints")
STATUS_OPTIONS = {
    "supported": "several independent, current, reliable sources back it",
    "provisional": "some support, but thin: usable only as a labelled hypothesis",
    "stale": "the only support is out of date",
    "unreliable": "the sources failed, are synthetic, or are not relevant",
    "missing": "no evidence gathered",
}
READINESS_OPTIONS = {
    "blocked": "dependent concept and execution work must stop",
    "provisional": "proceed only with labelled hypotheses and tests",
    "ready": "the next decision has adequate support",
}
STALE_AFTER_DAYS = 90
LONG_RUNNING_AD_DAYS = 30
FAILED_SCRAPES = {"gated", "error", "empty"}
DIMENSION_THRESHOLDS = Thresholds(act=0.6, review=0.3)
READINESS_THRESHOLDS = Thresholds(act=0.6, review=0.3)

_DIMENSION_INSTRUCTIONS = {
    "audience": "Is there evidence about who the audience is and what they say and do?",
    "problem": "Is there evidence of the audience's real problems, fears, or questions?",
    "proposition": "Is there evidence about which offers, hooks, or angles earn attention or money?",
    "differentiation": "Is there evidence of how competitors look and sound, and where a gap exists?",
    "constraints": "Are the brand's voice, visual, and claim constraints known?",
}


def _age_days(stamp: str, now: datetime) -> int | None:
    try:
        moment = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return (now - moment).days


def build_digest(
    research: ResearchOutput, brand: BrandProfile | None = None, *, dry_run: bool = False, now: datetime | None = None,
) -> dict[str, Any]:
    """Compact, model-readable summary of what the research run actually gathered."""
    now = now or datetime.now(timezone.utc)
    evidence_ids: dict[str, list[str]] = {name: [] for name in DIMENSIONS}
    stale: list[str] = []
    stale_dims: set[str] = set()
    unreliable: list[str] = []

    def stamped(section: str, stamp: str, *dimensions: str) -> bool:
        age = _age_days(stamp, now)
        if age is not None and age > STALE_AFTER_DAYS:
            stale.append(section)
            stale_dims.update(dimensions)
            return False
        return True

    ca = research.comment_analysis
    problem_items = 0
    comments_fresh = 0
    if ca and stamped("comment_analysis", ca.analyzed_at, "audience", "problem"):
        comments_fresh = ca.comment_count
        problem_items += sum(
            len(c.items) for c in ca.clusters if c.category in {"fears", "recurring_questions", "knowledge_gaps"}
        )
        evidence_ids["audience"].append("comment_analysis")
        if problem_items:
            evidence_ids["problem"].append("comment_analysis")

    ln = research.listening_node
    listening_posts = 0
    if ln and stamped("listening_node", ln.scraped_at, "audience", "problem"):
        listening_posts = len(ln.posts)
        problem_items += len(ln.top_questions)
        if ln.posts:
            evidence_ids["audience"].append("listening_node")
        if ln.top_questions:
            evidence_ids["problem"].append("listening_node")

    ads = research.ad_library
    long_running = 0
    if ads and stamped("ad_library", ads.scraped_at, "proposition"):
        long_running = sum(1 for ad in ads.ads if ad.days_running >= LONG_RUNNING_AD_DAYS)
        evidence_ids["proposition"] += [f"ad:{ad.ad_id}" for ad in ads.ads if ad.days_running >= LONG_RUNNING_AD_DAYS and ad.ad_id]

    usable_competitors = failed_competitors = 0
    fresh_platforms = 0
    for platform, data in research.platforms.items():
        if not stamped(f"platform:{platform}", data.scraped_at, "differentiation"):
            continue
        fresh_platforms += 1
        for competitor in data.competitors:
            if competitor.scrape_status in FAILED_SCRAPES:
                failed_competitors += 1
                unreliable.append(f"{platform}:{competitor.handle} ({competitor.scrape_status})")
            else:
                usable_competitors += 1
                evidence_ids["differentiation"].append(f"competitor:{platform}:{competitor.handle}")
    vd = research.visual_dna
    has_visual_dna = bool(
        vd and (vd.pattern_interrupt_opportunity or vd.dominant_aesthetic)
        and stamped("visual_dna", vd.analyzed_at, "differentiation")
    )
    if has_visual_dna:
        evidence_ids["differentiation"].append("visual_dna")

    brand_constraints = 0
    if brand:
        brand_constraints = sum(bool(x) for x in (
            brand.writing.dos, brand.writing.donts, brand.writing.banned_constructions,
            brand.visual.avoid_visuals, brand.audience.primary, brand.vocabulary.avoid_words,
        ))
        if brand_constraints:
            evidence_ids["constraints"].append("brand_profile")

    return {
        "brand": brand.slug if brand else research.brand_slug,
        "signals": {
            "synthetic": dry_run,
            "comment_count": comments_fresh,
            "listening_posts": listening_posts,
            "problem_items": problem_items,
            "long_running_ads": long_running,
            "usable_competitors": usable_competitors,
            "failed_competitors": failed_competitors,
            "fresh_platforms": fresh_platforms,
            "has_visual_dna": has_visual_dna,
            "brand_constraints": brand_constraints,
            "brand_known": brand is not None,
        },
        "evidence_ids": evidence_ids,
        "stale_inputs": sorted(set(stale)),
        "stale_dimensions": sorted(stale_dims),
        "unreliable_inputs": unreliable,
        "summary": research.summary[:1500],
    }


def _graded(count: int, needed: int) -> dict[str, float]:
    """Soft support level: clearly none, clearly enough, or thin (less sure the nearer the line)."""
    if count <= 0:
        return {"missing": 0.9, "provisional": 0.1}
    if count >= 2 * needed:
        return {"supported": 0.95, "provisional": 0.05}
    if count >= needed:
        return {"supported": 0.8, "provisional": 0.2}
    ratio = count / needed
    provisional = 0.5 + 0.4 * (1 - ratio)
    rest = 1 - provisional
    return {"provisional": provisional, "supported": rest * ratio, "missing": rest * (1 - ratio)}


def _with_context(digest: Mapping[str, Any], dimension: str, base: dict[str, float]) -> dict[str, float]:
    sig = digest["signals"]
    if sig["synthetic"]:
        return {"unreliable": 1.0}
    if dimension in digest["stale_dimensions"] and base.get("missing", 0) > 0.5:
        return {"stale": 0.85, "missing": 0.15}
    return base


def _audience(d: Mapping[str, Any]) -> dict[str, float]:
    return _with_context(d, "audience", _graded(d["signals"]["comment_count"] + d["signals"]["listening_posts"], 30))


def _problem(d: Mapping[str, Any]) -> dict[str, float]:
    return _with_context(d, "problem", _graded(d["signals"]["problem_items"], 3))


def _proposition(d: Mapping[str, Any]) -> dict[str, float]:
    return _with_context(d, "proposition", _graded(d["signals"]["long_running_ads"], 3))


def _differentiation(d: Mapping[str, Any]) -> dict[str, float]:
    sig = d["signals"]
    if not sig["synthetic"] and sig["usable_competitors"] == 0 and sig["failed_competitors"] > 0:
        return {"unreliable": 0.9, "missing": 0.1}
    count = sig["usable_competitors"] + (2 if sig["has_visual_dna"] else 0)
    return _with_context(d, "differentiation", _graded(count, 4))


def _constraints(d: Mapping[str, Any]) -> dict[str, float]:
    sig = d["signals"]
    if not sig["brand_known"]:
        return {"missing": 0.9, "provisional": 0.1}
    return _graded(sig["brand_constraints"], 3)


DIMENSION_RULES = {
    "audience": _audience, "problem": _problem, "proposition": _proposition,
    "differentiation": _differentiation, "constraints": _constraints,
}


def readiness_label(statuses: Mapping[str, str]) -> str:
    """Contract: blocked stops downstream work; ready needs no more than one thin dimension."""
    bad = {"missing", "unreliable", "stale"}
    weak = [name for name, status in statuses.items() if status in bad]
    if statuses["audience"] in bad or statuses["problem"] in bad or len(weak) >= 3:
        return "blocked"
    if not weak and sum(status != "supported" for status in statuses.values()) <= 1:
        return "ready"
    return "provisional"


def _next_step(label: str, statuses: Mapping[str, str]) -> str:
    gaps = [name for name, status in statuses.items() if status != "supported"]
    if label == "ready":
        return "Proceed to ideation." + (f" Watch thin area: {', '.join(gaps)}." if gaps else "")
    if label == "provisional":
        return f"Proceed only with labelled hypotheses and tests. Strengthen: {', '.join(gaps)}."
    return f"Do not start concept or execution work. Gather or repair evidence for: {', '.join(gaps)}."


def assess_evidence(
    research: ResearchOutput,
    brand: BrandProfile | None = None,
    *,
    backend: Backend | None = None,
    dry_run: bool = False,
    log: DecisionLog | None = None,
    now: datetime | None = None,
) -> EvidenceReadiness:
    """Return the evidence-readiness handoff for a research run.

    `backend` (for example `LLMBackend`) is consulted only where the rules are not confident.
    """
    digest = build_digest(research, brand, dry_run=dry_run, now=now)
    rules = RulesBackend({name: DIMENSION_RULES[name] for name in DIMENSIONS})
    engine: Backend = CascadeBackend([rules, backend], min_margin=DIMENSION_THRESHOLDS.act) if backend else rules

    questions = [
        Choice(name, STATUS_OPTIONS, _DIMENSION_INSTRUCTIONS[name],
               "Judge only from the state's signals and evidence_ids. Staleness and failed sources count against support.")
        for name in DIMENSIONS
    ]
    decisions = decide(digest, questions, engine, thresholds=DIMENSION_THRESHOLDS, log=log, name="research.evidence_dimension")
    statuses = {name: decisions[name].answer for name in DIMENSIONS}

    label = readiness_label(statuses)
    floor = min(decision.confidence for decision in decisions.values())
    p = (floor + 0.5) / 1.5
    others = [option for option in READINESS_OPTIONS if option != label]
    gate_probs = {label: p, **{option: (1 - p) / len(others) for option in others}}
    gate = decide(
        digest, [Choice("readiness", READINESS_OPTIONS, "Can downstream work start on this evidence?")],
        RulesBackend({"readiness": lambda _state: gate_probs}), thresholds=READINESS_THRESHOLDS, log=log,
        name="research.evidence_readiness",
    )["readiness"]
    sources = "+".join(sorted({d.source for d in decisions.values()}))

    weak_sections = {
        "audience": "comment_analysis or listening_node", "problem": "comment_analysis or listening_node",
        "proposition": "ad_library", "differentiation": "competitor scrape or visual_dna",
        "constraints": "brand profile writing rules",
    }
    notes = {
        name: f"{decisions[name].source}, confidence {decisions[name].confidence:.2f}"
        + ("; needs review" if decisions[name].route != ROUTE_ACT else "")
        for name in DIMENSIONS
    }
    return EvidenceReadiness(
        evidence_readiness=label,
        **{
            name: EvidenceDimension(
                status=statuses[name], evidence_ids=digest["evidence_ids"][name],
                notes=notes[name], confidence=decisions[name].confidence,
            )
            for name in DIMENSIONS
        },
        stale_inputs=digest["stale_inputs"],
        irrelevant_or_unreliable=(["synthetic dry-run data"] if dry_run else []) + digest["unreliable_inputs"],
        missing_inputs=[weak_sections[n] for n in DIMENSIONS if statuses[n] in {"missing", "stale"}],
        recommended_next_step=_next_step(label, statuses),
        decision=EvidenceDecision(
            decision_id=gate.decision_id, confidence=gate.confidence, route=gate.route, source=sources,
        ),
    )
