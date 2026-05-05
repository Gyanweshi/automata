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
        choices=["carousel", "reel", "post", "mood_board"],
        default="carousel",
    )
    p.add_argument("--topic", default="", help="Content topic or campaign name")
    p.add_argument("--slides", type=int, default=7, help="Slide count for carousels (default: 7)")
    p.add_argument("--duration", type=int, default=30, help="Duration in seconds for reels (default: 30)")
    p.add_argument(
        "--tool",
        choices=["freepik_image", "freepik_video", "blender", "generic"],
        default="freepik_image",
        help="AI generation tool to format prompts for",
    )
    p.add_argument("--aspect-ratio", default=None, help="Override aspect ratio (e.g. 4:5, 9:16, 1:1)")
    p.add_argument("--workspace", "-w", default=None)
    p.add_argument("--brands-dir", default=None)
    p.add_argument("--no-markdown", action="store_true")
    p.add_argument("--format", choices=["json", "markdown", "summary", "prompts"], default="summary")
    p.add_argument("--latest", action="store_true")
    p.add_argument("--list", action="store_true", dest="list_runs")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

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

    # Load research if available
    research = None
    research_data = workspace.read_latest("research", args.brand)
    if research_data:
        try:
            from agency_common.models import ResearchOutput
            research = ResearchOutput.model_validate(research_data)
        except Exception:
            pass

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
    )

    md_dir = None if args.no_markdown else workspace.root / "storyboards" / args.brand
    json_path, md_path = write_storyboard_output(output, workspace, brand_profile=brand, markdown_dir=md_dir)
    print(f"Storyboard written: {json_path}")
    if md_path:
        print(f"Markdown: {md_path}")

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
