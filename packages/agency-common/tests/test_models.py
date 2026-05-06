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


def test_brand_profile_memory_defaults_empty():
    brand = BrandProfile.model_validate({"slug": "x", "name": "X"})
    assert brand.memory == []


def test_brand_profile_memory_accepts_list():
    brand = BrandProfile.model_validate({
        "slug": "x",
        "name": "X",
        "memory": ["2026-05-06: carousel brief for topic A.", "2026-05-06: research — @cashify leads."],
    })
    assert len(brand.memory) == 2
    assert "carousel" in brand.memory[0]
