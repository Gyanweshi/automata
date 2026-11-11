"""Write research output as workspace JSON and a human-readable Markdown note."""
from __future__ import annotations

from pathlib import Path

from agency_common.canvas import CARD_WIDTH, CYAN, PURPLE, Canvas, card_height, section_grid, vault_relative
from agency_common.models import ResearchOutput
from agency_common.output_writer import OutputWriter
from agency_common.workspace import WorkspaceManager


def write_research_output(
    output: ResearchOutput,
    workspace: WorkspaceManager,
    markdown_dir: Path | None = None,
    *,
    status: str = "draft",
    canvas: bool = True,
) -> tuple[Path, Path | None]:
    """
    Write ResearchOutput to workspace as JSON and optionally to a Markdown directory, with a matching
    `.canvas` board beside the note. Returns (json_path, md_path).
    """
    json_path = workspace.write("research", output.brand_slug, output)

    md_path = None
    if markdown_dir:
        md_path = markdown_dir / f"{output.run_id}-research.md"
        md_content = _render_markdown(output)
        frontmatter = OutputWriter.standard_frontmatter(
            "research", output.brand_slug, output.run_id,
            tags=["competitor-analysis"] + list(output.platforms.keys()),
            status=status,
        )
        OutputWriter.write_markdown(md_content, md_path, frontmatter)
        if canvas:
            research_canvas(output, md_path).write(md_path.with_suffix(".canvas"))

    return json_path, md_path


def research_canvas(output: ResearchOutput, md_path: Path) -> Canvas:
    """A board for Obsidian: summary and the full report on top, one group per finding area below."""
    board = Canvas(seed=f"{output.brand_slug}/{output.run_id}/research")
    summary = f"# Research: {output.brand_slug}\n{output.run_id}"
    if output.summary:
        summary += f"\n\n{output.summary}"
    board.text(summary, 0, 0, CARD_WIDTH, color=PURPLE)
    board.file(vault_relative(md_path), CARD_WIDTH + 80, 0, CARD_WIDTH, 400)
    top = max(card_height(summary), 400) + 140
    section_grid(board, _research_sections(output), x=0, y=top, columns=3, color=CYAN)
    return board


def _bullets(items, limit: int = 10) -> str:
    return "\n".join(f"- {item}" for item in list(items)[:limit])


def _research_sections(output: ResearchOutput) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    for platform, research in output.platforms.items():
        cards = []
        if research.competitors:
            rows = ["| Handle | Followers | Avg ER% |", "|---|---|---|"]
            rows += [f"| {c.handle} | {c.follower_count:,} | {c.avg_engagement_rate:.2f}% |"
                     for c in research.competitors[:10]]
            cards.append("**Competitors**\n\n" + "\n".join(rows))
        if research.trending_hashtags:
            cards.append("**Trending hashtags**\n" + _bullets(
                f"{h.tag} ({h.trend_direction})" for h in research.trending_hashtags))
        if research.sentiment:
            s = research.sentiment
            cards.append(f"**Sentiment** ({s.sample_size} posts)\n- Positive {s.positive_pct}%\n"
                         f"- Neutral {s.neutral_pct}%\n- Negative {s.negative_pct}%")
        if cards:
            sections.append((platform.capitalize(), cards))
    if output.cross_platform_themes:
        sections.append(("Themes", [_bullets(
            f"**{t.theme}** ({t.frequency}): {', '.join(t.keywords[:3])}" for t in output.cross_platform_themes)]))
    ln = output.listening_node
    if ln and (ln.top_questions or ln.recurring_debates):
        cards = []
        if ln.top_questions:
            cards.append("**Top questions**\n" + _bullets(ln.top_questions))
        if ln.recurring_debates:
            cards.append("**Recurring debates**\n" + _bullets(ln.recurring_debates, 6))
        sections.append(("Community listening", cards))
    al = output.ad_library
    if al and (al.winning_angles or al.top_ctas):
        cards = []
        if al.winning_angles:
            cards.append("**Winning angles (30+ day ads)**\n" + _bullets(al.winning_angles, 8))
        if al.top_ctas:
            cards.append("**Dominant CTAs**\n" + _bullets(al.top_ctas, 5))
        sections.append(("Ad library", cards))
    vd = output.visual_dna
    if vd and vd.dominant_aesthetic:
        rows = [("Aesthetic", vd.dominant_aesthetic), ("Colour", vd.color_palette_trend),
                ("Typography", vd.typography_trend), ("Pacing", vd.pacing_trend),
                ("Industry standard", vd.industry_standard_aesthetic)]
        card = "\n".join(f"- **{k}**: {v}" for k, v in rows if v)
        if vd.pattern_interrupt_opportunity:
            card += f"\n\n> **Pattern interrupt**: {vd.pattern_interrupt_opportunity}"
        sections.append(("Visual DNA", [card]))
    ca = output.comment_analysis
    if ca and ca.clusters:
        cards = [f"**{c.category.replace('_', ' ').title()}**\n" + _bullets(c.items, 6)
                 for c in ca.clusters if c.items]
        if ca.content_pillars:
            cards.append("**Content pillars**\n" + _bullets(ca.content_pillars))
        if cards:
            sections.append(("Audience", cards))
    ar = output.adjacency_report
    if ar and ar.top_opportunities:
        sections.append(("Adjacent opportunities", [_bullets(ar.top_opportunities)]))
    return sections


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
        lines.append("| Dimension | Analysis |")
        lines.append("|-----------|----------|")
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
