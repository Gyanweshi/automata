"""Cross-industry adjacency mapper — surfaces trends bleeding in from adjacent sectors.

Step 5 of the deep research pipeline. Maps narrative and visual trends from premium
adjacent industries to find moves that haven't yet crossed into the primary category.
A trend that peaked in luxury hospitality may still be emerging in real estate.
Adapting it early puts the brand ahead of the local curve.

Requires: ANTHROPIC_API_KEY
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from agency_common.models import AdjacencyInsight, AdjacencyReport

LOGGER = logging.getLogger(__name__)

_ADJACENCY_PROMPT = """You are a brand trend analyst specializing in cross-industry narrative transfer.

Primary category: {primary_category}
Adjacent premium industries to analyze: {adjacent_industries}

For each adjacent industry, identify the most specific, actionable current trend — a narrative
style, visual language, copywriting approach, or campaign mechanic — that could be adapted
for the primary category.

Focus on premium/aspirational brands. Be specific. Name real aesthetic movements, not vague
directions. Reference actual brand or campaign styles where relevant.

Return a JSON object with this EXACT structure — no markdown, no explanation, JSON only:
{{
  "insights": [
    {{
      "source_industry": "Industry name",
      "trend_or_narrative": "Specific trend name or description (1-2 sentences)",
      "how_to_adapt": "Concrete suggestion for applying this in {primary_category} (1-2 sentences)",
      "readiness_to_cross": "peaked | crossing now | emerging"
    }}
  ],
  "top_opportunities": [
    "Single most actionable opportunity description (3-5 items)"
  ]
}}

readiness_to_cross guide:
- "peaked" = trend is mature or declining in the source industry, safe to borrow now
- "crossing now" = actively moving between sectors, act fast
- "emerging" = just appearing in source industry, get ahead of the curve"""


class AdjacencyMapper:
    """Map cross-industry trend pollination from adjacent premium sectors."""

    def __init__(self, anthropic_api_key: str = "", dry_run: bool = False):
        self.anthropic_api_key = anthropic_api_key
        self.dry_run = dry_run

    def map(
        self,
        primary_category: str,
        adjacent_industries: list[str],
    ) -> AdjacencyReport:
        """Return adjacency insights for the given primary category."""
        if not adjacent_industries:
            return AdjacencyReport(
                analyzed_at=datetime.utcnow().isoformat(),
                adjacent_industries=[],
            )

        if self.dry_run:
            LOGGER.info(
                "[dry-run] Would map adjacencies: %s → %s",
                primary_category,
                adjacent_industries,
            )
            return AdjacencyReport(
                analyzed_at=datetime.utcnow().isoformat(),
                adjacent_industries=adjacent_industries,
            )

        if not self.anthropic_api_key:
            LOGGER.warning("No ANTHROPIC_API_KEY — skipping adjacency mapping")
            return AdjacencyReport(
                analyzed_at=datetime.utcnow().isoformat(),
                adjacent_industries=adjacent_industries,
            )

        prompt = _ADJACENCY_PROMPT.format(
            primary_category=primary_category,
            adjacent_industries=", ".join(adjacent_industries),
        )

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()

            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            data = json.loads(raw)

            insights = []
            for item in data.get("insights", []):
                if not isinstance(item, dict):
                    continue
                try:
                    insights.append(AdjacencyInsight(**item))
                except Exception as e:
                    import os, logging
                    if os.environ.get("AGENCY_DEBUG") == "1":
                        logging.getLogger(__name__).error(e, exc_info=True)

            return AdjacencyReport(
                analyzed_at=datetime.utcnow().isoformat(),
                adjacent_industries=adjacent_industries,
                insights=insights,
                top_opportunities=data.get("top_opportunities", []),
            )

        except json.JSONDecodeError as exc:
            LOGGER.error("Adjacency mapping: JSON parse failed: %s", exc)
            return AdjacencyReport(
                analyzed_at=datetime.utcnow().isoformat(),
                adjacent_industries=adjacent_industries,
            )
        except Exception as exc:
            LOGGER.error("Adjacency mapping LLM call failed: %s", exc)
            return AdjacencyReport(
                analyzed_at=datetime.utcnow().isoformat(),
                adjacent_industries=adjacent_industries,
            )
