"""Meta Ad Library scraper — finds active ads running 30+ days to surface winning angles.

Step 2 of the deep research pipeline: audit what brands are *paying* to push. Long-running
ads prove a specific hook, angle, or visual style is converting — not just trending.

Authentication options (in priority order):
  1. META_AD_LIBRARY_TOKEN — Facebook access token with ads_read permission
  2. APIFY_API_TOKEN       — Falls back to Apify curious_coder/facebook-ads-scraper
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta

import requests

from agency_common.models import AdLibraryAd, AdLibraryReport

LOGGER = logging.getLogger(__name__)

GRAPH_API_VERSION = "v19.0"
AD_ARCHIVE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/ads_archive"


class MetaAdsLibraryScraper:
    """Scrape Meta Ad Library for active ads running 30+ days."""

    def __init__(
        self,
        access_token: str = "",
        apify_token: str = "",
        dry_run: bool = False,
    ):
        self.access_token = access_token
        self.apify_token = apify_token
        self.dry_run = dry_run

    def audit(
        self,
        keywords: list[str],
        countries: list[str] | None = None,
        min_days_running: int = 30,
        limit_per_keyword: int = 20,
    ) -> AdLibraryReport:
        """Return long-running ads matching keywords with winning angles extracted."""
        if not keywords:
            return AdLibraryReport(scraped_at=datetime.utcnow().isoformat())

        if self.dry_run:
            LOGGER.info("[dry-run] Meta Ad Library audit: keywords=%s", keywords)
            return AdLibraryReport(
                scraped_at=datetime.utcnow().isoformat(),
                keywords_searched=keywords,
            )

        if countries is None:
            countries = ["US", "GB", "AU", "IN"]

        # Only look for ads that started at least min_days_running ago
        cutoff_date = (datetime.utcnow() - timedelta(days=min_days_running)).strftime("%Y-%m-%d")
        all_ads: list[AdLibraryAd] = []

        for keyword in keywords:
            if self.access_token:
                ads = self._fetch_via_graph_api(keyword, countries, cutoff_date, limit_per_keyword)
            else:
                ads = self._fetch_via_apify(keyword, limit_per_keyword)
            all_ads.extend(ads)

        return self._build_report(keywords, all_ads, min_days_running)

    # ------------------------------------------------------------------
    # Graph API path (preferred — requires FB token with ads_read)
    # ------------------------------------------------------------------

    def _fetch_via_graph_api(
        self,
        keyword: str,
        countries: list[str],
        ad_delivery_date_max: str,
        limit: int,
    ) -> list[AdLibraryAd]:
        params = {
            "access_token": self.access_token,
            "search_terms": keyword,
            "ad_reached_countries": ",".join(countries),
            "ad_active_status": "ACTIVE",
            "ad_delivery_date_max": ad_delivery_date_max,
            "fields": (
                "id,page_name,ad_delivery_start_time,"
                "ad_creative_bodies,ad_creative_link_titles,"
                "ad_creative_link_captions,impressions"
            ),
            "limit": str(limit),
        }
        try:
            resp = requests.get(AD_ARCHIVE_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            ads = [self._parse_graph_ad(item) for item in data.get("data", [])]
            LOGGER.info("Meta Ad Library (Graph API): %d ads for '%s'", len(ads), keyword)
            return ads
        except Exception as exc:
            LOGGER.error("Meta Ad Library Graph API error for '%s': %s", keyword, exc)
            return []

    def _parse_graph_ad(self, item: dict) -> AdLibraryAd:
        start_date = item.get("ad_delivery_start_time", "")
        days_running = 0
        if start_date:
            try:
                started = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                days_running = (datetime.now(tz=started.tzinfo) - started).days
            except Exception as e:
                import os, logging
                if os.environ.get("AGENCY_DEBUG") == "1":
                    logging.getLogger(__name__).error(e, exc_info=True)

        bodies = item.get("ad_creative_bodies") or []
        titles = item.get("ad_creative_link_titles") or []
        captions = item.get("ad_creative_link_captions") or []

        ad_copy = " | ".join(filter(None, bodies[:2]))
        hook = bodies[0][:200] if bodies else (titles[0][:200] if titles else "")
        cta = captions[0] if captions else ""

        impressions = item.get("impressions") or {}
        imp_lower = int(impressions.get("lower_bound", 0) or 0)
        imp_upper = int(impressions.get("upper_bound", 0) or 0)

        return AdLibraryAd(
            ad_id=str(item.get("id", "")),
            page_name=item.get("page_name", ""),
            started_running=start_date,
            days_running=days_running,
            impressions_lower=imp_lower,
            impressions_upper=imp_upper,
            ad_copy=ad_copy,
            cta=cta,
            hook=hook,
            url=f"https://www.facebook.com/ads/library/?id={item.get('id', '')}",
        )

    # ------------------------------------------------------------------
    # Apify fallback (no Graph API token needed)
    # ------------------------------------------------------------------

    def _fetch_via_apify(self, keyword: str, limit: int) -> list[AdLibraryAd]:
        if not self.apify_token:
            LOGGER.warning(
                "Neither META_AD_LIBRARY_TOKEN nor APIFY_API_TOKEN set — "
                "skipping Meta Ad Library scrape"
            )
            return []

        try:
            from apify_client import ApifyClient
            client = ApifyClient(self.apify_token)
            run_input = {
                "searchTerms": [keyword],
                "activeStatus": "active",
                "maxAds": limit,
            }
            run = client.actor("curious_coder/facebook-ads-scraper").call(run_input=run_input)
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            ads = [self._parse_apify_ad(item) for item in items]
            LOGGER.info("Meta Ad Library (Apify): %d ads for '%s'", len(ads), keyword)
            return ads
        except Exception as exc:
            LOGGER.error("Apify Meta Ads fallback failed for '%s': %s", keyword, exc)
            return []

    def _parse_apify_ad(self, item: dict) -> AdLibraryAd:
        start_date = item.get("startDate", "") or item.get("startedRunningAt", "")
        days_running = int(item.get("daysRunning", 0) or 0)
        if not days_running and start_date:
            try:
                started = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                days_running = (datetime.now(tz=started.tzinfo) - started).days
            except Exception as e:
                import os, logging
                if os.environ.get("AGENCY_DEBUG") == "1":
                    logging.getLogger(__name__).error(e, exc_info=True)

        return AdLibraryAd(
            ad_id=str(item.get("id", "") or item.get("adId", "")),
            page_name=item.get("pageName", "") or item.get("advertiser", ""),
            started_running=start_date,
            days_running=days_running,
            ad_copy=(item.get("body", "") or item.get("adCopy", ""))[:500],
            cta=item.get("callToAction", "") or item.get("cta", ""),
            hook=(item.get("headline", "") or item.get("title", "") or "")[:200],
            url=item.get("url", "") or item.get("adUrl", ""),
        )

    # ------------------------------------------------------------------
    # Report synthesis
    # ------------------------------------------------------------------

    def _build_report(
        self,
        keywords: list[str],
        ads: list[AdLibraryAd],
        min_days: int,
    ) -> AdLibraryReport:
        # Keep only ads confirmed running >= min_days (days_running=0 means unknown, include anyway)
        long_running = [a for a in ads if a.days_running == 0 or a.days_running >= min_days]

        hooks = [a.hook for a in long_running if a.hook]
        ctas = [a.cta for a in long_running if a.cta]

        cta_counts = Counter(ctas)
        top_ctas = [cta for cta, _ in cta_counts.most_common(5)]

        # Winning angles: deduplicated hooks, sorted by days_running desc
        sorted_ads = sorted(long_running, key=lambda a: a.days_running, reverse=True)
        winning_angles: list[str] = []
        seen: set[str] = set()
        for ad in sorted_ads:
            if ad.hook and ad.hook not in seen:
                winning_angles.append(ad.hook)
                seen.add(ad.hook)
            if len(winning_angles) >= 8:
                break

        return AdLibraryReport(
            scraped_at=datetime.utcnow().isoformat(),
            keywords_searched=keywords,
            ads=long_running,
            top_hooks=hooks[:10],
            top_ctas=top_ctas,
            winning_angles=winning_angles,
        )
