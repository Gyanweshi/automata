"""AI generation prompt writer — structured prompts for image/video tools."""
from __future__ import annotations

from agency_common.models import BrandProfile, GenerationPrompt, Scene


# Supported tool schemas
TOOL_SCHEMAS = {
    "freepik_image": {
        "fields": ["positive_prompt", "negative_prompt", "aspect_ratio", "style"],
        "aspect_ratios": ["1:1", "4:5", "9:16", "16:9", "3:4"],
        "default_aspect": "4:5",
    },
    "freepik_video": {
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
}

UNIVERSAL_NEGATIVE = (
    "blurry, low quality, pixelated, watermark, text, logo, nsfw, "
    "distorted, overexposed, underexposed, noise, grain"
)


class PromptWriter:
    """Generate structured AI generation prompts from scenes and brand context."""

    def __init__(self, brand: BrandProfile):
        self.brand = brand

    def _brand_style_string(self) -> str:
        """Build a reusable brand aesthetic string for all prompts."""
        v = self.brand.visual
        parts = [v.photography_style, v.mood]
        if v.colors.primary:
            parts.append(f"color palette: {v.colors.primary}")
            if v.colors.secondary:
                parts.append(v.colors.secondary)
        return ", ".join(filter(None, parts))

    def scene_to_prompt(
        self,
        scene: Scene,
        tool: str = "freepik_image",
        aspect_ratio: str | None = None,
    ) -> GenerationPrompt:
        """Convert a scene into a generation prompt for the specified tool."""
        schema = TOOL_SCHEMAS.get(tool, TOOL_SCHEMAS["generic"])
        ar = aspect_ratio or schema["default_aspect"]
        brand_style = self._brand_style_string()

        shot_desc = ""
        if scene.shots:
            shot = scene.shots[0]
            shot_desc = (
                f"{shot.shot_type} shot, subject: {shot.subject}, "
                f"{shot.action}, lighting: {shot.lighting}"
            )

        visual_elements = ", ".join(scene.visual_elements) if scene.visual_elements else ""
        positive = (
            f"{scene.description}, {visual_elements}, {shot_desc}, "
            f"mood: {scene.mood}, {brand_style}"
        ).strip(", ")

        # Avoid brand's listed visual avoidances
        avoid = ", ".join(self.brand.visual.avoid_visuals)
        negative = f"{UNIVERSAL_NEGATIVE}, {avoid}".strip(", ")

        additional: dict = {}
        if tool == "freepik_video" and scene.duration_seconds:
            additional["duration"] = scene.duration_seconds
        if tool == "blender" and scene.shots:
            additional["camera_angle"] = scene.shots[0].camera_angle

        return GenerationPrompt(
            tool=tool,
            positive_prompt=positive,
            negative_prompt=negative,
            style=self.brand.visual.photography_style,
            aspect_ratio=ar,
            additional_params=additional,
        )

    def storyboard_prompts(
        self,
        scenes: list[Scene],
        tool: str = "freepik_image",
        aspect_ratio: str | None = None,
    ) -> list[GenerationPrompt]:
        """Generate one prompt per scene."""
        return [self.scene_to_prompt(scene, tool=tool, aspect_ratio=aspect_ratio) for scene in scenes]

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
