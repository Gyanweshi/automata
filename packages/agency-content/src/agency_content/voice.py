"""Brand voice engine — converts a BrandProfile into writing instructions."""
from __future__ import annotations

from agency_common.models import BrandProfile


class BrandVoiceEngine:
    """Translate a BrandProfile's voice parameters into actionable writing context.

    The output of this engine is fed into Jinja2 templates as context variables,
    and also into the Claude Code skill system prompt to guide AI writing.
    """

    def __init__(self, brand: BrandProfile):
        self.brand = brand

    def tone_description(self) -> str:
        """Generate a natural-language tone description from voice scores."""
        v = self.brand.voice
        parts = []
        # formal_casual
        if v.formal_casual <= 3:
            parts.append("very formal and professional")
        elif v.formal_casual <= 5:
            parts.append("professional yet approachable")
        elif v.formal_casual <= 7:
            parts.append("conversational and friendly")
        else:
            parts.append("casual and relaxed")
        # serious_playful
        if v.serious_playful <= 3:
            parts.append("serious and focused")
        elif v.serious_playful <= 6:
            parts.append("balanced between serious and lighthearted")
        else:
            parts.append("playful and fun")
        # technical_simple
        if v.technical_simple <= 3:
            parts.append("uses precise technical language")
        elif v.technical_simple <= 6:
            parts.append("clear and accessible")
        else:
            parts.append("simple and jargon-free")
        # bold_reserved
        if v.reserved_bold >= 7:
            parts.append("bold and direct")
        elif v.reserved_bold <= 3:
            parts.append("reserved and subtle")
        return ", ".join(parts)

    def archetype_guidance(self) -> str:
        archetype_map = {
            "authority": "Speak with confidence and expertise. Position the brand as the definitive source.",
            "innovator": "Lead with novelty and forward-thinking ideas. Challenge the status quo.",
            "friend": "Write like a trusted friend who happens to be an expert. Warm, encouraging, non-judgmental.",
            "rebel": "Challenge conventions. Be provocative and disruptive — in a constructive way.",
            "guide": "Lead the audience on a journey. Use storytelling and step-by-step clarity.",
        }
        primary = archetype_map.get(self.brand.voice.archetype_primary, "")
        secondary = archetype_map.get(self.brand.voice.archetype_secondary or "", "")
        if secondary:
            return f"Primary archetype ({self.brand.voice.archetype_primary}): {primary}\nSecondary ({self.brand.voice.archetype_secondary}): {secondary}"
        return f"Archetype ({self.brand.voice.archetype_primary}): {primary}"

    def vocabulary_context(self) -> str:
        v = self.brand.vocabulary
        lines = []
        if v.use_words:
            lines.append(f"Preferred words/phrases: {', '.join(v.use_words)}")
        if v.avoid_words:
            lines.append(f"Words to avoid: {', '.join(v.avoid_words)}")
        if v.signature_phrases:
            lines.append(f"Signature phrases: {', '.join(v.signature_phrases)}")
        return "\n".join(lines)

    def writing_rules(self) -> str:
        lines = []
        if self.brand.writing.dos:
            lines.append("Do:\n" + "\n".join(f"  - {d}" for d in self.brand.writing.dos))
        if self.brand.writing.donts:
            lines.append("Don't:\n" + "\n".join(f"  - {d}" for d in self.brand.writing.donts))
        return "\n".join(lines)

    def audience_context(self) -> str:
        a = self.brand.audience
        lines = [f"Primary audience: {a.primary}"]
        if a.secondary:
            lines.append(f"Secondary audience: {a.secondary}")
        if a.pain_points:
            lines.append("Pain points: " + "; ".join(a.pain_points))
        if a.desires:
            lines.append("What they want: " + "; ".join(a.desires))
        return "\n".join(lines)

    def full_brief(self) -> str:
        """Generate a complete writing brief string for Claude prompts."""
        return (
            f"BRAND: {self.brand.name}\n\n"
            f"TONE: {self.tone_description()}\n\n"
            f"{self.archetype_guidance()}\n\n"
            f"VOCABULARY:\n{self.vocabulary_context()}\n\n"
            f"WRITING RULES:\n{self.writing_rules()}\n\n"
            f"AUDIENCE:\n{self.audience_context()}"
        )

    def template_context(self) -> dict:
        """Return all voice data as a flat dict for Jinja2 templates."""
        return {
            "brand_name": self.brand.name,
            "brand_slug": self.brand.slug,
            "tone": self.tone_description(),
            "archetype": self.brand.voice.archetype_primary,
            "use_words": self.brand.vocabulary.use_words,
            "avoid_words": self.brand.vocabulary.avoid_words,
            "signature_phrases": self.brand.vocabulary.signature_phrases,
            "dos": self.brand.writing.dos,
            "donts": self.brand.writing.donts,
            "primary_audience": self.brand.audience.primary,
            "pain_points": self.brand.audience.pain_points,
            "desires": self.brand.audience.desires,
            "formal_casual": self.brand.voice.formal_casual,
            "serious_playful": self.brand.voice.serious_playful,
        }
