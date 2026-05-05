"""Framework-free autonomous harness runner."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable

from .obsidian_vector_index import search_second_brain
from .obsidian_writer import log_agent_session_with_related_notes

LOGGER = logging.getLogger(__name__)

ToolFunction = Callable[..., str]


@dataclass(frozen=True)
class NormalizedToolCall:
    """Model-agnostic representation of an LLM tool call."""

    id: str
    name: str
    arguments: str


class HarnessRunnerError(RuntimeError):
    """Raised when the harness cannot complete a task."""


class HarnessRunner:
    """Central model-call -> tool-call -> observation loop for local agents."""

    def __init__(
        self,
        agent_name: str,
        system_prompt: str,
        llm_client: Any,
        *,
        available_tools: dict[str, ToolFunction] | None = None,
        max_iterations: int = 5,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")

        self.agent_name = agent_name
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        self.available_tools: dict[str, ToolFunction] = available_tools or {
            "search_second_brain": search_second_brain,
        }
        self.tool_schemas = [
            {
                "type": "function",
                "function": {
                    "name": "search_second_brain",
                    "description": (
                        "Searches the user's Obsidian Second Brain for past notes, "
                        "blueprints, and concepts related to a specific query."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_query": {
                                "type": "string",
                                "description": "The concept, project name, or idea to search for.",
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "The number of related notes to retrieve.",
                                "default": 3,
                            },
                        },
                        "required": ["search_query"],
                    },
                },
            }
        ]

    def run_task(self, user_task: str) -> str:
        """Execute the autonomous loop for a single user task."""
        LOGGER.info("[%s] Starting task: %s", self.agent_name, user_task)
        self.messages.append({"role": "user", "content": user_task})

        for _ in range(self.max_iterations):
            response = self.llm_client.chat_completion(
                messages=self.messages,
                tools=self.tool_schemas,
            )
            assistant_message = self._message_from_response(response)
            self.messages.append(assistant_message)

            tool_calls = self._tool_calls_from_response(response)
            if not tool_calls:
                LOGGER.info("[%s] Task complete.", self.agent_name)
                break

            for tool_call in tool_calls:
                observation = self._execute_tool_call(tool_call)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.name,
                        "content": observation,
                    }
                )
        else:
            log_agent_session_with_related_notes(
                agent_name=self.agent_name,
                task_summary=user_task,
                transcript=self.format_transcript(),
                tags=[self.agent_name.lower(), "autonomous-run", "max-iterations-exceeded"],
            )
            raise HarnessRunnerError(f"{self.agent_name} exceeded {self.max_iterations} loop iterations")

        final_answer = self._last_assistant_content()
        log_agent_session_with_related_notes(
            agent_name=self.agent_name,
            task_summary=user_task,
            transcript=self.format_transcript(),
            tags=[self.agent_name.lower(), "autonomous-run"],
        )
        return final_answer

    def _execute_tool_call(self, tool_call: NormalizedToolCall) -> str:
        tool = self.available_tools.get(tool_call.name)
        if tool is None:
            LOGGER.error("Agent requested unknown tool: %s", tool_call.name)
            return f"Unknown tool requested: {tool_call.name}"

        try:
            args = json.loads(tool_call.arguments or "{}")
        except json.JSONDecodeError as exc:
            raise HarnessRunnerError(f"Invalid JSON arguments for tool {tool_call.name}") from exc

        LOGGER.info("[%s] Executing tool: %s with args: %s", self.agent_name, tool_call.name, args)
        return str(tool(**args))

    def format_transcript(self) -> str:
        """Convert message history into Markdown suitable for session logs."""
        transcript: list[str] = []
        for message in self.messages:
            role = str(message.get("role") or "")
            content = str(message.get("content") or "")

            if role == "user":
                transcript.append(f"**User:** {content}")
            elif role == "assistant" and content:
                transcript.append(f"**{self.agent_name}:** {content}")
            elif role == "tool":
                snippet = content[:200] + "..." if len(content) > 200 else content
                tool_name = message.get("name", "tool")
                transcript.append(f"> *{self.agent_name} ran `{tool_name}`.*\n>\n> {snippet}")

        return "\n\n".join(transcript)

    def _last_assistant_content(self) -> str:
        for message in reversed(self.messages):
            if message.get("role") == "assistant":
                return str(message.get("content") or "")
        return ""

    @staticmethod
    def _message_from_response(response: Any) -> dict[str, Any]:
        message = _get_value(response, "message")
        if message is None:
            message = response
        if isinstance(message, dict):
            return dict(message)

        return {
            "role": _get_value(message, "role") or "assistant",
            "content": _get_value(message, "content") or "",
            "tool_calls": _get_value(message, "tool_calls") or [],
        }

    @staticmethod
    def _tool_calls_from_response(response: Any) -> list[NormalizedToolCall]:
        raw_tool_calls = _get_value(response, "tool_calls")
        if raw_tool_calls is None:
            message = _get_value(response, "message")
            raw_tool_calls = _get_value(message, "tool_calls") if message is not None else None

        normalized: list[NormalizedToolCall] = []
        for index, raw_tool_call in enumerate(raw_tool_calls or []):
            function = _get_value(raw_tool_call, "function")
            name = _get_value(raw_tool_call, "name") or _get_value(function, "name")
            arguments = _get_value(raw_tool_call, "arguments") or _get_value(function, "arguments") or "{}"
            tool_call_id = _get_value(raw_tool_call, "id") or f"tool_call_{index}"
            if name:
                normalized.append(NormalizedToolCall(id=str(tool_call_id), name=str(name), arguments=str(arguments)))

        return normalized


def _get_value(item: Any, key: str) -> Any:
    if item is None:
        return None
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)
