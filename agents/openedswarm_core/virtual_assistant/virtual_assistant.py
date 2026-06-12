import os

from agency_swarm import Agent, ModelSettings
try:
    from agency_swarm import HostedMCPTool
except ImportError:
    HostedMCPTool = None
from agency_swarm.tools import (
    WebSearchTool,
    PersistentShellTool,
    IPythonInterpreter,
)
from openai.types.shared import Reasoning
from dotenv import load_dotenv

from config import get_default_model, is_openai_provider
from shared_tools import CopyFile, ExecuteTool, FindTools, ManageConnections, SearchTools

load_dotenv()

# Class-level rename — idempotent, safe to run once at import time.
IPythonInterpreter.__name__ = "ProgrammaticToolCalling"


def _get_capsulehub_mcp_tool():
    token = os.getenv("CAPSULEHUB_AUTH_TOKEN")
    if not token or HostedMCPTool is None:
        return None

    return HostedMCPTool(
        tool_config={
            "type": "mcp",
            "server_label": "capsulehub",
            "server_url": "https://backend.tilantra.com/mcp",
            "require_approval": "never",
            "headers": {
                "Authorization": f"Bearer {token}",
            },
        }
    )


def create_virtual_assistant() -> Agent:
    capsulehub_mcp = _get_capsulehub_mcp_tool()
    tools = [
        WebSearchTool(),
        PersistentShellTool,
        IPythonInterpreter,
        CopyFile,
        ExecuteTool,
        FindTools,
        ManageConnections,
        SearchTools,
    ]
    if capsulehub_mcp:
        tools.append(capsulehub_mcp)

    return Agent(
        name="General Agent",
        description="Your virtual assistant that connects to 10000+ external systems.",
        instructions="./instructions.md",
        files_folder="./files",
        tools_folder="./tools",
        model=get_default_model(),
        model_settings=ModelSettings(
            reasoning=Reasoning(effort="medium", summary="auto") if is_openai_provider() else None,
            response_include=["web_search_call.action.sources"] if is_openai_provider() else None,
        ),
        tools=tools,
        conversation_starters=[
            "Send a summary of my unread emails to Slack.",
            "Schedule a meeting with my team for next Monday.",
            "What external systems do I have connected?",
            "Draft and send a follow-up email to my last meeting attendees.",
        ],
    )


if __name__ == "__main__":
    from agency_swarm import Agency
    Agency(create_virtual_assistant()).terminal_demo()
