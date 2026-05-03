"""StoryboardAgent — orchestrates scene builder and prompt writer for a brand."""
from __future__ import annotations

from datetime import datetime

from agency_common.config import AgencyConfig
from agency_common.models import BrandProfile, ResearchOutput, StoryboardOutput

from .prompt_writer import PromptWriter
from .scene_builder import SceneBuilder
from .shot_list import generate_shot_list


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
        """
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
        else:
            scenes = scene_builder.breakdown_carousel(topic, slide_count=slide_count)
            prompts = prompt_writer.storyboard_prompts(scenes, tool=tool)

        mood_board = ""
        if content_type == "mood_board":
            mood_board = prompt_writer.mood_board_description(topic)
        else:
            mood_board = prompt_writer.mood_board_description(topic)

        return StoryboardOutput(
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
