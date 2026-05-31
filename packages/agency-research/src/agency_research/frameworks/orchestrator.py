"""Framework Orchestrator — decides which frameworks to run and when.

Runs all applicable frameworks during a research pass. On subsequent calls,
checks each framework's computed_at against its STALENESS_DAYS and only
re-runs those that are stale or missing.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from agency_common.models import BrandProfile, FrameworksOutput, ResearchOutput
from .base import FrameworkBase
from .engagement_benchmarking import EngagementBenchmarkingFramework
from .content_audit import ContentAuditFramework
from .hashtag_landscape import HashtagLandscapeFramework
from .share_of_voice import ShareOfVoiceFramework
from .swot import SWOTFramework
from .jtbd import JTBDFramework
from .cep import CEPFramework
from .persona import PersonaFramework

LOGGER = logging.getLogger(__name__)


class FrameworkOrchestrator:
    """Run the framework analysis layer (Step 6) over a ResearchOutput.

    Args:
        anthropic_api_key: Required for LLM-driven frameworks (SWOT, JTBD, CEP, Persona).
        dry_run: Skip all LLM calls, return empty results.
        only: If given, restrict to these OUTPUT_FIELD names (e.g. ["swot", "jtbd"]).
        force: Re-run every framework regardless of staleness.
    """

    def __init__(self, anthropic_api_key: str = "", dry_run: bool = False):
        self.dry_run = dry_run
        self._frameworks: list[FrameworkBase] = [
            EngagementBenchmarkingFramework(),
            ContentAuditFramework(),
            HashtagLandscapeFramework(),
            ShareOfVoiceFramework(),
            SWOTFramework(anthropic_api_key=anthropic_api_key, dry_run=dry_run),
            JTBDFramework(anthropic_api_key=anthropic_api_key, dry_run=dry_run),
            CEPFramework(anthropic_api_key=anthropic_api_key, dry_run=dry_run),
            PersonaFramework(anthropic_api_key=anthropic_api_key, dry_run=dry_run),
        ]

    def run(
        self,
        research: ResearchOutput,
        brand: BrandProfile,
        existing: FrameworksOutput | None = None,
        *,
        force: bool = False,
        only: list[str] | None = None,
    ) -> FrameworksOutput:
        """Run applicable, stale frameworks and return an updated FrameworksOutput.

        Args:
            research: The current ResearchOutput (may be freshly scraped or loaded from workspace).
            brand: Brand profile for context.
            existing: Previous FrameworksOutput to update in-place. Pass None for a fresh run.
            force: Ignore staleness checks and re-run everything.
            only: Whitelist of OUTPUT_FIELD names to run. Runs all if omitted.
        """
        output = existing or FrameworksOutput(brand_slug=brand.slug)

        for framework in self._frameworks:
            field = framework.OUTPUT_FIELD
            if only and field not in only:
                continue
            if not framework.is_applicable(research, brand):
                LOGGER.debug("Framework %s not applicable for %s — skipping", field, brand.slug)
                continue
            if not force and not self._is_stale(output, framework):
                LOGGER.debug("Framework %s is fresh for %s — skipping", field, brand.slug)
                continue

            LOGGER.info("Running framework: %s for %s", field, brand.slug)
            try:
                result = framework.analyze(research, brand)
                setattr(output, field, result)
            except Exception:
                LOGGER.exception("Framework %s failed for %s", field, brand.slug)

        return output

    @staticmethod
    def _is_stale(output: FrameworksOutput, framework: FrameworkBase) -> bool:
        """Return True if the framework result is missing or older than STALENESS_DAYS."""
        result = getattr(output, framework.OUTPUT_FIELD, None)
        if result is None:
            return True
        computed_at_str: str = getattr(result, "computed_at", "") or ""
        if not computed_at_str:
            return True
        try:
            computed_at = datetime.fromisoformat(computed_at_str)
            # Handle naive datetimes (UTC assumed)
            if computed_at.tzinfo is None:
                computed_at = computed_at.replace(tzinfo=timezone.utc)
            threshold = datetime.now(tz=timezone.utc) - timedelta(days=framework.STALENESS_DAYS)
            return computed_at < threshold
        except ValueError:
            return True
