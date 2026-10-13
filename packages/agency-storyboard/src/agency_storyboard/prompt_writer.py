"""AI generation prompt writer — structured prompts for image/video tools."""
from __future__ import annotations

from agency_common.models import BrandProfile, GenerationPrompt, Scene, ConsistencyBible
from agency_common.models import VisualDNA


# Supported tool schemas
TOOL_SCHEMAS = {
    "magnific_image": {
        "fields": ["positive_prompt", "negative_prompt", "aspect_ratio", "style"],
        "aspect_ratios": ["1:1", "4:5", "9:16", "16:9", "3:4"],
        "default_aspect": "4:5",
    },
    "magnific_video": {
        "fields": ["positive_prompt", "aspect_ratio", "duration"],
        "aspect_ratios": ["9:16", "16:9", "1:1"],
        "default_aspect": "9:16",
    },
    "blender": {
        "fields": ["positive_prompt", "style", "lighting", "camera_angle"],
        "aspect_ratios": ["1:1", "16:9", "9:16"],
        "default_aspect": "16:9",
    },
    "generic": {
        "fields": ["positive_prompt", "negative_prompt", "aspect_ratio", "style"],
        "aspect_ratios": ["1:1", "4:5", "9:16", "16:9"],
        "default_aspect": "1:1",
    },
    # --- Standalone image models (see skills/visual-image) ---
    "nano_banana_2": {
        "fields": ["positive_prompt", "negative_prompt", "aspect_ratio"],
        "aspect_ratios": [
            "1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4",
            "9:16", "16:9", "21:9", "1:8", "8:1", "1:4", "4:1",
        ],
        "default_aspect": "4:5",
        "prompt_style": "natural_language",
        "recommended_tier": ["simple"],
        "notes": (
            "Gemini 3 Flash image. Natural-language prose, no numeric lens params "
            "(50mm, f/2.8 are ignored). Supports image grounding for real places "
            "and extreme aspect ratios. ~$0.04/img."
        ),
    },
    "nano_banana_pro": {
        "fields": ["positive_prompt", "negative_prompt", "aspect_ratio"],
        "aspect_ratios": [
            "1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9",
        ],
        "default_aspect": "4:5",
        "prompt_style": "natural_language",
        "recommended_tier": ["hands_or_mechanical", "full_scene"],
        "notes": (
            "Gemini 3 Pro image. Thinking mode for complex/spatial scenes, up to "
            "14 reference images. ~$0.15/img — use for hero/key visuals."
        ),
    },
    "gpt_image_2": {
        "fields": ["scene", "subject", "important_details", "use_case", "constraints"],
        "aspect_ratios": ["1:1", "4:5", "5:4", "3:4", "4:3", "16:9", "9:16", "3:1"],
        "default_aspect": "4:5",
        "prompt_style": "five_slot",
        "quality_levels": ["low", "medium", "high"],
        "notes": (
            "5-slot template (Scene/Subject/Important Details/Use Case/Constraints). "
            "Best for dense/small text, UI mockups, brand assets, and identity-"
            "preserving edits. Avoid 'stunning/epic/masterpiece' (anti-slop)."
        ),
    },
    # --- Standalone video models (see skills/visual-video) ---
    "seedance": {
        "fields": ["positive_prompt", "aspect_ratio", "duration"],
        "aspect_ratios": ["9:16", "16:9", "1:1"],
        "default_aspect": "9:16",
        "max_duration": 12,
        "notes": "Multi-shot montages, fast cuts and drama. Up to 12s.",
    },
    "kling_3": {
        "fields": ["positive_prompt", "aspect_ratio", "duration"],
        "aspect_ratios": ["9:16", "16:9", "1:1"],
        "default_aspect": "9:16",
        "max_duration": 15,
        "notes": "Native multi-shot with dialogue and lip-sync. Up to 15s.",
    },
    "veo": {
        "fields": ["positive_prompt", "aspect_ratio", "duration"],
        "aspect_ratios": ["16:9", "9:16"],
        "default_aspect": "16:9",
        "max_duration": 8,
        "notes": "Dialogue + synchronized sound effects, commercial polish. Up to 8s.",
    },
}

UNIVERSAL_NEGATIVE = (
    "blurry, low quality, pixelated, watermark, text, logo, nsfw, "
    "distorted, overexposed, underexposed, noise, grain"
)

# Use-case → aspect ratio. Checked in order; first substring match wins.
# Keeps prompts sized for where they'll actually be posted unless the
# caller passes an explicit aspect_ratio override.
USE_CASE_ASPECT_RATIOS: list[tuple[str, str]] = [
    ("story", "9:16"),
    ("reel", "9:16"),
    ("tiktok", "9:16"),
    ("shorts", "9:16"),
    ("linkedin post", "1.91:1"),
    ("linkedin", "1.91:1"),
    ("youtube thumbnail", "16:9"),
    ("thumbnail", "16:9"),
    ("banner", "16:9"),
    ("cover photo", "16:9"),
    ("pinterest", "2:3"),
    ("poster", "2:3"),
    ("profile picture", "1:1"),
    ("square", "1:1"),
    ("carousel", "4:5"),
    ("instagram post", "4:5"),
    ("static post", "4:5"),
    ("feed post", "4:5"),
    ("product listing", "1:1"),
]


def _ratio_value(ratio: str) -> float:
    width, height = ratio.split(":")
    return float(width) / float(height)


def aspect_ratio_for_use_case(use_case: str, schema: dict) -> str | None:
    """Pick an aspect ratio matching the platform/format named in ``use_case``.

    Returns the matched ratio if the tool supports it, otherwise the
    tool-supported ratio closest to it. Returns None if ``use_case``
    doesn't match any known platform/format.
    """
    use_case_lower = use_case.lower()
    target = next(
        (ratio for keyword, ratio in USE_CASE_ASPECT_RATIOS if keyword in use_case_lower),
        None,
    )
    if target is None:
        return None

    supported = schema.get("aspect_ratios", [])
    if target in supported:
        return target
    if not supported:
        return target

    target_value = _ratio_value(target)
    return min(supported, key=lambda r: abs(_ratio_value(r) - target_value))


class PromptWriter:
    """Generate structured AI generation prompts from scenes and brand context."""

    def __init__(self, brand: BrandProfile):
        self.brand = brand

    def _brand_style_string(self) -> str:
        """Build a reusable brand aesthetic string for all prompts."""
        v = self.brand.visual
        parts = [v.photography_style, v.mood]
        parts = [v.photography_style.strip(), v.mood.strip()]
        if v.colors.primary:
            parts.append(f"color palette: {v.colors.primary}")
            if v.colors.secondary:
                parts.append(v.colors.secondary)
        return ", ".join(filter(None, parts))

    def scene_to_prompt(
        self,
        scene: Scene,
        tool: str = "magnific_image",
        aspect_ratio: str | None = None,
        bible: ConsistencyBible | None = None,
        reference_id: str | None = None,
    ) -> GenerationPrompt:
        """Convert a scene into a generation prompt for the specified tool."""
        schema = TOOL_SCHEMAS.get(tool, TOOL_SCHEMAS["generic"])
        ar = aspect_ratio or schema["default_aspect"]
        brand_style = self._brand_style_string()

        # Avoid brand's listed visual avoidances
        avoid = ", ".join(self.brand.visual.avoid_visuals)
        negative = f"{UNIVERSAL_NEGATIVE}, {avoid}".strip(", ")

        shot_desc = ""
        complexity = "simple"
        if scene.shots:
            shot = scene.shots[0]
            complexity = shot.complexity
            shot_desc = (
                f"{shot.shot_type} shot, subject: {shot.subject}, "
                f"{shot.action}, lighting: {shot.lighting}"
            )
            
            # Shot-aware negative prompts
            subject_action = (shot.subject + " " + shot.action).lower()
            if any(k in subject_action for k in ["hand", "grip", "lever", "handlebar"]) or complexity == "hands_or_mechanical":
                negative = f"{negative}, malformed hands, extra fingers, warped or duplicated mechanical geometry"
            
            if "macro" in shot.shot_type.lower() or "close-up" in shot.shot_type.lower() or "close up" in shot.shot_type.lower():
                negative = f"{negative}, not black and white, not monochrome, full-color photograph"

        visual_elements = ", ".join(scene.visual_elements) if scene.visual_elements else ""
        
        bible_str = ""
        if bible:
            bible_parts = []
            if bible.subject_descriptors:
                bible_parts.append("Subject: " + ", ".join(bible.subject_descriptors))
            if bible.wardrobe:
                bible_parts.append("Wardrobe: " + ", ".join(bible.wardrobe))
            if bible.equipment:
                bible_parts.append("Equipment: " + ", ".join(bible.equipment))
            if bible.color_grade:
                bible_parts.append(f"Color grade: {bible.color_grade}")
            bible_str = ", ".join(bible_parts)

        positive = (
            f"{bible_str}, {scene.description}, {visual_elements}, {shot_desc}, "
            f"mood: {scene.mood}, {brand_style}"
        ).strip(", ")

        additional: dict = {}
        if tool == "magnific_video" and scene.duration_seconds:
            additional["duration"] = scene.duration_seconds
        if tool == "blender" and scene.shots:
            additional["camera_angle"] = scene.shots[0].camera_angle

        prompt = GenerationPrompt(
            tool=tool,
            positive_prompt=positive,
            negative_prompt=negative,
            style=self.brand.visual.photography_style,
            aspect_ratio=ar,
            additional_params=additional,
        )
        if reference_id:
            prompt.reference_creation_ids = [reference_id]
        return prompt

    def storyboard_prompts(
        self,
        scenes: list[Scene],
        tool: str = "magnific_image",
        aspect_ratio: str | None = None,
        bible: ConsistencyBible | None = None,
        hero_reference_id: str | None = None,
    ) -> list[GenerationPrompt]:
        """Generate one prompt per scene."""
        return [self.scene_to_prompt(scene, tool=tool, aspect_ratio=aspect_ratio, bible=bible, reference_id=hero_reference_id) for scene in scenes]

    def standalone_image_prompt(
        self,
        subject: str,
        *,
        setting: str = "",
        action: str = "",
        composition: str = "",
        use_case: str = "",
        copy: str = "",
        copy_position: str = "lower third",
        tool: str = "nano_banana_2",
        aspect_ratio: str | None = None,
        detail_mode: str = "standard",
        visual_dna: VisualDNA | None = None,
    ) -> GenerationPrompt:
        """Build a standalone (non-storyboard) image prompt.

        Follows the 5-element framework from skills/visual-image
        (subject, setting, action, composition, style) layered with the brand's
        visual identity and, if available, the market's Visual DNA from research
        (dominant aesthetic, color trend, pattern-interrupt opportunity).

        ``detail_mode``: concise | standard | verbose | cinematic_verbose.
        ``cinematic_verbose`` adds the micro-detail layer (surface wear,
        micro-textures, specular highlights, contact shadows) for hero/key
        visuals that need to read as ultrarealistic.

        If ``aspect_ratio`` is not given, it is derived from ``use_case``
        (e.g. "Instagram static post" -> 4:5, "Instagram story"/"reel" -> 9:16,
        "LinkedIn post" -> 1.91:1) via ``aspect_ratio_for_use_case``, falling
        back to the tool's default aspect.

        ``copy``, if given, is rendered on the image as exact-quoted text in
        the brand's display/body font, positioned at ``copy_position``
        (default "lower third"), with anti-duplicate-text constraints added.
        """
        schema = TOOL_SCHEMAS.get(tool, TOOL_SCHEMAS["nano_banana_2"])
        use_case = use_case or "social media content"
        ar = (
            aspect_ratio
            or aspect_ratio_for_use_case(use_case, schema)
            or schema["default_aspect"]
        )
        brand_style = self._brand_style_string()

        creative_direction: list[str] = []
        if visual_dna:
            if visual_dna.pattern_interrupt_opportunity:
                creative_direction.append(visual_dna.pattern_interrupt_opportunity)
            if visual_dna.color_palette_trend:
                creative_direction.append(f"color direction: {visual_dna.color_palette_trend}")
            if visual_dna.typography_trend and "text" in (subject + action + composition).lower():
                creative_direction.append(f"typography direction: {visual_dna.typography_trend}")

        avoid = ", ".join(self.brand.visual.avoid_visuals)
        negative = f"{UNIVERSAL_NEGATIVE}, {avoid}".strip(", ")

        cinematic_layer = (
            "Add micro-detail for ultrarealism: visible surface wear and "
            "micro-textures, atmospheric particles, specular highlights on "
            "reflective surfaces, and natural contact shadows."
        )

        text_color = (
            self.brand.visual.colors.secondary
            or self.brand.visual.colors.background
            or "#FFFFFF"
        )
        text_font = (
            self.brand.visual.fonts.get("display")
            or self.brand.visual.fonts.get("body")
            or "a clean sans-serif"
        )

        if schema.get("prompt_style") == "five_slot":
            scene = setting or "studio setting consistent with the brand's photography style"
            subject_line = subject + (f", {action}" if action else "")
            important_details = ", ".join(
                filter(None, [composition, brand_style, *creative_direction])
            )
            if detail_mode == "cinematic_verbose":
                important_details = ", ".join(filter(None, [important_details, cinematic_layer]))
            constraints = "positive framing only, no extra elements, no added text unless quoted"
            if avoid:
                constraints += f", avoid: {avoid}"

            additional = {
                "scene": scene,
                "subject": subject_line,
                "important_details": important_details,
                "use_case": use_case,
                "constraints": constraints,
                "quality": "high",
            }
            positive_lines = [
                f"Scene: {scene}",
                f"Subject: {subject_line}",
                f"Important Details: {important_details}",
            ]
            if copy:
                text_line = f'"{copy}" in {text_font}, {text_color}, {copy_position}'
                additional["text"] = text_line
                positive_lines.append(f"Text: {text_line}")
                constraints += ", no extra text, no duplicate text, no watermarks"
                additional["constraints"] = constraints
            positive_lines += [
                f"Use Case: {use_case}",
                f"Constraints: {constraints}",
            ]
            positive = "\n".join(positive_lines)
        else:
            # Nano Banana family — natural-language prose:
            # Subject + Action + Location/context + Composition + Style
            parts = [subject]
            if action:
                parts.append(action)
            if setting:
                parts.append(f"in {setting}")
            if composition:
                parts.append(composition)
            parts.append(f"for {use_case}")
            if brand_style:
                parts.append(brand_style)
            parts.extend(creative_direction)
            if detail_mode == "cinematic_verbose":
                parts.append(cinematic_layer)
            additional = {"detail_mode": detail_mode}
            if copy:
                parts.append(
                    f'In the {copy_position}, render the words "{copy}" in '
                    f'{text_font}, {text_color}, small and restrained, like a caption'
                )
                additional["text"] = copy

            positive = ". ".join(p.strip(". ") for p in parts if p) + f". Format: {ar}."

        return GenerationPrompt(
            tool=tool,
            positive_prompt=positive,
            negative_prompt=negative,
            style=self.brand.visual.photography_style,
            aspect_ratio=ar,
            additional_params=additional,
        )

    def mood_board_description(self, campaign_name: str, tone: str = "") -> str:
        """Generate a mood board description document."""
        v = self.brand.visual
        tone_str = tone or v.mood
        lines = [
            f"# Mood Board: {campaign_name} — {self.brand.name}",
            "",
            "## Visual Direction",
            f"**Photography style**: {v.photography_style}",
            f"**Mood**: {tone_str}",
            "",
            "## Color Palette",
            f"- Primary: {v.colors.primary}",
            f"- Secondary: {v.colors.secondary or 'N/A'}",
            f"- Accent: {v.colors.accent or 'N/A'}",
            "",
            "## Typography",
        ]
        for role, font in v.fonts.items():
            lines.append(f"- {role.capitalize()}: {font}")
        lines += [
            "",
            "## Visual References",
            "- [Add reference images here]",
            "",
            "## Avoid",
        ]
        for avoid in v.avoid_visuals:
            lines.append(f"- {avoid}")
        lines += [
            "",
            "## Generation Prompts",
            f"**Positive style string**: {self._brand_style_string()}",
            f"**Negative (universal)**: {UNIVERSAL_NEGATIVE}",
        ]
        return "\n".join(lines)
