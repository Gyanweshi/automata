"""
Unified Autonomous Runner.
Wraps the execution of both OpenedSwarm and Automata agents, enforcing centralized logging.
"""
import sys
import argparse
from pathlib import Path

# Add the workspace root to sys.path so we can import agents/ and core/
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from core.session_logger import log_agent_session

def run_automata(brand: str, action: str):
    print(f"Running Automata agent for brand {brand} with action {action}...")
    # Import automata specific logic
    try:
        from agents.automata_core import run
        # Wrap the automata run logic here, for now just simulating
        session_data = {"agent": "automata", "brand": brand, "action": action, "status": "success"}
        log_agent_session("automata", session_data)
        print("Automata run completed and logged.")
    except ImportError as e:
        print(f"Failed to load Automata core: {e}")

def run_openedswarm():
    print("Running OpenedSwarm...")
    try:
        from agents.openedswarm_core.swarm import create_agency
        agency = create_agency()
        # In a real run, we would attach a logging callback to the agency
        session_data = {"agent": "openedswarm", "status": "initialized"}
        log_agent_session("openedswarm", session_data)
        print("OpenedSwarm initialized and logged.")
    except ImportError as e:
        print(f"Failed to load OpenedSwarm core: {e}")

def main():
    parser = argparse.ArgumentParser(description="Unified Agent Runner")
    parser.add_argument("--agent", choices=["automata", "openedswarm"], required=True)
    parser.add_argument("--brand", help="Brand name (Automata only)")
    parser.add_argument("--action", help="Action (Automata only)")
    
    args = parser.parse_args()
    
    if args.agent == "automata":
        if not args.brand or not args.action:
            print("Error: --brand and --action are required for automata")
            sys.exit(1)
        run_automata(args.brand, args.action)
    elif args.agent == "openedswarm":
        run_openedswarm()

if __name__ == "__main__":
    main()
