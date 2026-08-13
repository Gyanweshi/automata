"""Scene breakdown for different content formats."""
from __future__ import annotations

from agency_common.models import BrandProfile, Scene, Shot


class SceneBuilder:
    """Break a content concept into visual scenes."""

    def __init__(self, brand: BrandProfile):
        self.brand = brand

    def breakdown_carousel(self, topic: str, slide_count: int = 7) -> list[Scene]:
        """Generate scene-by-scene breakdown for an Instagram/LinkedIn carousel."""
        scenes: list[Scene] = []

        # Slide 1: Hook
        scenes.append(Scene(
            scene_number=1,
            description=f"Hook slide for: {topic}",
            visual_elements=["Bold typography", "Brand primary color background", "Single powerful image or icon"],
            text_overlay=f"HOOK: [Bold claim about {topic}]",
            mood=self.brand.visual.mood,
            camera_angle="static",
            shots=[Shot(
                shot_number=1,
                shot_type="close-up",
                subject="Typography/graphic",
                action="static",
                lighting=self.brand.visual.photography_style,
                notes="Hook must stop scroll — use brand primary color, max 7 words",
            )],
        ))

        # Middle slides: content points
        middle_count = slide_count - 2
        for i in range(1, middle_count + 1):
            scenes.append(Scene(
                scene_number=i + 1,
                description=f"Content point {i} — {topic}",
                visual_elements=["Icon or illustration", "Short text", "Brand accent color"],
                text_overlay=f"Point {i}: [key insight about {topic}]",
                mood=self.brand.visual.mood,
                camera_angle="medium",
                shots=[Shot(
                    shot_number=1,
                    shot_type="medium",
                    subject=f"Visual for point {i}",
                    action="static",
                    lighting=self.brand.visual.photography_style,
                    notes="One idea per slide. Headline + 1-2 supporting lines max.",
                )],
            ))

        # Last slide: CTA
        scenes.append(Scene(
            scene_number=slide_count,
            description="Call to action / follow prompt",
            visual_elements=["Brand logo", "Clear CTA text", "Social handles"],
            text_overlay="[CTA] + [Follow/Save prompt]",
            mood="inviting, clear",
            camera_angle="static",
            shots=[Shot(
                shot_number=1,
                shot_type="wide",
                subject="Brand CTA graphic",
                action="static",
                lighting="even, bright",
                notes="Include brand colors, logo, and exact handle. Drive a single action.",
            )],
        ))
        return scenes

    def breakdown_reel(self, topic: str, duration_seconds: int = 30) -> list[Scene]:
        """Generate timestamped scene breakdown for a short-form video/reel."""
        scenes: list[Scene] = []

        # Hook: 0-2s
        scenes.append(Scene(
            scene_number=1,
            description=f"Hook: grab attention in first 2 seconds — {topic}",
            visual_elements=["Close-up face or object", "Bold text overlay", "Fast cut or movement"],
            text_overlay="HOOK TEXT OVERLAY",
            mood="energetic, surprising",
            camera_angle="close-up",
            duration_seconds=2,
            shots=[Shot(
                shot_number=1,
                shot_type="close-up",
                subject="Hook visual (face, object, or movement)",
                action="Look into camera OR surprising reveal",
                lighting="bright, clear",
                notes="No context. Jump straight in. First 2s determine whether viewer stays.",
            )],
        ))

        # Setup: 2-7s
        scenes.append(Scene(
            scene_number=2,
            description="Setup — establish the problem or promise",
            visual_elements=["Speaker or graphic explaining context", "Text overlay"],
            text_overlay="[Problem statement or promise]",
            mood="relatable",
            camera_angle="medium",
            duration_seconds=5,
            shots=[Shot(
                shot_number=1,
                shot_type="medium",
                subject="Speaker/presenter",
                action="Speak directly to camera",
                lighting=self.brand.visual.photography_style,
                notes="Brief setup — 1-2 sentences max.",
            )],
        ))

        # Content beats
        remaining = duration_seconds - 7 - 5
        beats = 3
        beat_duration = max(3, remaining // beats)
        t = 7
        for i in range(1, beats + 1):
            end = t + beat_duration
            scenes.append(Scene(
                scene_number=i + 2,
                description=f"Value beat {i} — {topic}",
                visual_elements=["B-roll or talking head", "Text overlay with key point"],
                text_overlay=f"[Key point {i}]",
                mood=self.brand.visual.mood,
                camera_angle="medium",
                duration_seconds=beat_duration,
                shots=[Shot(
                    shot_number=1,
                    shot_type="medium",
                    subject=f"Visual demonstration or speaker for point {i}",
                    action=f"Demonstrate or explain point {i}",
                    lighting=self.brand.visual.photography_style,
                )],
            ))
            t = end

        # Outro/CTA
        scenes.append(Scene(
            scene_number=beats + 3,
            description="CTA — drive action",
            visual_elements=["Speaker to camera", "Text overlay with CTA", "Brand handle"],
            text_overlay="[Follow + specific action CTA]",
            mood="warm, direct",
            camera_angle="medium",
            duration_seconds=5,
            shots=[Shot(
                shot_number=1,
                shot_type="medium",
                subject="Speaker",
                action="Direct CTA delivery to camera",
                lighting="bright, brand colors",
                notes="Be specific: 'Follow for weekly [X]'. Show the value of following.",
            )],
        ))
        return scenes

    def breakdown_single_post(self, topic: str) -> list[Scene]:
        """Single image post — one scene."""
        return [Scene(
            scene_number=1,
            description=f"Single image post: {topic}",
            visual_elements=[
                "Hero image or illustration",
                "Brand color palette",
                "Optional text overlay",
            ],
            text_overlay="[Optional text overlay — keep minimal]",
            mood=self.brand.visual.mood,
            camera_angle="varies",
            shots=[Shot(
                shot_number=1,
                shot_type="varies",
                subject=f"Visual subject for {topic}",
                action="static or candid",
                lighting=self.brand.visual.photography_style,
                notes="Single image must communicate the core idea without a caption.",
            )],
        )]

    def from_script(self, raw_script: list[dict]) -> list[Scene]:
        """Parse a structured list of scenes into Scene and Shot objects."""
        scenes: list[Scene] = []
        for i, scene_data in enumerate(raw_script):
            shots_data = scene_data.get("shots", [])
            shots = []
            for j, shot_data in enumerate(shots_data):
                shots.append(Shot(
                    shot_number=shot_data.get("shot_number", j + 1),
                    shot_type=shot_data.get("shot_type", ""),
                    subject=shot_data.get("subject", ""),
                    action=shot_data.get("action", ""),
                    lighting=shot_data.get("lighting", self.brand.visual.photography_style),
                    props=shot_data.get("props", []),
                    notes=shot_data.get("notes", ""),
                    complexity=shot_data.get("complexity", "simple"),
                ))
            
            scenes.append(Scene(
                scene_number=scene_data.get("scene_number", i + 1),
                description=scene_data.get("description", ""),
                visual_elements=scene_data.get("visual_elements", []),
                text_overlay=scene_data.get("text_overlay", ""),
                mood=scene_data.get("mood", self.brand.visual.mood),
                camera_angle=scene_data.get("camera_angle", ""),
                duration_seconds=scene_data.get("duration_seconds"),
                location=scene_data.get("location", ""),
                shots=shots,
            ))
        return scenes
