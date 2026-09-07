"""Check selection semantics and source integrity, without network or vault writes."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
import tempfile

from select_tools import FRAMEWORK_BANK_PATH, HISTORICAL_BANK_PATH, load_bank, near_twin_warning, select_tools


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.bank = load_bank()

    def test_filter_and_exclude(self):
        selected = select_tools(self.bank, tags=["PROOF"], exclude=["es-21"])
        self.assertEqual([t["id"] for t in selected], ["es-15"])

    def test_unknown_tags_do_not_fabricate_matches(self):
        self.assertEqual(select_tools(self.bank, tags=["no-such-tag"]), [])

    def test_ids_and_tags_intersect(self):
        self.assertEqual(select_tools(self.bank, tags=["trust"], ids=["es-08"]), [])
        self.assertEqual(select_tools(self.bank, ids=["es-08"])[0]["id"], "es-08")

    def test_bad_identifiers_and_limits_fail(self):
        for options in ({"ids": ["bogus"]}, {"exclude": ["bogus"]}, {"limit": 0}):
            with self.assertRaises(ValueError):
                select_tools(self.bank, **options)

    def test_selection_does_not_mutate_bank(self):
        before = copy.deepcopy(self.bank)
        self.assertEqual(len(select_tools(self.bank, limit=2)), 2)
        self.assertEqual(self.bank, before)

    def test_agency_bank_is_source_independent(self):
        self.assertEqual(self.bank["bank_kind"], "agency_mechanisms")
        self.assertEqual(len(self.bank["tools"]), 23)
        self.assertEqual(len(self.bank["tag_vocabulary"]), len(set(self.bank["tag_vocabulary"])))
        self.assertEqual(len(self.bank["family_vocabulary"]), 6)
        for tool in self.bank["tools"]:
            self.assertTrue(set(tool["tags"]) <= set(self.bank["tag_vocabulary"]))
            self.assertIn(tool["family"], self.bank["family_vocabulary"])
        self.assertEqual(len(select_tools(self.bank, altitude="platform", limit=20)), 10)
        self.assertTrue(all(t["id"] not in {"es-08", "es-09"} for t in select_tools(self.bank, altitude="platform")))

    def test_validator_rejects_unknown_tag_and_family(self):
        for field, value in (("tags", ["totally-made-up-tag"]), ("family", "totally-made-up-family")):
            broken = copy.deepcopy(self.bank)
            if field == "tags":
                broken["tools"][0][field] = value
            else:
                broken["tools"][0][field] = value
            with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
                json.dump(broken, handle)
                path = Path(handle.name)
            try:
                with self.assertRaises(ValueError):
                    load_bank(path)
            finally:
                path.unlink()

    def test_historical_ids_keep_their_original_meaning(self):
        historical = load_bank(HISTORICAL_BANK_PATH)
        self.assertEqual(len(historical["tools"]), 15)
        self.assertFalse(historical["current_primary_access"]["tool_bodies_read"])
        self.assertEqual(select_tools(historical, ids=["dob-03"])[0]["historical_number"], 3)
        with self.assertRaises(ValueError):
            select_tools(self.bank, ids=["dob-03"])

    def test_current_historical_references_resolve(self):
        historical_ids = {tool["id"] for tool in load_bank(HISTORICAL_BANK_PATH)["tools"]}
        for tool in self.bank["tools"]:
            self.assertTrue(set(tool.get("related_historical_ids", [])) <= historical_ids)

    def test_list_projection_keeps_attribution_key(self):
        self.assertTrue(all("source_id" not in tool for tool in self.bank["tools"]))

    def test_documented_tag_command_and_list_attribution(self):
        script = str(__import__("pathlib").Path(__file__).with_name("select_tools.py"))
        tagged = json.loads(subprocess.check_output([sys.executable, script, "--tag", "community", "--limit", "5"], text=True))
        self.assertEqual(len(tagged["tools"]), 5)
        listed = json.loads(subprocess.check_output([sys.executable, script, "--list"], text=True))
        self.assertEqual(listed["sources"], {})
        self.assertTrue(listed["attribution"])

    def test_near_twin_pairing_requires_explicit_opt_in(self):
        with self.assertRaises(ValueError):
            select_tools(self.bank, ids=["es-08", "es-09"])
        self.assertEqual(len(select_tools(self.bank, ids=["es-08", "es-09"], allow_near_twins=True)), 2)
        broad = select_tools(self.bank, altitude="execution", limit=30)
        warning = near_twin_warning(self.bank, broad)
        self.assertEqual(warning[0]["ids"], ["es-08", "es-09"])

    def test_resources_integrity_and_local_mappings(self):
        resources_path = Path(__file__).resolve().parents[1] / "references" / "resources.json"
        resources = json.loads(resources_path.read_text(encoding="utf-8"))
        framework_ids = {tool["id"] for tool in load_bank(FRAMEWORK_BANK_PATH)["tools"]}
        self.assertIsInstance(resources.get("resources"), list)
        for resource in resources["resources"]:
            self.assertTrue(resource.get("name") and resource.get("url"))
            for local_id in resource.get("local_ids", []):
                self.assertIn(local_id, framework_ids)

    def test_evidence_readiness_has_one_canonical_contract(self):
        reference = Path(__file__).resolve().parents[2] / "agency-research" / "references" / "evidence-readiness.md"
        text = reference.read_text(encoding="utf-8")
        self.assertEqual(text.count('"evidence_readiness"'), 1)
        for status in ("blocked", "provisional", "ready"):
            self.assertIn(status, text)

    def test_framework_bank_routes_by_stage_and_validates_outputs(self):
        frameworks = load_bank(FRAMEWORK_BANK_PATH)
        self.assertEqual(len(frameworks["tools"]), 9)
        insight = select_tools(frameworks, stage="insight")
        self.assertEqual({tool["id"] for tool in insight}, {"ideo-themes", "bos-noncustomers"})
        self.assertTrue(all(tool["application"]["outputs"] for tool in frameworks["tools"]))
        self.assertEqual({tool["id"] for tool in select_tools(frameworks, stage="memory")}, {"ehb-distinctiveness"})
        with self.assertRaises(ValueError):
            select_tools(self.bank, stage="insight")


if __name__ == "__main__":
    unittest.main()
