"""WorkspaceManager — shared filesystem bus for inter-agent communication."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel


class WorkspaceManager:
    """Manages reading and writing agent outputs to a shared workspace directory.

    Directory layout:
        workspace/{agent}/{brand}/{YYYY-MM-DD_NNN}.json

    Usage:
        wm = WorkspaceManager()
        wm.write("research", "my-brand", research_output)
        data = wm.read_latest("research", "my-brand")
    """

    def __init__(self, workspace_root: str | Path | None = None):
        if workspace_root:
            self.root = Path(workspace_root)
        else:
            env = os.environ.get("AGENCY_WORKSPACE")
            if env:
                self.root = Path(env)
            else:
                # Walk up from CWD
                cwd = Path.cwd()
                for candidate in [cwd / "workspace", cwd.parent / "workspace"]:
                    if candidate.is_dir():
                        self.root = candidate
                        break
                else:
                    self.root = cwd / "workspace"

    def _agent_brand_dir(self, agent: str, brand: str) -> Path:
        path = self.root / agent / brand
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _next_run_id(self, agent: str, brand: str) -> str:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        dir_path = self._agent_brand_dir(agent, brand)
        existing = sorted(dir_path.glob(f"{today}_*.json"))
        seq = len(existing) + 1
        return f"{today}_{seq:03d}"

    def write(self, agent: str, brand: str, data: BaseModel | dict) -> Path:
        """Write output data to workspace. Returns the path written."""
        run_id = self._next_run_id(agent, brand)
        dir_path = self._agent_brand_dir(agent, brand)
        out_path = dir_path / f"{run_id}.json"
        if isinstance(data, BaseModel):
            payload = data.model_dump()
        else:
            payload = data
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2, default=str)
        return out_path

    def read_latest(self, agent: str, brand: str) -> dict[str, Any] | None:
        """Read the most recent run output for an agent+brand pair."""
        dir_path = self._agent_brand_dir(agent, brand)
        files = sorted(dir_path.glob("*.json"))
        if not files:
            return None
        with open(files[-1], "r") as f:
            return json.load(f)

    def read_latest_as(self, agent: str, brand: str, model: Type[BaseModel]) -> BaseModel | None:
        """Read latest output and validate it into a Pydantic model."""
        data = self.read_latest(agent, brand)
        if data is None:
            return None
        return model.model_validate(data)

    def list_runs(self, agent: str, brand: str) -> list[Path]:
        """List all past run files for an agent+brand pair, sorted oldest→newest."""
        dir_path = self._agent_brand_dir(agent, brand)
        return sorted(dir_path.glob("*.json"))

    def has_output(self, agent: str, brand: str) -> bool:
        """Return True if any output exists for this agent+brand."""
        return bool(self.list_runs(agent, brand))
