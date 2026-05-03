import pytest
from unittest.mock import MagicMock
from agency_research.scrapers.instagram import InstagramScraper
from agency_common.models import CompetitorAnalysis

def test_instagram_scrape_profile_success(mocker):
    # Mock instaloader classes
    mocker.patch("instaloader.Instaloader")
    mock_profile = mocker.patch("instaloader.Profile.from_username")
    
    mock_profile.return_value.followers = 1000
    mock_profile.return_value.followees = 500
    mock_profile.return_value.mediacount = 100
    mock_profile.return_value.biography = "Test Bio"
    
    scraper = InstagramScraper(dry_run=False)
    scraper._get_loader = MagicMock()
    
    result = scraper.scrape_profile("test_handle")
    assert result.handle == "test_handle"
    assert result.follower_count == 1000
    assert result.bio == "Test Bio"

def test_instagram_scrape_profile_retries_and_fails(mocker):
    scraper = InstagramScraper(dry_run=False)
    scraper._get_loader = MagicMock()
    
    # Force an exception to trigger retries
    mock_profile = mocker.patch("instaloader.Profile.from_username", side_effect=Exception("API Blocked"))
    
    # Mock tenacity sleep to make tests fast
    mocker.patch("tenacity.nap.time.sleep")
    
    result = scraper.scrape_profile("test_handle")
    
    # Should retry 3 times (initial + 2 retries) because of stop_after_attempt(3)
    assert mock_profile.call_count == 3
    assert result.bio == "Error: API Blocked"
    assert result.handle == "test_handle"
