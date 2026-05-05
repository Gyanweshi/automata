"""Shot list generator — expands scenes into production-ready shots."""
from __future__ import annotations

from agency_common.models import BrandProfile, Scene


def generate_shot_list(scenes: list[Scene], brand: BrandProfile) -> list[dict]:
    """Expand scenes into a production shot list with full details."""
    shot_list = []
    for scene in scenes:
        for shot in scene.shots:
            shot_list.append({
                "scene": scene.scene_number,
                "shot": shot.shot_number,
                "shot_type": shot.shot_type,
                "description": scene.description,
                "subject": shot.subject,
                "action": shot.action,
                "duration_s": scene.duration_seconds,
                "lighting": shot.lighting or brand.visual.photography_style,
                "mood": scene.mood,
                "text_overlay": scene.text_overlay,
                "visual_elements": scene.visual_elements,
                "brand_colors": [
                    brand.visual.colors.primary,
                    brand.visual.colors.secondary or "",
                    brand.visual.colors.accent or "",
                ],
                "props": shot.props,
                "notes": shot.notes,
            })
    return shot_list


def format_shot_list_markdown(shot_list: list[dict]) -> str:
    """Render a shot list as a markdown table."""
    if not shot_list:
        return "*No shots.*"
    lines = [
        "| Scene | Shot | Type | Subject | Action | Duration | Notes |",
        "|-------|------|------|---------|--------|----------|-------|",
    ]
    for s in shot_list:
        duration = f"{s['duration_s']}s" if s.get("duration_s") else "-"
        notes = s.get("notes", "")[:50]
        lines.append(
            f"| {s['scene']} | {s['shot']} | {s['shot_type']} | "
            f"{s['subject'][:30]} | {s['action'][:30]} | {duration} | {notes} |"
        )
    return "\n".join(lines)
