"""Brand voice engine — converts a BrandProfile into writing instructions."""
from __future__ import annotations

from agency_common.models import BrandProfile

# These are hardcoded because they apply to ALL brands — not brand-specific config.
# They address the default failure modes of LLM writing regardless of tone or style.
_UNIVERSAL_ANTI_AI_RULES = """\
ANTI-AI-WRITING — enforce absolutely, no exceptions:
- No em dashes (—). Rewrite the sentence. Use a comma, a full stop, or two sentences.
- Never use: "it's worth noting", "it's important to", "delve", "leverage" (unless in brand vocab), \
"in conclusion", "furthermore", "moreover", "seamlessly", "game-changer", "groundbreaking", \
"innovative solution", "cutting-edge", "unlock", "elevate".
- No subordinate clause chains. If removing a comma before "which", "that", or "who" breaks \
the sentence, split it into two.
- No passive voice in hooks or CTAs.
- No generic reel/carousel hooks: "Most people don't know...", "Stop doing X", \
"The [number] hack that changed everything". Write hooks specific to this brand and topic.
- Short sentences. Write how a smart person talks, not how they write a university essay.\
"""


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

    def sentence_constraint(self) -> str:
        limit = self.brand.writing.sentence_max_words
        if limit and limit > 0:
            return f"MAX SENTENCE LENGTH: {limit} words. Count them. Split anything longer."
        return ""

    def banned_constructions(self) -> str:
        items = self.brand.writing.banned_constructions
        if not items:
            return ""
        return "BANNED CONSTRUCTIONS (brand-specific):\n" + "\n".join(f"- {c}" for c in items)

    def example_copy(self) -> str:
        examples = self.brand.writing.example_captions
        if not examples:
            return ""
        header = (
            "EXAMPLE COPY — calibrate your voice against these. "
            "Match the rhythm, sentence length, and register. Do not copy; use as anchor:"
        )
        body = "\n\n---\n\n".join(ex.strip() for ex in examples if ex.strip())
        return f"{header}\n\n{body}"

    def archetype_hooks(self) -> str:
        """Return hook style guidance derived from the brand archetype — no generic fill-in-the-blank patterns."""
        archetype_hooks = {
            "authority": (
                "Hooks should establish credibility through specificity: a counterintuitive finding, "
                "a precise number, or a direct claim only an expert would make."
            ),
            "innovator": (
                "Hooks should challenge an assumption the audience holds: 'What if [common belief] "
                "is exactly backwards?' or frame a familiar problem in an unfamiliar way."
            ),
            "friend": (
                "Hooks should feel like the opening of a real conversation: a personal admission, "
                "a relatable mistake, or a direct question the reader is already thinking."
            ),
            "rebel": (
                "Hooks should name something the industry does that the audience hates, "
                "or take a position that most accounts in this space wouldn't dare to."
            ),
            "guide": (
                "Hooks should promise a specific, believable transformation: "
                "what will the reader know or be able to do by the end that they couldn't before?"
            ),
        }
        primary = self.brand.voice.archetype_primary
        return f"HOOK STYLE ({primary} archetype): {archetype_hooks.get(primary, 'Write an opening line specific to this brand and topic.')}"

    def memory_context(self) -> str:
        """Include distilled run history directly in the brief — no retrieval needed."""
        if not self.brand.memory:
            return ""
        bullets = "\n".join(f"- {m}" for m in self.brand.memory)
        return (
            "BRAND MEMORY (distilled history — use as context, do not repeat verbatim):\n"
            + bullets
        )

    def full_brief(self) -> str:
        """Generate a complete writing brief string for Claude prompts."""
        sections = [
            f"BRAND: {self.brand.name}",
            f"TONE: {self.tone_description()}",
            self.archetype_guidance(),
            f"VOCABULARY:\n{self.vocabulary_context()}",
            f"WRITING RULES:\n{self.writing_rules()}",
            f"AUDIENCE:\n{self.audience_context()}",
            self.archetype_hooks(),
            _UNIVERSAL_ANTI_AI_RULES,
        ]
        constraint = self.sentence_constraint()
        if constraint:
            sections.append(constraint)
        banned = self.banned_constructions()
        if banned:
            sections.append(banned)
        examples = self.example_copy()
        if examples:
            sections.append(examples)
        memory = self.memory_context()
        if memory:
            sections.append(memory)
        return "\n\n".join(s for s in sections if s.strip())

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
