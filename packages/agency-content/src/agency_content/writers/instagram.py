"""Instagram content formatter — captions, carousels, reel scripts."""
from __future__ import annotations

from agency_common.models import BrandProfile, ContentPiece, ResearchOutput

from ..voice import BrandVoiceEngine

CAPTION_LIMIT = 2200
REEL_CAPTION_LIMIT = 2200


class InstagramWriter:
    """Generate Instagram content structures for AI writing or template rendering.

    This class produces *structured content prompts* — formatted briefs that
    either Claude (via the skill) fills in, or that serve as ready-made content
    scaffolding. The actual creative copy is written by Claude when run via skill.
    """

    def __init__(self, brand: BrandProfile):
        self.brand = brand
        self.voice = BrandVoiceEngine(brand)

    def caption_brief(
        self,
        topic: str,
        tone_override: str = "",
        research: ResearchOutput | None = None,
    ) -> ContentPiece:
        """Generate a structured brief for a single Instagram caption."""
        ig = self.brand.platforms.instagram
        hashtag_guidance = ""
        if ig:
            niche = ig.hashtag_groups.niche[:5]
            broad = ig.hashtag_groups.broad[:5]
            hashtag_guidance = f"Niche: {', '.join(niche)}; Broad: {', '.join(broad)}"

        # Pull trending hashtags from research if available
        trending_tags: list[str] = []
        if research and "instagram" in research.platforms:
            ig_research = research.platforms["instagram"]
            trending_tags = [h.tag for h in ig_research.trending_hashtags[:5]]

        body = self._caption_template(topic, tone_override, hashtag_guidance, trending_tags)
        return ContentPiece(
            platform="instagram",
            content_type="caption",
            topic=topic,
            body=body,
            hashtags=self._select_hashtags(research),
            cta=self._cta_options()[0],
            notes=f"Target: {self.brand.audience.primary}. Max {CAPTION_LIMIT} chars.",
        )

    def carousel_brief(
        self,
        topic: str,
        slide_count: int = 7,
        research: ResearchOutput | None = None,
    ) -> ContentPiece:
        """Generate a slide-by-slide carousel content brief."""
        slides = self._carousel_structure(topic, slide_count)
        body = self._render_carousel_brief(slides, research)
        return ContentPiece(
            platform="instagram",
            content_type="carousel",
            topic=topic,
            body=body,
            hashtags=self._select_hashtags(research),
            cta=self._cta_options()[0],
            notes=f"{slide_count} slides. First slide is hook — must stop the scroll.",
        )

    def reel_script_brief(
        self,
        topic: str,
        duration_seconds: int = 30,
        research: ResearchOutput | None = None,
    ) -> ContentPiece:
        """Generate a reel script brief with timestamped scene/voiceover structure."""
        body = self._reel_template(topic, duration_seconds)
        return ContentPiece(
            platform="instagram",
            content_type="reel_script",
            topic=topic,
            body=body,
            hashtags=self._select_hashtags(research),
            cta="Follow for more + link in bio",
            notes=f"~{duration_seconds}s duration. Hook in first 2 seconds.",
        )

    # --- Internal helpers ---

    def _caption_template(
        self,
        topic: str,
        tone: str,
        hashtag_guidance: str,
        trending: list[str],
    ) -> str:
        vc = self.voice.template_context()
        lines = [
            f"# Instagram Caption Brief: {topic}",
            "",
            f"**Brand voice**: {vc['tone']}",
            f"**Archetype**: {vc['archetype']}",
            f"**Audience**: {vc['primary_audience']}",
            "",
            "## Writing Instructions",
            "Write a caption following this structure:",
            "1. **Hook** (line 1): Pattern interrupt or bold statement — stops scroll",
            "2. **Body** (lines 2-8): Value delivery in the brand voice — short paragraphs",
            "3. **CTA** (last line): Clear single action",
            "",
            f"**Tone**: {tone or vc['tone']}",
        ]
        if vc["use_words"]:
            lines.append(f"**Use words like**: {', '.join(vc['use_words'][:5])}")
        if vc["avoid_words"]:
            lines.append(f"**Avoid**: {', '.join(vc['avoid_words'][:5])}")
        if vc["dos"]:
            lines += ["", "**Rules:**"] + [f"- {d}" for d in vc["dos"][:3]]
        if hashtag_guidance:
            lines += ["", f"**Hashtag pool**: {hashtag_guidance}"]
        if trending:
            lines.append(f"**Trending tags to consider**: {', '.join(trending)}")
        lines += [
            "",
            "---",
            f"*Topic: {topic}*",
            f"*Max {CAPTION_LIMIT} characters including hashtags.*",
        ]
        return "\n".join(lines)

    def _carousel_structure(self, topic: str, slide_count: int) -> list[dict]:
        """Generate a slide-by-slide structural outline."""
        slides = [{"slide": 1, "role": "hook", "guidance": f"Bold statement about {topic} — stop the scroll"}]
        middle = slide_count - 2
        for i in range(2, middle + 2):
            slides.append({
                "slide": i,
                "role": f"point_{i-1}",
                "guidance": f"Point {i-1}: [expand on {topic}]",
            })
        slides.append({"slide": slide_count, "role": "cta", "guidance": "CTA + follow prompt"})
        return slides

    def _render_carousel_brief(self, slides: list[dict], research: ResearchOutput | None) -> str:
        vc = self.voice.template_context()
        lines = [
            "# Instagram Carousel Brief",
            "",
            f"**Voice**: {vc['tone']}",
            f"**Rules**: {'; '.join(vc['dos'][:2]) if vc['dos'] else 'see brand profile'}",
            "",
            "## Slide Structure",
            "For each slide: write the visual headline (5-7 words max) and 1-2 supporting lines.\n",
        ]
        for s in slides:
            lines += [
                f"### Slide {s['slide']} — {s['role'].upper()}",
                f"*Guidance*: {s['guidance']}",
                "**Headline**: [write here]",
                "**Body**: [write here]",
                "",
            ]
        if research and "instagram" in research.platforms:
            themes = research.platforms["instagram"].content_themes[:3]
            if themes:
                theme_words = [t.theme for t in themes]
                lines.append(f"*Research insight: top themes in this niche — {', '.join(theme_words)}*")
        return "\n".join(lines)

    def _reel_template(self, topic: str, duration: int) -> str:
        vc = self.voice.template_context()
        lines = [
            f"# Reel Script Brief: {topic} ({duration}s)",
            "",
            f"**Brand voice**: {vc['tone']}",
            "",
            "## Script Structure",
            "| Time | Visual | Voiceover/Text |",
            "|------|--------|----------------|",
            "| 0-2s | Hook visual | [Bold opening hook] |",
            "| 2-8s | Setup | [Problem or promise] |",
        ]
        segment_size = max(3, (duration - 10) // 3)
        t = 8
        for i in range(1, 4):
            end = t + segment_size
            lines.append(f"| {t}-{end}s | Content beat {i} | [Value point {i}] |")
            t = end
        lines += [
            f"| {t}-{duration}s | CTA + branding | [Call to action] |",
            "",
            "## Hooks to try (pick one):",
            "- 'Most people don't know this about [topic]...'",
            "- 'Stop doing X — here's why'",
            "- 'The [number] [topic] hack that changed everything'",
        ]
        return "\n".join(lines)

    def _select_hashtags(self, research: ResearchOutput | None) -> list[str]:
        ig = self.brand.platforms.instagram
        if not ig:
            return []
        tags = (ig.hashtag_groups.niche[:3]
                + ig.hashtag_groups.broad[:3]
                + ig.hashtag_groups.branded[:1])
        if research and "instagram" in research.platforms:
            trending = [h.tag for h in research.platforms["instagram"].trending_hashtags[:3]]
            tags += [t for t in trending if t not in tags]
        return tags[:12]

    def _cta_options(self) -> list[str]:
        return [
            "Save this post — you'll want it later.",
            "Share with someone who needs to hear this.",
            "Drop a comment below 👇",
            "Link in bio for more.",
            "Follow for weekly tips.",
        ]
