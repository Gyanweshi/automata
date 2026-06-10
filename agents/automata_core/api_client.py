"""Lightweight LLM API client for the agency autonomous harness."""
from __future__ import annotations

import logging
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

load_dotenv()

LOGGER = logging.getLogger(__name__)


class LLMResponseWrapper:
    """
    Wraps an OpenAI chat completion message so it matches the interface
    HarnessRunner expects: .message and .tool_calls.
    """

    def __init__(self, openai_message: ChatCompletionMessage) -> None:
        # Store the raw Pydantic message so it can be appended to message history as-is
        self.message = openai_message
        self.tool_calls = openai_message.tool_calls

    @property
    def content(self) -> str | None:
        return self.message.content


class BaseLLMClient:
    """
    Lightweight, framework-free OpenAI API client.
    Pointable at local models (Ollama, LM Studio) via base_url.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        *,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        client_kwargs: dict[str, Any] = {}
        if base_url:
            client_kwargs["base_url"] = base_url
        if api_key:
            client_kwargs["api_key"] = api_key

        self.client = OpenAI(**client_kwargs)
        self.model = model

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponseWrapper:
        """Send the conversation history and available tools to the LLM."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        LOGGER.info("Sending request to %s with %d messages...", self.model, len(messages))
        response = self.client.chat.completions.create(**kwargs)
        return LLMResponseWrapper(response.choices[0].message)
