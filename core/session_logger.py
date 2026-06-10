"""
Unified Session Logger for all autonomous agents in the monorepo.
"""
import json
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).parent.parent
LOGS_DIR = WORKSPACE_ROOT / "data" / "logs"

def log_agent_session(agent_name: str, session_data: dict):
    """Logs the execution session of any agent in a standard format."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"{agent_name}_{timestamp}.json"
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
        
    return log_file
