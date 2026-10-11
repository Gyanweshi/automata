"""Read-only workflow tools shared by every swarm specialist and the orchestrator."""
from agency_swarm.tools import BaseTool
from pydantic import Field

def _workflow_call(name, **kwargs):
    # Standalone OpenSwarm installations may not include the monorepo packages.
    # Keep factories loadable and report the missing capability when invoked.
    try:
        from agency_common import workflow_discovery
    except ModuleNotFoundError as exc:
        if exc.name not in {"agency_common", "agency_common.workflow_discovery"}:
            raise
        return ("Workflow discovery unavailable: agency-common is not installed. "
                "Use the Automata repo environment (make install), or inspect local "
                "skills and specialist instructions with available file tools. "
                "Do not assume no matching workflow exists.")
    return getattr(workflow_discovery, name)(**kwargs)


class DiscoverWorkflows(BaseTool):
    """Find existing skills, specialist instruction files and routing policy before task execution."""

    def run(self):
        return _workflow_call("discover_workflows")


class ReadWorkflow(BaseTool):
    """Read a discovered skill, specialist instruction or required text reference."""

    path: str = Field(..., description="Absolute or repo-relative instruction/reference path.")

    def run(self):
        return _workflow_call("read_workflow", path=self.path)
