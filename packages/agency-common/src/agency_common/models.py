"""Shared Pydantic models used as data contracts between all agency agents."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Brand Profile
# ---------------------------------------------------------------------------

class BrandVoice(BaseModel):
    formal_casual: int = Field(5, ge=1, le=10, description="1=extremely formal, 10=extremely casual")
    serious_playful: int = Field(5, ge=1, le=10, description="1=extremely serious, 10=extremely playful")
    technical_simple: int = Field(5, ge=1, le=10, description="1=extremely technical, 10=extremely simple")
    reserved_bold: int = Field(5, ge=1, le=10, description="1=extremely reserved, 10=extremely bold")
    archetype_primary: str = "friend"
    archetype_secondary: Optional[str] = None


class BrandVocabulary(BaseModel):
    use_words: list[str] = Field(default_factory=list)
    avoid_words: list[str] = Field(default_factory=list)
    signature_phrases: list[str] = Field(default_factory=list)


class BrandWritingRules(BaseModel):
    dos: list[str] = Field(default_factory=list)
    donts: list[str] = Field(default_factory=list)
    sentence_max_words: int = Field(0, description="Hard cap on words per sentence. 0 = no limit.")
    banned_constructions: list[str] = Field(default_factory=list, description="Specific sentence patterns to never use.")
    example_captions: list[str] = Field(default_factory=list, description="Real approved captions that anchor the voice.")


class BrandAudience(BaseModel):
    primary: str = ""
    secondary: Optional[str] = None
    pain_points: list[str] = Field(default_factory=list)
    desires: list[str] = Field(default_factory=list)


class BrandColors(BaseModel):
    primary: str = "#000000"
    secondary: Optional[str] = None
    accent: Optional[str] = None
    background: Optional[str] = None


class BrandVisual(BaseModel):
    colors: BrandColors = Field(default_factory=BrandColors)
    fonts: dict[str, str] = Field(default_factory=dict)
    photography_style: str = ""
    mood: str = ""
    avoid_visuals: list[str] = Field(default_factory=list)


class BrandHashtagGroups(BaseModel):
    niche: list[str] = Field(default_factory=list)
    broad: list[str] = Field(default_factory=list)
    branded: list[str] = Field(default_factory=list)


class BrandPlatformConfig(BaseModel):
    handle: str = ""
    content_types: list[str] = Field(default_factory=list)
    posting_frequency: str = ""
    hashtag_groups: BrandHashtagGroups = Field(default_factory=BrandHashtagGroups)


class BrandPlatforms(BaseModel):
    instagram: Optional[BrandPlatformConfig] = None
    linkedin: Optional[BrandPlatformConfig] = None


class BrandCompetitors(BaseModel):
    instagram: list[str] = Field(default_factory=list)
    linkedin: list[str] = Field(default_factory=list)
    facebook: list[str] = Field(default_factory=list)


class BrandContentPillars(BaseModel):
    educational: int = 35
    behind_the_scenes: int = 20
    social_proof: int = 15
    engagement: int = 20
    promotional: int = 10


class BrandCommunityConfig(BaseModel):
    subreddits: list[str] = Field(default_factory=list, description="e.g. ['apple', 'MachineLearning']")
    youtube_channels: list[str] = Field(default_factory=list, description="YouTube channel IDs")
    x_lists: list[str] = Field(default_factory=list, description="Full X/Twitter list URLs")


class BrandMetaAdsConfig(BaseModel):
    keywords: list[str] = Field(default_factory=list, description="Keywords to search in Meta Ad Library")
    countries: list[str] = Field(default_factory=lambda: ["US", "GB", "AU"], description="ISO country codes")


class BrandProfile(BaseModel):
    slug: str
    name: str
    onboarded: str = ""
    voice: BrandVoice = Field(default_factory=BrandVoice)
    vocabulary: BrandVocabulary = Field(default_factory=BrandVocabulary)
    writing: BrandWritingRules = Field(default_factory=BrandWritingRules)
    audience: BrandAudience = Field(default_factory=BrandAudience)
    visual: BrandVisual = Field(default_factory=BrandVisual)
    platforms: BrandPlatforms = Field(default_factory=BrandPlatforms)
    competitors: BrandCompetitors = Field(default_factory=BrandCompetitors)
    content_pillars: BrandContentPillars = Field(default_factory=BrandContentPillars)
    community: BrandCommunityConfig = Field(
        default_factory=BrandCommunityConfig,
        description="Reddit/YouTube/X community listening configuration",
    )
    meta_ads: BrandMetaAdsConfig = Field(
        default_factory=BrandMetaAdsConfig,
        description="Meta Ad Library audit keywords",
    )
    adjacent_industries: list[str] = Field(
        default_factory=list,
        description="Premium adjacent industries to scan for cross-pollination trends",
    )
    memory: list[str] = Field(
        default_factory=list,
        description="Distilled run history — max 10 bullets, always current. "
                    "Parsed from the ## Memory section of the brand .md note.",
    )


# ---------------------------------------------------------------------------
# Research Output
# ---------------------------------------------------------------------------

class PostData(BaseModel):
    platform: str
    post_id: str = ""
    url: str = ""
    caption: str = ""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    timestamp: Optional[str] = None
    hashtags: list[str] = Field(default_factory=list)
    media_type: str = ""
    engagement_rate: float = 0.0


class CompetitorAnalysis(BaseModel):
    handle: str
    platform: str
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    avg_likes: float = 0.0
    avg_comments: float = 0.0
    avg_engagement_rate: float = 0.0
    top_posts: list[PostData] = Field(default_factory=list)
    top_hashtags: list[str] = Field(default_factory=list)
    content_types: dict[str, int] = Field(default_factory=dict)
    posting_frequency: str = ""
    bio: str = ""


class HashtagTrend(BaseModel):
    tag: str
    post_count: int = 0
    avg_likes: float = 0.0
    trend_score: float = 0.0
    trend_direction: str = "stable"


class ContentTheme(BaseModel):
    theme: str
    keywords: list[str] = Field(default_factory=list)
    frequency: int = 0
    platforms: list[str] = Field(default_factory=list)


class SentimentReport(BaseModel):
    positive_pct: float = 0.0
    neutral_pct: float = 0.0
    negative_pct: float = 0.0
    top_positive_themes: list[str] = Field(default_factory=list)
    top_negative_themes: list[str] = Field(default_factory=list)
    sample_size: int = 0


class PlatformResearch(BaseModel):
    platform: str
    scraped_at: str = ""
    competitors: list[CompetitorAnalysis] = Field(default_factory=list)
    trending_hashtags: list[HashtagTrend] = Field(default_factory=list)
    content_themes: list[ContentTheme] = Field(default_factory=list)
    sentiment: Optional[SentimentReport] = None
    raw_posts: list[PostData] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Community Listening Node (Step 1)
# ---------------------------------------------------------------------------

class CommunityPost(BaseModel):
    source: str  # "reddit" | "youtube" | "x"
    subreddit: str = ""
    title: str = ""
    body: str = ""
    url: str = ""
    upvotes: int = 0
    comments: int = 0
    author: str = ""
    timestamp: Optional[str] = None
    score: float = 0.0


class ListeningNodeReport(BaseModel):
    scraped_at: str = ""
    sources: list[str] = Field(default_factory=list)
    posts: list[CommunityPost] = Field(default_factory=list)
    top_questions: list[str] = Field(default_factory=list)
    recurring_debates: list[str] = Field(default_factory=list)
    emerging_keywords: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Meta Ad Library (Step 2)
# ---------------------------------------------------------------------------

class AdLibraryAd(BaseModel):
    ad_id: str = ""
    page_name: str = ""
    started_running: Optional[str] = None
    days_running: int = 0
    impressions_lower: int = 0
    impressions_upper: int = 0
    ad_copy: str = ""
    cta: str = ""
    hook: str = ""
    visual_description: str = ""
    url: str = ""


class AdLibraryReport(BaseModel):
    scraped_at: str = ""
    keywords_searched: list[str] = Field(default_factory=list)
    ads: list[AdLibraryAd] = Field(default_factory=list)
    top_hooks: list[str] = Field(default_factory=list)
    top_ctas: list[str] = Field(default_factory=list)
    winning_angles: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Visual DNA (Step 3)
# ---------------------------------------------------------------------------

class VisualDNA(BaseModel):
    analyzed_at: str = ""
    dominant_aesthetic: str = ""
    color_palette_trend: str = ""
    typography_trend: str = ""
    pacing_trend: str = ""
    industry_standard_aesthetic: str = ""
    pattern_interrupt_opportunity: str = ""
    raw_analysis: str = ""


# ---------------------------------------------------------------------------
# Comment / Audience Analysis (Step 4)
# ---------------------------------------------------------------------------

class CommentCluster(BaseModel):
    category: str  # "fears" | "recurring_questions" | "knowledge_gaps" | "desires"
    items: list[str] = Field(default_factory=list)
    sentiment: str = ""


class CommentAnalysis(BaseModel):
    analyzed_at: str = ""
    source_posts: list[str] = Field(default_factory=list)
    comment_count: int = 0
    clusters: list[CommentCluster] = Field(default_factory=list)
    content_pillars: list[str] = Field(default_factory=list)
    raw_analysis: str = ""


# ---------------------------------------------------------------------------
# Cross-Industry Adjacency Mapping (Step 5)
# ---------------------------------------------------------------------------

class AdjacencyInsight(BaseModel):
    source_industry: str
    trend_or_narrative: str = ""
    how_to_adapt: str = ""
    readiness_to_cross: str = ""  # "peaked" | "crossing now" | "emerging"


class AdjacencyReport(BaseModel):
    analyzed_at: str = ""
    adjacent_industries: list[str] = Field(default_factory=list)
    insights: list[AdjacencyInsight] = Field(default_factory=list)
    top_opportunities: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Research Output
# ---------------------------------------------------------------------------

class ResearchOutput(BaseModel):
    brand_slug: str
    run_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    platforms: dict[str, PlatformResearch] = Field(default_factory=dict)
    cross_platform_trends: list[HashtagTrend] = Field(default_factory=list)
    cross_platform_themes: list[ContentTheme] = Field(default_factory=list)
    listening_node: Optional[ListeningNodeReport] = None
    ad_library: Optional[AdLibraryReport] = None
    visual_dna: Optional[VisualDNA] = None
    comment_analysis: Optional[CommentAnalysis] = None
    adjacency_report: Optional[AdjacencyReport] = None
    summary: str = ""


# ---------------------------------------------------------------------------
# Storyboard Output
# ---------------------------------------------------------------------------

class Shot(BaseModel):
    shot_number: int
    shot_type: str = ""
    subject: str = ""
    action: str = ""
    lighting: str = ""
    props: list[str] = Field(default_factory=list)
    notes: str = ""


class Scene(BaseModel):
    scene_number: int
    description: str = ""
    visual_elements: list[str] = Field(default_factory=list)
    text_overlay: str = ""
    mood: str = ""
    camera_angle: str = ""
    duration_seconds: Optional[int] = None
    shots: list[Shot] = Field(default_factory=list)


class GenerationPrompt(BaseModel):
    tool: str = ""
    positive_prompt: str = ""
    negative_prompt: str = ""
    style: str = ""
    aspect_ratio: str = "1:1"
    additional_params: dict[str, Any] = Field(default_factory=dict)


class StoryboardOutput(BaseModel):
    brand_slug: str
    run_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    content_type: str = ""
    topic: str = ""
    scenes: list[Scene] = Field(default_factory=list)
    prompts: list[GenerationPrompt] = Field(default_factory=list)
    mood_board_description: str = ""
    summary: str = ""


# ---------------------------------------------------------------------------
# Content Output
# ---------------------------------------------------------------------------

class ContentPiece(BaseModel):
    platform: str
    content_type: str = ""
    topic: str = ""
    body: str = ""
    hashtags: list[str] = Field(default_factory=list)
    cta: str = ""
    notes: str = ""
    variation_index: int = 1


class ContentOutput(BaseModel):
    brand_slug: str
    run_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    pieces: list[ContentPiece] = Field(default_factory=list)
    summary: str = ""
