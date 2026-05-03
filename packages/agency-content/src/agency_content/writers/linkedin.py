"""LinkedIn content formatter — posts, articles, document carousels."""
from __future__ import annotations

from agency_common.models import BrandProfile, ContentPiece, ResearchOutput

from ..voice import BrandVoiceEngine

POST_LIMIT = 3000


class LinkedInWriter:
    """Generate LinkedIn content structures and writing briefs."""

    HOOK_TYPES = {
        "contrarian": "Challenge a widely-held belief in your niche",
        "story": "Open with a personal anecdote that connects to the lesson",
        "stat": "Lead with a surprising or counterintuitive statistic",
        "question": "Ask a question your audience is already thinking",
        "list_tease": "Promise a list of specific, valuable insights",
    }

    def __init__(self, brand: BrandProfile):
        self.brand = brand
        self.voice = BrandVoiceEngine(brand)

    def post_brief(
        self,
        topic: str,
        hook_type: str = "story",
        research: ResearchOutput | None = None,
    ) -> ContentPiece:
        """Generate a LinkedIn post writing brief."""
        body = self._post_template(topic, hook_type, research)
        li = self.brand.platforms.linkedin
        hashtags = []
        if li:
            hashtags = li.hashtag_groups.niche[:2] + li.hashtag_groups.broad[:2] + li.hashtag_groups.branded[:1]
        return ContentPiece(
            platform="linkedin",
            content_type="post",
            topic=topic,
            body=body,
            hashtags=hashtags[:5],
            cta="What's your take? Share below.",
            notes=f"Max {POST_LIMIT} chars. LinkedIn algorithm favors posts with early engagement.",
        )

    def article_brief(
        self,
        title: str,
        angle: str = "",
        research: ResearchOutput | None = None,
    ) -> ContentPiece:
        """Generate a LinkedIn article writing brief."""
        body = self._article_template(title, angle, research)
        return ContentPiece(
            platform="linkedin",
            content_type="article",
            topic=title,
            body=body,
            hashtags=self._article_hashtags(),
            cta="Follow for more deep-dives like this.",
            notes="Long-form. SEO-friendly. Target 800-1500 words.",
        )

    def document_carousel_brief(
        self,
        topic: str,
        slide_count: int = 10,
    ) -> ContentPiece:
        """Generate a LinkedIn document (PDF carousel) content brief."""
        body = self._carousel_template(topic, slide_count)
        li = self.brand.platforms.linkedin
        hashtags = []
        if li:
            hashtags = li.hashtag_groups.niche[:3] + li.hashtag_groups.branded[:1]
        return ContentPiece(
            platform="linkedin",
            content_type="document_carousel",
            topic=topic,
            body=body,
            hashtags=hashtags,
            cta="Save this carousel — download the full PDF.",
            notes="LinkedIn document carousels get 3x the reach of regular posts. Max 300 pages.",
        )

    # --- Internal helpers ---

    def _post_template(self, topic: str, hook_type: str, research: ResearchOutput | None) -> str:
        vc = self.voice.template_context()
        hook_guidance = self.HOOK_TYPES.get(hook_type, self.HOOK_TYPES["story"])
        lines = [
            f"# LinkedIn Post Brief: {topic}",
            "",
            f"**Brand voice**: {vc['tone']}",
            f"**Audience**: {vc['primary_audience']}",
            "",
            "## Structure",
            "LinkedIn posts perform best with:",
            "- **Line 1**: Hook that gets clicked 'see more' (no context, pure intrigue or bold claim)",
            "- **Lines 2-3**: [blank line after hook]",
            "- **Body**: Short paragraphs — 1-2 sentences each. White space is your friend.",
            "- **Closing**: Lesson or takeaway in 1 sentence",
            "- **CTA**: Question to drive comments (LinkedIn rewards early comment engagement)",
            "",
            f"**Hook approach**: {hook_guidance}",
            "",
        ]
        if vc["use_words"]:
            lines.append(f"**Vocabulary to use**: {', '.join(vc['use_words'][:5])}")
        if vc["dos"]:
            lines += ["", "**Rules:**"] + [f"- {d}" for d in vc["dos"][:3]]
        if research and "linkedin" in research.platforms:
            themes = research.platforms["linkedin"].content_themes[:3]
            if themes:
                lines += [
                    "",
                    f"**Trending themes from competitor research**: {', '.join(t.theme for t in themes)}",
                ]
        lines += ["", "---", f"*Topic: {topic} | Max {POST_LIMIT} chars*"]
        return "\n".join(lines)

    def _article_template(self, title: str, angle: str, research: ResearchOutput | None) -> str:
        vc = self.voice.template_context()
        lines = [
            f"# LinkedIn Article Brief: {title}",
            "",
            f"**Voice**: {vc['tone']}",
            f"**Angle**: {angle or 'Choose the most useful angle for ' + vc['primary_audience']}",
            "",
            "## Article Structure",
            "1. **Title**: SEO-aware, specific, promise-driven",
            "2. **Intro** (100 words): Hook + what reader will learn",
            "3. **Section 1**: Background / context",
            "4. **Section 2**: Core insight or method",
            "5. **Section 3**: Practical steps or examples",
            "6. **Section 4** (optional): Common mistakes or objections",
            "7. **Conclusion**: Summary + CTA",
            "",
            "**Target length**: 800-1500 words",
            "**Use headers**: H2 for sections, H3 for sub-points",
        ]
        if vc["pain_points"]:
            lines += ["", f"**Address these pain points**: {'; '.join(vc['pain_points'][:2])}"]
        return "\n".join(lines)

    def _carousel_template(self, topic: str, slide_count: int) -> str:
        vc = self.voice.template_context()
        lines = [
            f"# LinkedIn Document Carousel Brief: {topic}",
            "",
            f"**Voice**: {vc['tone']}",
            "",
            "## Slide Structure",
            "",
            "| Slide | Role | Content Guidance |",
            "|-------|------|-----------------|",
            "| 1 | Cover | Title + brand, bold visual claim |",
            "| 2 | Problem | Agitate the pain point |",
        ]
        points = slide_count - 4
        for i in range(1, points + 1):
            lines.append(f"| {i+2} | Point {i} | Key insight #{i} with example |")
        lines += [
            f"| {slide_count - 1} | Summary | Recap of key takeaways |",
            f"| {slide_count} | CTA | Follow + download prompt |",
            "",
            "**Design notes**: Use brand colors. Each slide = 1 idea. Bold headline + 2-3 bullets max.",
        ]
        return "\n".join(lines)

    def _article_hashtags(self) -> list[str]:
        li = self.brand.platforms.linkedin
        if not li:
            return []
        return li.hashtag_groups.niche[:2] + li.hashtag_groups.broad[:2] + li.hashtag_groups.branded[:1]
