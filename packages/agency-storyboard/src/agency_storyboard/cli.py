"""CLI entry point for agency-storyboard.

Usage:
    agency-storyboard --brand my-client --type carousel --topic "5 productivity hacks" --slides 7
    agency-storyboard --brand my-client --type reel --topic "day in the life" --duration 30
    agency-storyboard --brand my-client --type mood-board --topic "summer campaign"
    agency-storyboard --brand my-client --latest
"""
from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agency-storyboard",
        description="Storyboard agent — visual planning and AI prompt generation for brand content",
    )
    p.add_argument("--brand", "-b", required=True, help="Brand slug")
    p.add_argument(
        "--type", "-t", dest="content_type",
        choices=["carousel", "reel", "post", "mood_board", "image"],
        default="carousel",
    )
    p.add_argument("--topic", default="", help="Content topic or campaign name (subject, for --type image)")
    p.add_argument("--slides", type=int, default=7, help="Slide count for carousels (default: 7)")
    p.add_argument("--duration", type=int, default=30, help="Duration in seconds for reels (default: 30)")
    p.add_argument(
        "--tool",
        choices=[
            "freepik_image", "freepik_video", "blender", "generic",
            "nano_banana_2", "nano_banana_pro", "gpt_image_2",
            "seedance", "kling_3", "veo",
        ],
        default="freepik_image",
        help="AI generation tool to format prompts for",
    )
    p.add_argument(
        "--aspect-ratio", default=None,
        help=(
            "Override aspect ratio (e.g. 4:5, 9:16, 1:1). If omitted for --type image, "
            "it's derived from --use-case (e.g. 'Instagram static post' -> 4:5, "
            "'Instagram story'/'reel' -> 9:16, 'LinkedIn post' -> 1.91:1)."
        ),
    )
    p.add_argument("--setting", default="", help="(--type image) Location/environment for the shot")
    p.add_argument("--action", default="", help="(--type image) What the subject is doing")
    p.add_argument("--composition", default="", help="(--type image) Camera angle/framing/composition notes")
    p.add_argument(
        "--use-case", default="",
        help=(
            "(--type image) e.g. 'Instagram static post', 'Instagram story', "
            "'LinkedIn post', 'product listing'. Also drives the default aspect "
            "ratio unless --aspect-ratio is set."
        ),
    )
    p.add_argument(
        "--detail-mode",
        choices=["concise", "standard", "verbose", "cinematic_verbose"],
        default="standard",
        help="(--type image) cinematic_verbose adds ultrarealism micro-detail layer",
    )
    p.add_argument(
        "--copy", default="",
        help="(--type image) Exact text/tagline to render on the image, in the brand's font",
    )
    p.add_argument(
        "--copy-position", default="lower third",
        help="(--type image) Where to place --copy on the image (default: 'lower third')",
    )
    p.add_argument("--workspace", "-w", default=None)
    p.add_argument("--brands-dir", default=None)
    p.add_argument("--no-markdown", action="store_true")
    p.add_argument("--commit-vault", action="store_true", help="Write the Markdown note as final and update brand Memory.")
    p.add_argument("--commit-reason", help="Required approval/finalization reason for --commit-vault.")
    p.add_argument("--format", choices=["json", "markdown", "summary", "prompts"], default="summary")
    p.add_argument("--latest", action="store_true")
    p.add_argument("--list", action="store_true", dest="list_runs")
    return p


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()
    if args.commit_vault and not (args.commit_reason or "").strip():
        parser.error("--commit-reason is required with --commit-vault")
    if args.commit_vault and args.no_markdown:
        parser.error("--no-markdown cannot be combined with --commit-vault")

    from agency_common.brand_loader import load_brand
    from agency_common.config import AgencyConfig
    from agency_common.workspace import WorkspaceManager

    config = AgencyConfig.from_env()
    workspace = WorkspaceManager(workspace_root=args.workspace)

    if args.list_runs:
        runs = workspace.list_runs("storyboards", args.brand)
        if not runs:
            print(f"No storyboard runs found for brand '{args.brand}'")
        else:
            for r in runs:
                print(f"  {r.name}")
        return

    if args.latest:
        data = workspace.read_latest("storyboards", args.brand)
        if not data:
            print(f"No storyboard data found for brand '{args.brand}'")
            sys.exit(1)
        print(json.dumps(data, indent=2, default=str))
        return

    try:
        brand = load_brand(args.brand, brands_dir=args.brands_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not args.topic:
        print("Error: --topic is required", file=sys.stderr)
        sys.exit(1)

    if args.content_type == "image" and args.tool in ("freepik_image", "freepik_video", "blender", "generic"):
        args.tool = "nano_banana_2"

    # Load research if available
    research = None
    research_data = workspace.read_latest("research", args.brand)
    if research_data:
        try:
            from agency_common.models import ResearchOutput
            research = ResearchOutput.model_validate(research_data)
        except Exception as e:
            import os
            import logging
            if os.environ.get("AGENCY_DEBUG") == "1":
                logging.getLogger(__name__).error(e, exc_info=True)

    from .agent import StoryboardAgent
    from .outputs import write_storyboard_output

    agent = StoryboardAgent(config=config)
    output = agent.run(
        brand,
        content_type=args.content_type,
        topic=args.topic,
        tool=args.tool,
        slide_count=args.slides,
        duration_seconds=args.duration,
        aspect_ratio=args.aspect_ratio,
        research=research,
        setting=args.setting,
        action=args.action,
        composition=args.composition,
        use_case=args.use_case,
        copy=args.copy,
        copy_position=args.copy_position,
        detail_mode=args.detail_mode,
    )

    note_status = "final" if args.commit_vault else "draft"
    if args.no_markdown:
        md_dir = None
    else:
        from agency_common.output_writer import OutputWriter
        md_dir = OutputWriter.vault_markdown_directory(
            args.brand,
            "Storyboards",
            status=note_status,
            vault_path=config.obsidian_vault_path,
        )
    json_path, md_path = write_storyboard_output(
        output,
        workspace,
        brand_profile=brand,
        markdown_dir=md_dir,
        status=note_status,
    )
    print(f"Storyboard written: {json_path}")
    if md_path:
        print(f"Markdown: {md_path}")

    if args.commit_vault:
        from agency_common.obsidian_writer import update_brand_memory
        update_brand_memory(
            brand_slug=brand.slug,
            insight=(
                f"Storyboard finalized: {args.content_type} for '{args.topic}' — "
                f"{len(output.scenes)} scenes, tool: {args.tool}."
            ),
            commit_vault=True,
            commit_reason=args.commit_reason,
        )
        print("Vault finalization committed.")

    if args.format == "json":
        print(json.dumps(output.model_dump(), indent=2, default=str))
    elif args.format == "markdown" and md_path:
        print(md_path.read_text())
    elif args.format == "prompts":
        print(f"\n{'='*60}")
        print("GENERATION PROMPTS")
        print('='*60)
        for i, p in enumerate(output.prompts, 1):
            print(f"\n--- Prompt {i} ({p.tool} | {p.aspect_ratio}) ---")
            print(f"POSITIVE: {p.positive_prompt}")
            print(f"NEGATIVE: {p.negative_prompt}")
    else:
        print(f"\n{output.summary}")
        print(f"Scenes: {len(output.scenes)} | Prompts: {len(output.prompts)}")
        if output.prompts:
            print("\nFirst prompt preview:")
            print(f"  {output.prompts[0].positive_prompt[:120]}...")


if __name__ == "__main__":
    main()
