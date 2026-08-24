"""StoryboardAgent — orchestrates scene builder and prompt writer for a brand."""
from __future__ import annotations

import logging
from datetime import datetime

from agency_common.config import AgencyConfig
from agency_common.models import BrandProfile, ResearchOutput, StoryboardOutput

from .prompt_writer import PromptWriter
from .scene_builder import SceneBuilder

LOGGER = logging.getLogger(__name__)


class StoryboardAgent:
    """Generate visual storyboards and AI generation prompts for brand content."""

    def __init__(self, config: AgencyConfig | None = None):
        self.config = config or AgencyConfig.from_env()

    def run(
        self,
        brand: BrandProfile,
        content_type: str,
        topic: str,
        tool: str = "freepik_image",
        slide_count: int = 7,
        duration_seconds: int = 30,
        aspect_ratio: str | None = None,
        research: ResearchOutput | None = None,
        setting: str = "",
        action: str = "",
        composition: str = "",
        use_case: str = "",
        copy: str = "",
        copy_position: str = "lower third",
        detail_mode: str = "standard",
    ) -> StoryboardOutput:
        """
        Generate a storyboard for a content piece.

        Args:
            brand:          Brand profile
            content_type:   carousel | reel | post | mood_board
            topic:          Content topic/campaign name
            tool:           AI gen tool: freepik_image | freepik_video | blender | generic
            slide_count:    For carousels — number of slides
            duration_seconds: For reels — length in seconds
            aspect_ratio:   Override default aspect ratio for the tool
            content_type:   carousel | reel | post | mood_board | image
            topic:          Content topic/campaign name (for "image", the subject)
            tool:           AI gen tool: freepik_image | freepik_video | blender | generic |
                            nano_banana_2 | nano_banana_pro | gpt_image_2 |
                            seedance | kling_3 | veo
            slide_count:    For carousels — number of slides
            duration_seconds: For reels — length in seconds
            aspect_ratio:   Override default aspect ratio for the tool
            setting, action, composition, use_case, detail_mode:
                            Additional context for "image" (standalone) prompts.
                            detail_mode: concise | standard | verbose | cinematic_verbose
            copy, copy_position:
                            Optional exact text to render on the image (e.g. a
                            tagline), and where to place it (default "lower third").
        """
        if brand.memory:
            LOGGER.info("Brand memory loaded for %s (%d entries)", brand.slug, len(brand.memory))

        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        scene_builder = SceneBuilder(brand)
        prompt_writer = PromptWriter(brand)

        if content_type == "carousel":
            scenes = scene_builder.breakdown_carousel(topic, slide_count=slide_count)
            prompts = prompt_writer.storyboard_prompts(scenes, tool=tool, aspect_ratio=aspect_ratio or "4:5")
        elif content_type == "reel":
            scenes = scene_builder.breakdown_reel(topic, duration_seconds=duration_seconds)
            prompts = prompt_writer.storyboard_prompts(scenes, tool=tool or "freepik_video", aspect_ratio=aspect_ratio or "9:16")
        elif content_type == "post":
            scenes = scene_builder.breakdown_single_post(topic)
            prompts = prompt_writer.storyboard_prompts(scenes, tool=tool, aspect_ratio=aspect_ratio or "1:1")
        elif content_type == "mood_board":
            scenes = []
            prompts = []
        elif content_type == "image":
            scenes = []
            prompts = [prompt_writer.standalone_image_prompt(
                topic,
                setting=setting,
                action=action,
                composition=composition,
                use_case=use_case,
                copy=copy,
                copy_position=copy_position,
                tool=tool or "nano_banana_2",
                aspect_ratio=aspect_ratio,
                detail_mode=detail_mode,
                visual_dna=research.visual_dna if research else None,
            )]
        else:
            scenes = scene_builder.breakdown_carousel(topic, slide_count=slide_count)
            prompts = prompt_writer.storyboard_prompts(scenes, tool=tool)

        mood_board = ""
        if content_type == "mood_board":
            mood_board = prompt_writer.mood_board_description(topic)
        else:
            mood_board = prompt_writer.mood_board_description(topic)

        output = StoryboardOutput(
            brand_slug=brand.slug,
            run_id=run_id,
            content_type=content_type,
            topic=topic,
            scenes=scenes,
            prompts=prompts,
            mood_board_description=mood_board,
            summary=(
                f"Storyboard for '{topic}' ({brand.name}) — {content_type}, "
                f"{len(scenes)} scenes, {len(prompts)} generation prompts, tool: {tool}"
            ),
        )

        return output
