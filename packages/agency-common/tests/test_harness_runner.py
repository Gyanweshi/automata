from types import SimpleNamespace

import pytest

from agency_common.harness_runner import HarnessRunner, HarnessRunnerError


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def chat_completion(self, *, messages, tools):
        self.calls.append({"messages": list(messages), "tools": tools})
        return self.responses.pop(0)


def test_harness_runner_executes_tool_and_returns_final_answer(monkeypatch):
    first_response = SimpleNamespace(
        message={"role": "assistant", "content": "", "tool_calls": []},
        tool_calls=[
            SimpleNamespace(
                id="call_1",
                name="search_second_brain",
                arguments='{"search_query": "error handling", "num_results": 2}',
            )
        ],
    )
    second_response = SimpleNamespace(
        message={"role": "assistant", "content": "Use VaultPathError again."},
        tool_calls=[],
    )
    client = FakeClient([first_response, second_response])
    logged = []
    monkeypatch.setattr("agency_common.harness_runner.log_agent_session_with_related_notes", lambda **kwargs: logged.append(kwargs))

    runner = HarnessRunner(
        agent_name="Core_Architect",
        system_prompt="Use memory first.",
        llm_client=client,
        available_tools={
            "search_second_brain": lambda search_query, num_results=3: f"context:{search_query}:{num_results}",
        },
        commit_vault=True,
        commit_reason="test finalization",
    )

    answer = runner.run_task("Use the same error handling structure")

    assert answer == "Use VaultPathError again."
    assert runner.messages[-2] == {
        "role": "tool",
        "tool_call_id": "call_1",
        "name": "search_second_brain",
        "content": "context:error handling:2",
    }
    assert logged[0]["agent_name"] == "Core_Architect"
    assert logged[0]["task_summary"] == "Use the same error handling structure"
    assert "Core_Architect ran `search_second_brain`" in logged[0]["transcript"]
    assert logged[0]["commit_vault"] is True


def test_harness_runner_does_not_log_without_explicit_finalization(monkeypatch):
    client = FakeClient([
        SimpleNamespace(message={"role": "assistant", "content": "Done"}, tool_calls=[]),
    ])
    logged = []
    monkeypatch.setattr(
        "agency_common.harness_runner.log_agent_session_with_related_notes",
        lambda **kwargs: logged.append(kwargs),
    )

    runner = HarnessRunner(agent_name="Agent", system_prompt="System", llm_client=client)

    assert runner.run_task("Task") == "Done"
    assert logged == []


def test_harness_runner_supports_openai_style_function_tool_calls(monkeypatch):
    response = SimpleNamespace(
        message=SimpleNamespace(
            role="assistant",
            content="",
            tool_calls=[
                SimpleNamespace(
                    id="call_1",
                    function=SimpleNamespace(
                        name="search_second_brain",
                        arguments='{"search_query": "architecture"}',
                    ),
                )
            ],
        )
    )
    final_response = SimpleNamespace(message=SimpleNamespace(role="assistant", content="Done"), tool_calls=[])
    client = FakeClient([response, final_response])
    monkeypatch.setattr("agency_common.harness_runner.log_agent_session_with_related_notes", lambda **kwargs: None)

    runner = HarnessRunner(
        agent_name="Agent",
        system_prompt="System",
        llm_client=client,
        available_tools={"search_second_brain": lambda search_query, num_results=3: "context"},
    )

    assert runner.run_task("Task") == "Done"


def test_harness_runner_records_unknown_tool_observation(monkeypatch):
    first_response = SimpleNamespace(
        message={"role": "assistant", "content": ""},
        tool_calls=[SimpleNamespace(id="call_1", name="missing_tool", arguments="{}")],
    )
    final_response = SimpleNamespace(message={"role": "assistant", "content": "Recovered"}, tool_calls=[])
    client = FakeClient([first_response, final_response])
    monkeypatch.setattr("agency_common.harness_runner.log_agent_session_with_related_notes", lambda **kwargs: None)

    runner = HarnessRunner(agent_name="Agent", system_prompt="System", llm_client=client)

    assert runner.run_task("Task") == "Recovered"
    assert runner.messages[-2]["content"] == "Unknown tool requested: missing_tool"


def test_harness_runner_raises_on_invalid_tool_arguments():
    response = SimpleNamespace(
        message={"role": "assistant", "content": ""},
        tool_calls=[SimpleNamespace(id="call_1", name="search_second_brain", arguments="{not-json}")],
    )
    client = FakeClient([response])
    runner = HarnessRunner(
        agent_name="Agent",
        system_prompt="System",
        llm_client=client,
        available_tools={"search_second_brain": lambda **kwargs: "context"},
    )

    with pytest.raises(HarnessRunnerError, match="Invalid JSON"):
        runner.run_task("Task")


def test_harness_runner_iteration_failsafe(monkeypatch):
    looping_response = SimpleNamespace(
        message={"role": "assistant", "content": ""},
        tool_calls=[SimpleNamespace(id="call_1", name="search_second_brain", arguments="{}")],
    )
    client = FakeClient([looping_response, looping_response])
    monkeypatch.setattr("agency_common.harness_runner.log_agent_session_with_related_notes", lambda **kwargs: None)
    runner = HarnessRunner(
        agent_name="Agent",
        system_prompt="System",
        llm_client=client,
        available_tools={"search_second_brain": lambda **kwargs: "context"},
        max_iterations=1,
    )

    with pytest.raises(HarnessRunnerError, match="exceeded"):
        runner.run_task("Task")


def test_harness_runner_rejects_invalid_iteration_limit():
    with pytest.raises(ValueError, match="max_iterations"):
        HarnessRunner(agent_name="Agent", system_prompt="System", llm_client=object(), max_iterations=0)
