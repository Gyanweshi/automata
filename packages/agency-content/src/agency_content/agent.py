"""ContentAgent — orchestrates voice engine and writers for a brand."""
from __future__ import annotations

import logging
from datetime import datetime

from agency_common.config import AgencyConfig
from agency_common.models import (
    BrandProfile,
    ContentOutput,
    ContentPiece,
    ResearchOutput,
    StoryboardOutput,
)
from agency_common.obsidian_writer import log_brand_run_summary
from agency_common.workspace import WorkspaceManager

from .voice import BrandVoiceEngine
from .writers import InstagramWriter, LinkedInWriter

LOGGER = logging.getLogger(__name__)


def _try_vault_search(query: str) -> str:
    """Search the Second Brain vault. Returns empty string silently on any failure."""
    try:
        from agency_common.obsidian_vector_index import search_second_brain
        result = search_second_brain(query, num_results=2)
        if "No relevant notes" in result or "No readable" in result:
            return ""
        return result
    except Exception as exc:
        LOGGER.debug("Vault search unavailable: %s", exc)
        return ""


CONTENT_TYPES = {
    "instagram": {
        "caption": "instagram_caption",
        "carousel": "instagram_carousel",
        "reel": "instagram_reel",
        "reel_script": "instagram_reel",
    },
    "linkedin": {
        "post": "linkedin_post",
        "article": "linkedin_article",
        "carousel": "linkedin_carousel",
        "document_carousel": "linkedin_carousel",
    },
}


class ContentAgent:
    """Generate content briefs for a brand on Instagram and LinkedIn.

    The agent produces structured writing briefs that contain:
    - Brand voice instructions
    - Platform-specific formatting rules
    - Research-informed hashtag recommendations
    - Slot structure for Claude to fill in
    """

    def __init__(self, config: AgencyConfig | None = None):
        self.config = config or AgencyConfig.from_env()

    def generate(
        self,
        brand: BrandProfile,
        platform: str,
        content_type: str,
        topic: str,
        research: ResearchOutput | None = None,
        storyboard: StoryboardOutput | None = None,
        variations: int = 2,
        **kwargs,
    ) -> ContentOutput:
        """Generate content briefs for a specific platform and content type."""
        vault_context = _try_vault_search(f"{brand.slug} content style campaigns {topic}")
        if vault_context:
            LOGGER.info("Loaded vault context for %s (%d chars)", brand.slug, len(vault_context))

        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        pieces: list[ContentPiece] = []

        for i in range(1, variations + 1):
            piece = self._generate_piece(brand, platform, content_type, topic, research, vault_context=vault_context, **kwargs)
            piece.variation_index = i
            pieces.append(piece)

        output = ContentOutput(
            brand_slug=brand.slug,
            run_id=run_id,
            pieces=pieces,
            summary=f"{variations} {platform}/{content_type} brief(s) generated for '{topic}' ({brand.name})",
        )

        # Write a short note to the vault recording what was generated and for which topic.
        # Future runs searching for this brand's content style will find this.
        run_note = (
            f"Generated {variations} {platform}/{content_type} brief(s) for topic: '{topic}'.\n\n"
            + "\n\n---\n\n".join(
                f"**Piece {p.variation_index}** ({p.content_type}):\n{p.body[:600]}{'...' if len(p.body) > 600 else ''}"
                for p in pieces
            )
        )
        written = log_brand_run_summary(
            brand_slug=brand.slug,
            agent_name="ContentAgent",
            summary=run_note,
            extra_tags=["content", platform, content_type],
        )
        if written:
            LOGGER.info("Content run summary written to vault: %s", written)

        return output

    def generate_week(
        self,
        brand: BrandProfile,
        research: ResearchOutput | None = None,
    ) -> ContentOutput:
        """Generate a week of content briefs based on brand content pillars and platform schedules."""
        vault_context = _try_vault_search(f"{brand.slug} content style campaigns weekly")
        if vault_context:
            LOGGER.info("Loaded vault context for %s weekly plan (%d chars)", brand.slug, len(vault_context))

        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        pieces: list[ContentPiece] = []

        ig = brand.platforms.instagram
        li = brand.platforms.linkedin

        # Instagram: 5x/week by default — rotate content types
        if ig:
            ig_schedule = [
                ("carousel", "educational", "Your weekly educational carousel"),
                ("reel_script", "engagement", "Engagement reel — question or challenge"),
                ("caption", "behind_the_scenes", "Behind the scenes moment"),
                ("carousel", "social_proof", "Client result or testimonial carousel"),
                ("caption", "educational", "Quick tip caption"),
            ]
            for ct, pillar, placeholder_topic in ig_schedule:
                piece = self._generate_piece(brand, "instagram", ct, placeholder_topic, research, vault_context=vault_context)
                piece.notes += f" | Pillar: {pillar}"
                pieces.append(piece)

        # LinkedIn: 3x/week
        if li:
            li_schedule = [
                ("post", "Thought leadership post"),
                ("document_carousel", "Value-packed carousel"),
                ("post", "Engagement post — question or opinion"),
            ]
            for ct, placeholder_topic in li_schedule:
                piece = self._generate_piece(brand, "linkedin", ct, placeholder_topic, research, vault_context=vault_context)
                pieces.append(piece)

        output = ContentOutput(
            brand_slug=brand.slug,
            run_id=run_id,
            pieces=pieces,
            summary=f"Weekly content plan: {len(pieces)} briefs generated for {brand.name}",
        )

        run_note = (
            f"Weekly content plan: {len(pieces)} briefs generated for {brand.name}.\n\n"
            + "\n\n---\n\n".join(
                f"**{p.platform}/{p.content_type}** — {p.topic}:\n{p.body[:400]}{'...' if len(p.body) > 400 else ''}"
                for p in pieces
            )
        )
        written = log_brand_run_summary(
            brand_slug=brand.slug,
            agent_name="ContentAgent",
            summary=run_note,
            extra_tags=["content", "weekly-plan"],
        )
        if written:
            LOGGER.info("Weekly content plan written to vault: %s", written)

        return output

    def _generate_piece(
        self,
        brand: BrandProfile,
        platform: str,
        content_type: str,
        topic: str,
        research: ResearchOutput | None = None,
        vault_context: str = "",
        **kwargs,
    ) -> ContentPiece:
        if platform == "instagram":
            writer = InstagramWriter(brand)
            if content_type in ("caption",):
                piece = writer.caption_brief(topic, research=research, **kwargs)
            elif content_type in ("carousel",):
                piece = writer.carousel_brief(topic, research=research, **kwargs)
            elif content_type in ("reel", "reel_script"):
                piece = writer.reel_script_brief(topic, research=research, **kwargs)
            else:
                piece = writer.caption_brief(topic, research=research)
        elif platform == "linkedin":
            writer = LinkedInWriter(brand)
            if content_type in ("post",):
                piece = writer.post_brief(topic, research=research, **kwargs)
            elif content_type in ("article",):
                piece = writer.article_brief(topic, research=research, **kwargs)
            elif content_type in ("carousel", "document_carousel"):
                piece = writer.document_carousel_brief(topic, **kwargs)
            else:
                piece = writer.post_brief(topic, research=research)
        else:
            piece = ContentPiece(
                platform=platform,
                content_type=content_type,
                topic=topic,
                body=f"Unsupported platform: {platform}",
            )

        if vault_context:
            piece.body += (
                "\n\n---\n## Vault Context (past decisions and campaign style for this brand)\n"
                + vault_context
            )

        return piece

    def voice_brief(self, brand: BrandProfile) -> str:
        """Return the full brand voice brief string (for Claude skill system prompt)."""
        return BrandVoiceEngine(brand).full_brief()
