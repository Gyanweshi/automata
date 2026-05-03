"""CLI entry point for agency-research.

Usage:
    agency-research --brand my-client --workspace ./workspace
    agency-research --brand my-client --platforms ig,li --dry-run
    agency-research --brand my-client --latest
    agency-research --brand my-client --list
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agency-research",
        description="Social media research agent — scrape competitors, trends, and sentiment",
    )
    p.add_argument("--brand", "-b", required=True, help="Brand slug (matches brands/<slug>.yaml)")
    p.add_argument(
        "--workspace", "-w",
        default=None,
        help="Path to shared workspace directory (default: $AGENCY_WORKSPACE or ./workspace)",
    )
    p.add_argument(
        "--brands-dir",
        default=None,
        help="Path to brands YAML directory (default: $AGENCY_BRANDS_DIR or ./brands)",
    )
    p.add_argument(
        "--platforms", "-p",
        default=None,
        help="Comma-separated platforms to scrape: ig,li,fb (default: all configured)",
    )
    p.add_argument("--post-count", type=int, default=20, help="Posts to fetch per competitor")
    p.add_argument("--dry-run", action="store_true", help="Validate config without API calls")
    p.add_argument("--latest", action="store_true", help="Show latest run output and exit")
    p.add_argument("--list", action="store_true", dest="list_runs", help="List past runs and exit")
    p.add_argument("--format", choices=["json", "summary"], default="summary", help="Output format")
    p.add_argument("--no-markdown", action="store_true", help="Skip writing markdown output to workspace")
    p.add_argument(
        "--scraper",
        choices=["playwright", "instaloader"],
        default="playwright",
        help="Instagram scraper backend (default: playwright)",
    )
    p.add_argument(
        "--notebooklm",
        action="store_true",
        help="Feed research output into NotebookLM for AI synthesis",
    )
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    from agency_common.brand_loader import load_brand
    from agency_common.config import AgencyConfig
    from agency_common.workspace import WorkspaceManager

    config = AgencyConfig.from_env()
    workspace = WorkspaceManager(workspace_root=args.workspace)

    # --list
    if args.list_runs:
        runs = workspace.list_runs("research", args.brand)
        if not runs:
            print(f"No research runs found for brand '{args.brand}'")
        else:
            print(f"Research runs for '{args.brand}':")
            for r in runs:
                print(f"  {r.name}")
        return

    # --latest
    if args.latest:
        data = workspace.read_latest("research", args.brand)
        if not data:
            print(f"No research data found for brand '{args.brand}'")
            sys.exit(1)
        print(json.dumps(data, indent=2, default=str))
        return

    # Load brand profile
    try:
        brand = load_brand(args.brand, brands_dir=args.brands_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"[dry-run] Brand loaded: {brand.name}")
        print(f"[dry-run] Instagram competitors: {brand.competitors.instagram}")
        print(f"[dry-run] LinkedIn competitors: {brand.competitors.linkedin}")
        print(f"[dry-run] Workspace: {workspace.root.resolve()}")
        print("[dry-run] OK — no API calls made.")
        return

    platforms = None
    if args.platforms:
        platform_map = {"ig": "instagram", "li": "linkedin", "fb": "facebook"}
        platforms = [platform_map.get(p.strip(), p.strip()) for p in args.platforms.split(",")]

    from .agent import ResearchAgent
    from .outputs import write_research_output

    agent = ResearchAgent(config=config, scraper=args.scraper)
    print(f"Running research for '{brand.name}' (scraper: {args.scraper})...")
    output = agent.run(brand, platforms=platforms, post_count=args.post_count)

    # Write to workspace
    md_dir = None if args.no_markdown else workspace.root / "research" / args.brand
    json_path, md_path = write_research_output(output, workspace, markdown_dir=md_dir)
    print(f"Research complete. Output: {json_path}")
    if md_path:
        print(f"Markdown report: {md_path}")

    if args.format == "json":
        print(json.dumps(output.model_dump(), indent=2, default=str))
    else:
        print(f"\n{output.summary}")
        for platform, research in output.platforms.items():
            print(f"\n{platform.upper()}")
            print(f"  Competitors analyzed: {len(research.competitors)}")
            print(f"  Trending hashtags: {len(research.trending_hashtags)}")
            if research.trending_hashtags:
                top = research.trending_hashtags[:5]
                print(f"  Top tags: {', '.join(h.tag for h in top)}")
            if research.sentiment:
                s = research.sentiment
                print(f"  Sentiment: {s.positive_pct}% positive, {s.negative_pct}% negative")

    if args.notebooklm and md_path:
        _run_notebooklm(brand.name, args.brand, md_path)


def _run_notebooklm(brand_name: str, brand_slug: str, md_path: Path):
    """Feed the markdown research report into a NotebookLM notebook."""
    import subprocess
    import shutil

    nlm = shutil.which("notebooklm")
    if not nlm:
        print("\n[notebooklm] notebooklm CLI not found — skipping. Install with: pip install notebooklm-py")
        return

    # Check auth
    auth_result = subprocess.run([nlm, "auth", "check", "--json"], capture_output=True, text=True)
    try:
        auth_data = json.loads(auth_result.stdout)
        checks = auth_data.get("checks", {})
        # token_fetch can be null (not tested) — only the cookie checks matter
        required = ["storage_exists", "json_valid", "cookies_present", "sid_cookie"]
        authenticated = all(checks.get(k) for k in required)
    except Exception:
        authenticated = False

    if not authenticated:
        print("\n[notebooklm] Not authenticated — run 'notebooklm login' then retry with --notebooklm")
        return

    # Create (or reuse) a notebook for this brand
    title = f"Research: {brand_name}"
    print(f"\n[notebooklm] Creating notebook '{title}'...")
    create_result = subprocess.run(
        [nlm, "create", title, "--json"],
        capture_output=True, text=True
    )
    try:
        nb_data = json.loads(create_result.stdout)
        # CLI wraps result under {"notebook": {...}}
        nb_id = (nb_data.get("notebook") or nb_data).get("id", "")
    except Exception:
        print(f"[notebooklm] Failed to create notebook: {create_result.stdout} {create_result.stderr}")
        return

    if not nb_id:
        print("[notebooklm] No notebook ID returned.")
        return

    # Add the markdown report as a source
    print(f"[notebooklm] Adding research report as source ({md_path.name})...")
    add_result = subprocess.run(
        [nlm, "--notebook", nb_id, "source", "add", str(md_path), "--json"],
        capture_output=True, text=True
    )
    try:
        src_data = json.loads(add_result.stdout)
        src_id = src_data.get("source_id", "")
        print(f"[notebooklm] Source added: {src_id} (status: {src_data.get('status', '?')})")
    except Exception:
        print(f"[notebooklm] Source add output: {add_result.stdout}")

    print(f"[notebooklm] Notebook ready. Generate a brief with:")
    print(f"  notebooklm --notebook {nb_id} generate report --format briefing-doc")


if __name__ == "__main__":
    main()
