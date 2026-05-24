"""Write research output to workspace as JSON and markdown."""
from __future__ import annotations

from pathlib import Path

from agency_common.models import ResearchOutput
from agency_common.output_writer import OutputWriter
from agency_common.workspace import WorkspaceManager


def write_research_output(
    output: ResearchOutput,
    workspace: WorkspaceManager,
    markdown_dir: Path | None = None,
) -> tuple[Path, Path | None]:
    """
    Write ResearchOutput to workspace as JSON and optionally as markdown.
    Returns (json_path, md_path).
    """
    json_path = workspace.write("research", output.brand_slug, output)

    md_path = None
    if markdown_dir:
        md_path = markdown_dir / f"{output.run_id}-research.md"
        md_content = _render_markdown(output)
        frontmatter = OutputWriter.standard_frontmatter(
            "research", output.brand_slug, output.run_id,
            tags=["competitor-analysis"] + list(output.platforms.keys()),
        )
        OutputWriter.write_markdown(md_content, md_path, frontmatter)

    return json_path, md_path


def _render_markdown(output: ResearchOutput) -> str:
    lines = [f"# Research Report: {output.brand_slug}", f"**Run ID**: {output.run_id}\n"]

    if output.summary:
        lines += ["## Summary", output.summary, ""]

    for platform, research in output.platforms.items():
        lines.append(f"## {platform.capitalize()}")
        if research.competitors:
            lines.append("### Competitors\n")
            lines.append("| Handle | Followers | Avg Likes | Avg ER% |")
            lines.append("|--------|-----------|-----------|---------|")
            for c in research.competitors:
                lines.append(
                    f"| {c.handle} | {c.follower_count:,} | "
                    f"{c.avg_likes:.0f} | {c.avg_engagement_rate:.2f}% |"
                )
            lines.append("")

        if research.trending_hashtags:
            lines.append("### Trending Hashtags\n")
            lines.append("| Hashtag | Posts | Avg Likes | Direction |")
            lines.append("|---------|-------|-----------|-----------|")
            for h in research.trending_hashtags[:10]:
                lines.append(f"| {h.tag} | {h.post_count} | {h.avg_likes:.0f} | {h.trend_direction} |")
            lines.append("")

        if research.sentiment:
            s = research.sentiment
            lines += [
                "### Audience Sentiment",
                f"- Positive: {s.positive_pct}%",
                f"- Neutral: {s.neutral_pct}%",
                f"- Negative: {s.negative_pct}%",
                f"- Sample size: {s.sample_size} posts",
                "",
            ]

    if output.cross_platform_themes:
        lines.append("## Cross-Platform Content Themes\n")
        for theme in output.cross_platform_themes[:10]:
            lines.append(f"- **{theme.theme}** ({theme.frequency} mentions) — {', '.join(theme.keywords[:3])}")
        lines.append("")

    # ---- Step 1: Community listening node ----
    ln = output.listening_node
    if ln and ln.posts:
        sources_str = ", ".join(ln.sources) or "community"
        lines.append(f"## Community Listening Node ({sources_str})\n")
        lines.append(f"**Posts collected**: {len(ln.posts)}\n")
        if ln.top_questions:
            lines.append("### Top Consumer Questions\n")
            for q in ln.top_questions[:10]:
                lines.append(f"- {q}")
            lines.append("")
        if ln.recurring_debates:
            lines.append("### Recurring Debates\n")
            for d in ln.recurring_debates[:6]:
                lines.append(f"- {d}")
            lines.append("")
        if ln.emerging_keywords:
            lines.append(f"**Emerging keywords**: {', '.join(ln.emerging_keywords[:15])}\n")

    # ---- Step 2: Meta Ad Library ----
    al = output.ad_library
    if al and al.ads:
        lines.append(f"## Meta Ad Library Audit ({len(al.ads)} long-running ads)\n")
        if al.winning_angles:
            lines.append("### Winning Angles (30+ day ads)\n")
            for angle in al.winning_angles[:8]:
                lines.append(f"- {angle}")
            lines.append("")
        if al.top_ctas:
            lines.append(f"**Dominant CTAs**: {', '.join(al.top_ctas[:5])}\n")
        if al.ads[:5]:
            lines.append("### Sample Long-Running Ads\n")
            lines.append("| Page | Days Running | Hook |")
            lines.append("|------|--------------|------|")
            for ad in sorted(al.ads, key=lambda a: a.days_running, reverse=True)[:8]:
                hook = (ad.hook or ad.ad_copy)[:60].replace("|", "/")
                lines.append(f"| {ad.page_name} | {ad.days_running} | {hook} |")
            lines.append("")

    # ---- Step 3: Visual DNA ----
    vd = output.visual_dna
    if vd and vd.dominant_aesthetic:
        lines.append("## Visual DNA\n")
        lines.append(f"| Dimension | Analysis |")
        lines.append(f"|-----------|----------|")
        lines.append(f"| Dominant aesthetic | {vd.dominant_aesthetic} |")
        if vd.color_palette_trend:
            lines.append(f"| Color direction | {vd.color_palette_trend} |")
        if vd.typography_trend:
            lines.append(f"| Typography | {vd.typography_trend} |")
        if vd.pacing_trend:
            lines.append(f"| Pacing | {vd.pacing_trend} |")
        if vd.industry_standard_aesthetic:
            lines.append(f"| Industry standard | {vd.industry_standard_aesthetic} |")
        lines.append("")
        if vd.pattern_interrupt_opportunity:
            lines.append(f"> **Pattern interrupt opportunity**: {vd.pattern_interrupt_opportunity}\n")

    # ---- Step 4: Audience intelligence ----
    ca = output.comment_analysis
    if ca and ca.clusters:
        lines.append("## Audience Intelligence (LLM Analysis)\n")
        for cluster in ca.clusters:
            if not cluster.items:
                continue
            label = cluster.category.replace("_", " ").title()
            lines.append(f"### {label}\n")
            for item in cluster.items:
                lines.append(f"- {item}")
            lines.append("")
        if ca.content_pillars:
            lines.append("### Suggested Content Pillars\n")
            for pillar in ca.content_pillars:
                lines.append(f"- {pillar}")
            lines.append("")

    # ---- Step 5: Adjacency map ----
    ar = output.adjacency_report
    if ar and ar.insights:
        lines.append("## Cross-Industry Adjacency Map\n")
        for insight in ar.insights:
            readiness = insight.readiness_to_cross or "?"
            lines.append(f"### {insight.source_industry} _{readiness}_\n")
            lines.append(f"**Trend**: {insight.trend_or_narrative}")
            lines.append(f"**Adapt as**: {insight.how_to_adapt}\n")
        if ar.top_opportunities:
            lines.append("### Top Opportunities\n")
            for opp in ar.top_opportunities:
                lines.append(f"- {opp}")
            lines.append("")

    lines.append("---\n*Generated by Research Agent. Review before sharing.*")
    return "\n".join(lines)
