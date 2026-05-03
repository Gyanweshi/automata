"""Lexicon-based sentiment analysis for social media comments/captions."""
from __future__ import annotations

from collections import Counter

from agency_common.models import PostData, SentimentReport


# Expanded sentiment lexicons
POSITIVE_WORDS = {
    "love", "great", "amazing", "awesome", "fantastic", "wonderful", "excellent",
    "best", "beautiful", "perfect", "happy", "joy", "brilliant", "outstanding",
    "helpful", "inspiring", "motivated", "excited", "grateful", "incredible",
    "stunning", "fabulous", "superb", "delightful", "thank", "thanks", "congratulations",
    "congrats", "wow", "impressive", "recommend", "recommended", "must", "genius",
    "magnificent", "terrific", "splendid", "marvelous", "phenomenal", "exceptional",
    "top", "good", "nice", "cool", "fire", "solid", "valuable", "useful", "helpful",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "horrible", "worst", "hate", "disgusting", "useless",
    "waste", "disappointed", "disappointing", "poor", "boring", "overrated",
    "scam", "fake", "misleading", "frustrating", "annoying", "broken", "wrong",
    "fail", "failed", "failure", "ridiculous", "pathetic", "mediocre", "trash",
    "rubbish", "garbage", "spam", "clickbait", "mislead", "stupid", "nonsense",
    "terrible", "nightmare", "problem", "issue", "complaint", "refund",
}


class SentimentAnalyzer:
    """Lexicon-based sentiment analysis. No external ML dependencies."""

    def score_text(self, text: str) -> float:
        """Return sentiment score: positive > 0, negative < 0, neutral = 0."""
        words = text.lower().split()
        score = 0
        for word in words:
            clean = word.strip(".,!?#@\"'()[]")
            if clean in POSITIVE_WORDS:
                score += 1
            elif clean in NEGATIVE_WORDS:
                score -= 1
        return score

    def classify(self, score: float) -> str:
        if score > 0:
            return "positive"
        elif score < 0:
            return "negative"
        return "neutral"

    def analyze_posts(self, posts: list[PostData]) -> SentimentReport:
        """Analyze sentiment across a collection of posts/captions."""
        if not posts:
            return SentimentReport(sample_size=0)

        scores = [(post, self.score_text(post.caption)) for post in posts]
        positive = [p for p, s in scores if s > 0]
        negative = [p for p, s in scores if s < 0]
        neutral = [p for p, s in scores if s == 0]
        total = len(posts)

        # Extract common positive/negative themes
        pos_words: Counter = Counter()
        neg_words: Counter = Counter()
        for post, score in scores:
            words = post.caption.lower().split()
            clean_words = [w.strip(".,!?#@\"'()[]") for w in words]
            if score > 0:
                for w in clean_words:
                    if w in POSITIVE_WORDS:
                        pos_words[w] += 1
            elif score < 0:
                for w in clean_words:
                    if w in NEGATIVE_WORDS:
                        neg_words[w] += 1

        return SentimentReport(
            positive_pct=round(len(positive) / total * 100, 1),
            neutral_pct=round(len(neutral) / total * 100, 1),
            negative_pct=round(len(negative) / total * 100, 1),
            top_positive_themes=[w for w, _ in pos_words.most_common(5)],
            top_negative_themes=[w for w, _ in neg_words.most_common(5)],
            sample_size=total,
        )
