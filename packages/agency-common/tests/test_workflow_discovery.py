import importlib.util
import json
import builtins
import sys
from pathlib import Path
from types import ModuleType

from pydantic import BaseModel

from agency_common import workflow_discovery as workflows


def make_skill(root, name="example"):
    path = root / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(f"---\nname: {name}\ndescription: >\n  First line\n  second line\n---\n\nUse this workflow.\n")
    return path


def test_catalog_prefers_canonical_and_parses_multiline_metadata(tmp_path):
    source = make_skill(tmp_path)
    shim = tmp_path / ".agents/skills/example/SKILL.md"
    shim.parent.mkdir(parents=True)
    shim.write_text(source.read_text())
    agent = tmp_path / "agents/openedswarm_core/docs_agent/instructions.md"
    agent.parent.mkdir(parents=True)
    agent.write_text("Document specialist")
    catalog = workflows.workflow_catalog(tmp_path)
    assert len(catalog["skills"]) == 1
    assert catalog["skills"][0]["path"] == str(source)
    assert catalog["skills"][0]["description"].strip() == "First line second line"
    assert catalog["agents"][0]["instructions"] == str(agent)


def test_read_reference_but_reject_secret_traversal_and_symlink_escape(tmp_path, monkeypatch):
    source = make_skill(tmp_path)
    secret = tmp_path / ".env"
    secret.write_text("SECRET")
    escape = source.parent / "escape.md"
    escape.symlink_to(secret)
    monkeypatch.setattr(workflows, "repo_root", lambda: tmp_path)
    assert "Use this workflow" in workflows.read_workflow(str(source))
    assert "denied" in workflows.read_workflow("skills/example/../../.env")
    assert "denied" in workflows.read_workflow(str(escape))


def test_registration_is_idempotent_detects_drift_and_preserves_conflicts(tmp_path):
    script = workflows.repo_root() / "scripts/sync-skills.py"
    spec = importlib.util.spec_from_file_location("sync_skills", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = make_skill(tmp_path)
    assert len(module.sync(tmp_path)) == 2
    assert module.sync(tmp_path, write=True) == []
    assert module.sync(tmp_path, write=True) == []
    target = tmp_path / ".agents/skills/example/SKILL.md"
    target.write_text("---\nname: custom\ndescription: Keep me\n---\nUser-owned skill")
    original = target.read_bytes()
    assert module.sync(tmp_path, write=True)
    assert target.read_bytes() == original
    source.write_text(source.read_text().replace("First line", "Changed"))
    assert any("Metadata differs" in item for item in module.sync(tmp_path))


def test_autonomous_harness_can_discover_then_read_real_skill():
    from agency_common.harness_runner import HarnessRunner, NormalizedToolCall
    runner = HarnessRunner("Example", "System", object())
    advertised = {schema["function"]["name"] for schema in runner.tool_schemas}
    assert {"discover_workflows", "read_workflow"} <= advertised
    result = runner._execute_tool_call(NormalizedToolCall("1", "discover_workflows", "{}"))
    catalog = json.loads(result)
    skill = next(s for s in catalog["skills"] if s["name"] == "visual-video")
    result = runner._execute_tool_call(NormalizedToolCall("2", "read_workflow", json.dumps({"path": skill["path"]})))
    assert result == Path(skill["path"]).read_text()


def test_custom_harness_tools_do_not_advertise_unavailable_discovery():
    from agency_common.harness_runner import HarnessRunner
    runner = HarnessRunner("Example", "System", object(), available_tools={})
    assert runner.available_tools == {}
    assert runner.tool_schemas == []


def test_swarm_adapters_read_skills_and_handle_standalone_missing_package(monkeypatch):
    # Exercise the adapter with a Pydantic tool base; no live agency/model needed.
    tool_module = ModuleType("agency_swarm.tools")
    tool_module.BaseTool = BaseModel
    monkeypatch.setitem(sys.modules, "agency_swarm.tools", tool_module)
    path = workflows.repo_root() / "agents/openedswarm_core/shared_tools/WorkflowDiscovery.py"
    spec = importlib.util.spec_from_file_location("workflow_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    catalog = json.loads(module.DiscoverWorkflows().run())
    assert module.ReadWorkflow(path=catalog["skills"][0]["path"]).run().startswith("---")
    original_import = builtins.__import__

    def missing_common(name, *args, **kwargs):
        if name == "agency_common":
            raise ModuleNotFoundError("Missing agency-common", name="agency_common")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_common)
    assert "not installed" in module.DiscoverWorkflows().run()
