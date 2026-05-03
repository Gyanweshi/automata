"""ContentAgent — orchestrates voice engine and writers for a brand."""
from __future__ import annotations

from datetime import datetime

from agency_common.config import AgencyConfig
from agency_common.models import (
    BrandProfile,
    ContentOutput,
    ContentPiece,
    ResearchOutput,
    StoryboardOutput,
)
from agency_common.workspace import WorkspaceManager

from .voice import BrandVoiceEngine
from .writers import InstagramWriter, LinkedInWriter


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
        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        pieces: list[ContentPiece] = []

        for i in range(1, variations + 1):
            piece = self._generate_piece(brand, platform, content_type, topic, research, **kwargs)
            piece.variation_index = i
            pieces.append(piece)

        return ContentOutput(
            brand_slug=brand.slug,
            run_id=run_id,
            pieces=pieces,
            summary=f"{variations} {platform}/{content_type} brief(s) generated for '{topic}' ({brand.name})",
        )

    def generate_week(
        self,
        brand: BrandProfile,
        research: ResearchOutput | None = None,
    ) -> ContentOutput:
        """Generate a week of content briefs based on brand content pillars and platform schedules."""
        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        pieces: list[ContentPiece] = []
        pillars = brand.content_pillars

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
                piece = self._generate_piece(brand, "instagram", ct, placeholder_topic, research)
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
                piece = self._generate_piece(brand, "linkedin", ct, placeholder_topic, research)
                pieces.append(piece)

        return ContentOutput(
            brand_slug=brand.slug,
            run_id=run_id,
            pieces=pieces,
            summary=f"Weekly content plan: {len(pieces)} briefs generated for {brand.name}",
        )

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
                return writer.caption_brief(topic, research=research, **kwargs)
            elif content_type in ("carousel",):
                return writer.carousel_brief(topic, research=research, **kwargs)
            elif content_type in ("reel", "reel_script"):
                return writer.reel_script_brief(topic, research=research, **kwargs)
            else:
                return writer.caption_brief(topic, research=research)
        elif platform == "linkedin":
            writer = LinkedInWriter(brand)
            if content_type in ("post",):
                return writer.post_brief(topic, research=research, **kwargs)
            elif content_type in ("article",):
                return writer.article_brief(topic, research=research, **kwargs)
            elif content_type in ("carousel", "document_carousel"):
                return writer.document_carousel_brief(topic, **kwargs)
            else:
                return writer.post_brief(topic, research=research)
        else:
            return ContentPiece(
                platform=platform,
                content_type=content_type,
                topic=topic,
                body=f"Unsupported platform: {platform}",
            )

    def voice_brief(self, brand: BrandProfile) -> str:
        """Return the full brand voice brief string (for Claude skill system prompt)."""
        return BrandVoiceEngine(brand).full_brief()
