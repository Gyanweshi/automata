"""Write storyboard output as workspace JSON and a human-readable Markdown note."""
from __future__ import annotations

from pathlib import Path

from agency_common.canvas import CARD_WIDTH, CYAN, PURPLE, Canvas, card_height, section_grid, vault_relative
from agency_common.models import StoryboardOutput
from agency_common.output_writer import OutputWriter
from agency_common.workspace import WorkspaceManager

from .shot_list import format_shot_list_markdown, generate_shot_list


def write_storyboard_output(
    output: StoryboardOutput,
    workspace: WorkspaceManager,
    brand_profile=None,
    markdown_dir: Path | None = None,
    *,
    status: str = "draft",
    canvas: bool = True,
) -> tuple[Path, Path | None]:
    """Write StoryboardOutput JSON to workspace, plus optional Markdown and a matching `.canvas` board."""
    json_path = workspace.write("storyboards", output.brand_slug, output)

    md_path = None
    if markdown_dir:
        md_path = markdown_dir / f"{output.run_id}-storyboard.md"
        md_content = _render_markdown(output, brand_profile)
        frontmatter = OutputWriter.standard_frontmatter(
            "storyboard", output.brand_slug, output.run_id,
            tags=[output.content_type, "visual"],
            status=status,
        )
        OutputWriter.write_markdown(md_content, md_path, frontmatter)
        if canvas:
            storyboard_canvas(output, md_path).write(md_path.with_suffix(".canvas"))

    return json_path, md_path


def storyboard_canvas(output: StoryboardOutput, md_path: Path) -> Canvas:
    """A board for Obsidian: the brief and the note on top, scenes left to right, each prompt under its scene."""
    board = Canvas(seed=f"{output.brand_slug}/{output.run_id}/storyboard")
    brief = [f"# {output.topic or 'Storyboard'}",
             f"{output.brand_slug} · {output.content_type} · {len(output.scenes)} scenes"]
    if output.summary:
        brief += ["", output.summary]
    if output.mood_board_description:
        brief += ["", "**Mood board**", output.mood_board_description]
    brief_text = "\n".join(brief)
    board.text(brief_text, 0, 0, CARD_WIDTH, color=PURPLE)
    board.file(vault_relative(md_path), CARD_WIDTH + 80, 0, CARD_WIDTH, 400)
    top = max(card_height(brief_text), 400) + 140

    paired = len(output.prompts) == len(output.scenes)
    sections = []
    for index, scene in enumerate(output.scenes):
        cards = [_scene_card(scene)]
        if paired:
            cards.append(_prompt_card(output.prompts[index]))
        sections.append((f"Scene {scene.scene_number}", cards))
    columns = len(sections) if len(sections) <= 8 else 6
    groups = section_grid(board, sections, x=0, y=top, columns=max(columns, 1), color=CYAN)
    for left, right in zip(groups, groups[1:]):
        board.edge(left, right, from_side="right", to_side="left")

    if output.prompts and not paired:
        bottom = max((n["y"] + n["height"] for n in board.to_dict()["nodes"]), default=top)
        section_grid(board, [("Generation prompts", [_prompt_card(p) for p in output.prompts])],
                     x=0, y=bottom + 140, columns=1)
    return board


def _scene_card(scene) -> str:
    lines = [f"### Scene {scene.scene_number}", scene.description or "", ""]
    for label, value in (("Mood", scene.mood), ("Camera", scene.camera_angle), ("Location", scene.location)):
        if value:
            lines.append(f"- **{label}**: {value}")
    if scene.text_overlay:
        lines.append(f"- **Text overlay**: `{scene.text_overlay}`")
    if scene.visual_elements:
        lines.append(f"- **Visual elements**: {', '.join(scene.visual_elements)}")
    if scene.duration_seconds:
        lines.append(f"- **Duration**: {scene.duration_seconds}s")
    return "\n".join(lines).strip()


def _prompt_card(prompt) -> str:
    lines = [f"**Prompt** · {prompt.tool or 'any tool'} · {prompt.aspect_ratio}", "", prompt.positive_prompt]
    if prompt.negative_prompt:
        lines += ["", f"*Negative*: {prompt.negative_prompt}"]
    return "\n".join(lines).strip()


def _render_markdown(output: StoryboardOutput, brand_profile=None) -> str:
    lines = [
        f"# Storyboard: {output.topic}",
        f"**Brand**: {output.brand_slug} | **Type**: {output.content_type} | **Run**: {output.run_id}",
        "",
        output.summary,
        "",
    ]

    if output.scenes:
        lines.append("## Scenes\n")
        for scene in output.scenes:
            lines += [
                f"### Scene {scene.scene_number}: {scene.description}",
                f"- **Mood**: {scene.mood}",
                f"- **Camera**: {scene.camera_angle}",
                f"- **Text overlay**: `{scene.text_overlay}`",
                f"- **Visual elements**: {', '.join(scene.visual_elements)}",
            ]
            if scene.duration_seconds:
                lines.append(f"- **Duration**: {scene.duration_seconds}s")
            lines.append("")

        if brand_profile:
            from agency_common.models import BrandProfile
            if isinstance(brand_profile, BrandProfile):
                shot_list = generate_shot_list(output.scenes, brand_profile)
                lines += ["## Shot List\n", format_shot_list_markdown(shot_list), ""]

    if output.prompts:
        lines.append("## Generation Prompts\n")
        for i, p in enumerate(output.prompts, 1):
            lines += [
                f"### Prompt {i} ({p.tool} — {p.aspect_ratio})",
                f"**Positive**: {p.positive_prompt}",
                f"**Negative**: {p.negative_prompt}",
            ]
            if p.additional_params:
                for k, v in p.additional_params.items():
                    lines.append(f"**{k}**: {v}")
            lines.append("")

    if output.mood_board_description:
        lines += ["## Mood Board", output.mood_board_description, ""]

    lines.append("---\n*Generated by Storyboard Agent. Review before production.*")
    return "\n".join(lines)
