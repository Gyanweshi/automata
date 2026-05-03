import pytest
import yaml
from agency_common.models import BrandProfile

def test_brand_profile_parsing():
    yaml_data = """
slug: "test-brand"
name: "Test Brand"
onboarded: "2026-05-03"
platforms:
  instagram:
    handle: "@test"
    content_types: ["reel"]
    posting_frequency: "3x/week"
    hashtag_groups:
      niche: ["#test"]
      broad: []
      branded: []
competitors:
  instagram: []
  linkedin: []
  facebook: []
content_pillars:
  educational: 100
"""
    data = yaml.safe_load(yaml_data)
    brand = BrandProfile.model_validate(data)
    assert brand.slug == "test-brand"
    assert brand.name == "Test Brand"
    assert brand.platforms.instagram is not None
    assert brand.platforms.instagram.handle == "@test"
