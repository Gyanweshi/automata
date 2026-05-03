import sys
from types import ModuleType, SimpleNamespace

import pytest

from agency_common.autonomous_cli import get_persona_prompt, load_client, main


def test_get_persona_prompt_includes_core_directive():
    prompt = get_persona_prompt("research")

    assert "Senior Research Analyst" in prompt
    assert "search_second_brain" in prompt
    assert "CORE DIRECTIVE" in prompt


def test_load_client_instantiates_module_class(monkeypatch):
    module = ModuleType("fake_api_client")

    class FakeClient:
        pass

    module.BaseLLMClient = FakeClient
    monkeypatch.setitem(sys.modules, "fake_api_client", module)

    assert isinstance(load_client("fake_api_client:BaseLLMClient"), FakeClient)


def test_load_client_rejects_invalid_path():
    with pytest.raises(ValueError, match="module:Class"):
        load_client("missing-format")


def test_main_runs_autonomous_agent(monkeypatch, capsys):
    module = ModuleType("fake_api_client_cli")

    class FakeClient:
        def chat_completion(self, *, messages, tools):
            return SimpleNamespace(message={"role": "assistant", "content": "Final answer"}, tool_calls=[])

    module.BaseLLMClient = FakeClient
    monkeypatch.setitem(sys.modules, "fake_api_client_cli", module)
    monkeypatch.setattr("agency_common.harness_runner.log_agent_session", lambda **kwargs: None)

    exit_code = main(
        [
            "--agent",
            "research",
            "--task",
            "Analyze the architecture",
            "--client-path",
            "fake_api_client_cli:BaseLLMClient",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Booting Research Agent Engine" in output
    assert "Final answer" in output


def test_main_returns_error_for_missing_client(capsys):
    exit_code = main(
        [
            "--agent",
            "research",
            "--task",
            "Analyze the architecture",
            "--client-path",
            "missing_client_module:BaseLLMClient",
        ]
    )

    assert exit_code == 1
