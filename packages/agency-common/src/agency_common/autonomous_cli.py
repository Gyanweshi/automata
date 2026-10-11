"""CLI entry point for the autonomous harness runner."""
from __future__ import annotations

import argparse
import importlib
import logging
import sys
from typing import Any

from .harness_runner import HarnessRunner

LOGGER = logging.getLogger(__name__)
DEFAULT_CLIENT_PATH = "api_client:BaseLLMClient"

PERSONA_PROMPTS = {
    "research": "You are a Senior Research Analyst. Break down complex topics with rigor and cite useful context.",
    "storyboard": "You are an Expert Visual Storyteller. Design scene-by-scene plans with clear visual intent.",
    "content": "You are a Master Copywriter. Craft compelling narratives matched to the brand voice.",
}

CORE_DIRECTIVE = (
    "\n\nCORE DIRECTIVE: Before planning or executing each new request, call "
    "discover_workflows to check matching skills and existing specialist agents. "
    "Use read_workflow to read AGENTS.md, the relevant SKILL.md and required references. "
    "Follow the smallest applicable workflow without waiting for the user to name it. "
    "Reuse unchanged instructions for follow-ups. Preserve project decisions, references, "
    "constraints, approval scope and budget through retries and handoffs. Name the chosen "
    "workflow briefly on first use. Agent files do not imply callable delegation; disclose "
    "missing capabilities and do not claim execution or verification that did not occur. "
    "Use search_second_brain for broad non-brand context only. Brand-specific context "
    "comes from the brand note, not vector search; if this runtime cannot read that note, "
    "surface the gap before dependent work."
)


def get_persona_prompt(agent_type: str) -> str:
    """Return the system prompt for a supported agent persona."""
    return PERSONA_PROMPTS.get(agent_type, "You are a helpful AI assistant.") + CORE_DIRECTIVE


def load_client(client_path: str = DEFAULT_CLIENT_PATH, **kwargs: Any) -> Any:
    """Load and instantiate an LLM client from a module path in module:Class format."""
    if ":" not in client_path:
        raise ValueError("client path must use module:Class format")

    module_name, class_name = client_path.split(":", 1)
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise RuntimeError(
            f"Could not import LLM client module '{module_name}'. "
            f"Create it or pass --client-path module:Class."
        ) from exc

    try:
        client_class = getattr(module, class_name)
    except AttributeError as exc:
        raise RuntimeError(f"Module '{module_name}' does not define '{class_name}'.") from exc

    return client_class(**kwargs)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an autonomous agency agent.")
    parser.add_argument("--agent", choices=["research", "storyboard", "content"], required=True)
    parser.add_argument("--task", required=True, help="The task to execute.")
    parser.add_argument(
        "--client-path",
        default=DEFAULT_CLIENT_PATH,
        help="LLM client class path in module:Class format. Defaults to api_client:BaseLLMClient.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name to pass to the LLM client (e.g. gpt-4o, gpt-4o-mini).",
    )
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument(
        "--commit-vault",
        action="store_true",
        help="Finalize the session and canonical Memory state in the vault.",
    )
    parser.add_argument(
        "--commit-reason",
        help="Required reason/approval reference when --commit-vault is used.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.commit_vault and not (args.commit_reason or "").strip():
        parser.error("--commit-reason is required with --commit-vault")

    client_kwargs: dict[str, Any] = {}
    if args.model:
        client_kwargs["model"] = args.model

    try:
        llm_client = load_client(args.client_path, **client_kwargs)
        runner = HarnessRunner(
            agent_name=f"{args.agent.capitalize()}Agent",
            system_prompt=get_persona_prompt(args.agent),
            llm_client=llm_client,
            max_iterations=args.max_iterations,
            commit_vault=args.commit_vault,
            commit_reason=args.commit_reason,
        )
        print(f"Booting {args.agent.capitalize()} Agent Engine...")
        final_result = runner.run_task(args.task)
    except KeyboardInterrupt:
        print("\nExecution aborted by user.")
        return 1
    except Exception:
        LOGGER.error("Agent failed", exc_info=True)
        return 1

    print("\n=== FINAL OUTPUT ===\n")
    print(final_result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
