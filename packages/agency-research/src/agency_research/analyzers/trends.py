"""Trend detection across scraped social media data."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from agency_common.models import ContentTheme, HashtagTrend, PostData


class TrendAnalyzer:
    """Detect trending hashtags, formats, and content themes from posts."""

    def trending_hashtags(
        self, posts: list[PostData], top_n: int = 20
    ) -> list[HashtagTrend]:
        """Identify trending hashtags weighted by frequency and recency."""
        tag_posts: dict[str, list[PostData]] = {}
        for post in posts:
            for tag in post.hashtags:
                tag_lower = tag.lower().lstrip("#")
                tag_posts.setdefault(tag_lower, []).append(post)

        trends = []
        for tag, tagged_posts in tag_posts.items():
            avg_likes = sum(p.likes for p in tagged_posts) / len(tagged_posts)
            # Recency score: posts in the last 7 days get a boost
            recent_count = 0
            try:
                now = datetime.now(timezone.utc)
                for p in tagged_posts:
                    if p.timestamp:
                        ts = datetime.fromisoformat(p.timestamp.replace("Z", "+00:00"))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        if (now - ts).days <= 7:
                            recent_count += 1
            except Exception:
                pass
            trend_score = len(tagged_posts) * (1 + recent_count * 0.5)
            trends.append(HashtagTrend(
                tag=f"#{tag}",
                post_count=len(tagged_posts),
                avg_likes=round(avg_likes, 1),
                trend_score=round(trend_score, 2),
                trend_direction="rising" if recent_count > len(tagged_posts) * 0.4 else "stable",
            ))
        trends.sort(key=lambda t: t.trend_score, reverse=True)
        return trends[:top_n]

    def content_themes(
        self, posts: list[PostData], top_n: int = 10
    ) -> list[ContentTheme]:
        """Identify recurring content themes using keyword frequency."""
        # Simple TF-based theme extraction — no heavy NLP dependencies
        STOP_WORDS = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "shall", "can", "i", "you",
            "he", "she", "it", "we", "they", "my", "your", "our", "their",
            "this", "that", "these", "those", "from", "by", "as", "up",
            "out", "so", "if", "not", "no", "all", "any", "get", "just",
        }
        word_counter: Counter = Counter()
        word_platforms: dict[str, set[str]] = {}
        for post in posts:
            words = post.caption.lower().split()
            clean = [
                w.strip(".,!?#@\"'()[]") for w in words
                if len(w) > 3 and w.strip(".,!?#@\"'()[]") not in STOP_WORDS
            ]
            for word in set(clean):
                word_counter[word] += 1
                word_platforms.setdefault(word, set()).add(post.platform)

        themes = []
        seen_words: set[str] = set()
        for word, count in word_counter.most_common(top_n * 3):
            if word in seen_words or count < 2:
                continue
            # Group semantically similar words (basic: check for prefix overlap)
            related = [w for w in word_counter if w != word and (
                w.startswith(word[:4]) or word.startswith(w[:4])
            ) and w not in seen_words]
            keywords = [word] + related[:4]
            for k in keywords:
                seen_words.add(k)
            themes.append(ContentTheme(
                theme=word,
                keywords=keywords,
                frequency=count,
                platforms=list(word_platforms.get(word, set())),
            ))
            if len(themes) >= top_n:
                break
        return themes

    def format_distribution(self, posts: list[PostData]) -> dict[str, float]:
        """Return percentage breakdown of content types/formats."""
        if not posts:
            return {}
        counter: Counter = Counter(p.media_type or "unknown" for p in posts)
        total = len(posts)
        return {fmt: round(cnt / total * 100, 1) for fmt, cnt in counter.most_common()}
