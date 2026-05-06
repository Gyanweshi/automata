from agency_common.models import CompetitorAnalysis
from agency_research.scrapers.apify_instagram import ApifyInstagramScraper


def test_apify_item_to_post_maps_common_actor_fields():
    scraper = ApifyInstagramScraper(dry_run=True)

    post = scraper._item_to_post(
        {
            "shortCode": "ABC123",
            "url": "https://www.instagram.com/p/ABC123/",
            "caption": "New drop #design #branding",
            "likesCount": 42,
            "commentsCount": 7,
            "timestamp": "2026-05-06T12:00:00.000Z",
            "hashtags": [{"name": "design"}, {"name": "branding"}],
            "type": "Video",
        }
    )

    assert post is not None
    assert post.platform == "instagram"
    assert post.post_id == "ABC123"
    assert post.likes == 42
    assert post.comments == 7
    assert post.hashtags == ["design", "branding"]
    assert post.media_type == "Video"


def test_apify_build_analysis_calculates_engagement_and_post_metadata():
    scraper = ApifyInstagramScraper(dry_run=True)

    analysis = scraper._build_analysis(
        "brandstudio",
        [
            {
                "shortCode": "ONE",
                "caption": "Launch #creative",
                "likesCount": 100,
                "commentsCount": 10,
                "followersCount": 1000,
                "followingCount": 50,
                "postsCount": 20,
                "biography": "A studio",
                "hashtags": ["creative"],
                "type": "Image",
            },
            {
                "shortCode": "TWO",
                "caption": "Behind the scenes #creative #process",
                "likesCount": 50,
                "commentsCount": 5,
                "hashtags": ["creative", "process"],
                "type": "Video",
            },
        ],
    )

    assert analysis.handle == "brandstudio"
    assert analysis.follower_count == 1000
    assert analysis.following_count == 50
    assert analysis.post_count == 20
    assert analysis.bio == "A studio"
    assert analysis.avg_likes == 75
    assert analysis.avg_comments == 7.5
    assert analysis.avg_engagement_rate == 8.25
    assert analysis.top_hashtags == ["creative", "process"]
    assert analysis.content_types == {"Image": 1, "Video": 1}


def test_apify_research_brand_dry_run_returns_competitor_shells():
    scraper = ApifyInstagramScraper(dry_run=True)

    competitors, hashtag_posts = scraper.research_brand(
        competitor_handles=["@first", "second"],
        hashtags=["niche"],
    )

    assert hashtag_posts == []
    assert competitors == [
        CompetitorAnalysis(handle="first", platform="instagram"),
        CompetitorAnalysis(handle="second", platform="instagram"),
    ]
