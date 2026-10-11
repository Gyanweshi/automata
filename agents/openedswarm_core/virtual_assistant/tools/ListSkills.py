from agency_swarm.tools import BaseTool
from shared_tools.WorkflowDiscovery import DiscoverWorkflows


class ListSkills(BaseTool):
    """List repo skills and specialist workflows (legacy alias for DiscoverWorkflows)."""

    def run(self):
        return DiscoverWorkflows().run()
