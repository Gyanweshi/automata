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

from .voice import BrandVoiceEngine
from .writers import InstagramWriter, LinkedInWriter

LOGGER = logging.getLogger(__name__)

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
    - Brand voice instructions (including distilled memory — no retrieval needed)
    - Platform-specific formatting rules
    - Research-informed hashtag recommendations
    - Slot structure for Claude to fill in

    Runs are workspace-only. The CLI performs any explicitly authorized final
    Memory update after the output has been written.
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
        # Brand memory is already in brand.memory, loaded from the .md note by brand_loader.
        # BrandVoiceEngine.full_brief() includes it directly — no retrieval needed.
        if brand.memory:
            LOGGER.info("Brand memory loaded for %s (%d entries)", brand.slug, len(brand.memory))

        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        pieces: list[ContentPiece] = []

        for i in range(1, variations + 1):
            piece = self._generate_piece(brand, platform, content_type, topic, research, **kwargs)
            piece.variation_index = i
            pieces.append(piece)

        output = ContentOutput(
            brand_slug=brand.slug,
            run_id=run_id,
            pieces=pieces,
            summary=f"{variations} {platform}/{content_type} brief(s) generated for '{topic}' ({brand.name})",
        )

        return output

    def generate_week(
        self,
        brand: BrandProfile,
        research: ResearchOutput | None = None,
    ) -> ContentOutput:
        """Generate a week of content briefs based on brand content pillars and platform schedules."""
        if brand.memory:
            LOGGER.info("Brand memory loaded for %s (%d entries)", brand.slug, len(brand.memory))

        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        pieces: list[ContentPiece] = []

        ig = brand.platforms.instagram
        li = brand.platforms.linkedin

        if ig:
            ig_schedule = [
                ("carousel", "educational", "Your weekly educational carousel"),
                ("reel_script", "engagement", "Engagement reel — question or challenge"),
                ("caption", "behind_the_scenes", "Behind the scenes moment"),
                ("carousel", "social_proof", "Client result or testimonial carousel"),
                ("caption", "educational", "Quick tip caption"),
            ]
            for ct, pillar, placeholder_topic in ig_schedule:
                piece = self._generate_piece(brand, "instagram", ct, placeholder_topic, research)
                piece.notes += f" | Pillar: {pillar}"
                pieces.append(piece)

        if li:
            li_schedule = [
                ("post", "Thought leadership post"),
                ("document_carousel", "Value-packed carousel"),
                ("post", "Engagement post — question or opinion"),
            ]
            for ct, placeholder_topic in li_schedule:
                piece = self._generate_piece(brand, "linkedin", ct, placeholder_topic, research)
                pieces.append(piece)

        output = ContentOutput(
            brand_slug=brand.slug,
            run_id=run_id,
            pieces=pieces,
            summary=f"Weekly content plan: {len(pieces)} briefs generated for {brand.name}",
        )

        return output

    def _generate_piece(
        self,
        brand: BrandProfile,
        platform: str,
        content_type: str,
        topic: str,
        research: ResearchOutput | None = None,
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

        return piece

    def voice_brief(self, brand: BrandProfile) -> str:
        """Return the full brand voice brief string (for Claude skill system prompt)."""
        return BrandVoiceEngine(brand).full_brief()
