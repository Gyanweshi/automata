"""CLI entry point for agency-content.

Usage:
    agency-content --brand my-client --platform instagram --type caption --topic "morning routine"
    agency-content --brand my-client --platform linkedin --type post --topic "hiring announcement"
    agency-content --brand my-client --week
    agency-content --brand my-client --voice-brief
"""
from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agency-content",
        description="Content writing agent — generate structured content briefs in brand voice",
    )
    p.add_argument("--brand", "-b", required=True, help="Brand slug (matches brands/<slug>.yaml)")
    p.add_argument("--platform", choices=["instagram", "linkedin"], default="instagram")
    p.add_argument(
        "--type", "-t", dest="content_type",
        choices=["caption", "carousel", "reel", "post", "article", "document_carousel"],
        default="caption",
    )
    p.add_argument("--topic", default="", help="Content topic or title")
    p.add_argument("--variations", type=int, default=2, help="Number of variations to generate (default: 2)")
    p.add_argument("--week", action="store_true", help="Generate a full week of content briefs")
    p.add_argument("--voice-brief", action="store_true", help="Print the brand voice brief and exit")
    p.add_argument("--workspace", "-w", default=None)
    p.add_argument("--brands-dir", default=None)
    p.add_argument("--no-markdown", action="store_true")
    p.add_argument("--format", choices=["json", "markdown", "summary"], default="summary")
    p.add_argument("--latest", action="store_true", help="Show latest run output")
    p.add_argument("--list", action="store_true", dest="list_runs", help="List past runs")
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
        runs = workspace.list_runs("content", args.brand)
        if not runs:
            print(f"No content runs found for brand '{args.brand}'")
        else:
            for r in runs:
                print(f"  {r.name}")
        return

    if args.latest:
        data = workspace.read_latest("content", args.brand)
        if not data:
            print(f"No content data found for brand '{args.brand}'")
            sys.exit(1)
        print(json.dumps(data, indent=2, default=str))
        return

    try:
        brand = load_brand(args.brand, brands_dir=args.brands_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.voice_brief:
        from .voice import BrandVoiceEngine
        print(BrandVoiceEngine(brand).full_brief())
        return

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

    from .agent import ContentAgent
    from .outputs import write_content_output

    agent = ContentAgent(config=config)

    if args.week:
        output = agent.generate_week(brand, research=research)
    else:
        if not args.topic:
            print("Error: --topic is required unless using --week", file=sys.stderr)
            sys.exit(1)
        output = agent.generate(
            brand,
            platform=args.platform,
            content_type=args.content_type,
            topic=args.topic,
            research=research,
            variations=args.variations,
        )

    md_dir = None if args.no_markdown else workspace.root / "content" / args.brand
    json_path, md_path = write_content_output(output, workspace, markdown_dir=md_dir)
    print(f"Content briefs written: {json_path}")
    if md_path:
        print(f"Markdown: {md_path}")

    if args.format == "json":
        print(json.dumps(output.model_dump(), indent=2, default=str))
    elif args.format == "markdown" and md_path:
        print(md_path.read_text())
    else:
        print(f"\n{output.summary}")
        for piece in output.pieces[:3]:
            print(f"\n  [{piece.platform} / {piece.content_type}] {piece.topic}")
            print(f"  Tags: {' '.join(piece.hashtags[:5]) if piece.hashtags else 'none'}")


if __name__ == "__main__":
    main()
