"""
Unified Autonomous Runner.
Wraps the execution of both OpenedSwarm and Automata agents,
enforcing centralized logging and memory updates to Brainiac2.
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add the workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from core.session_logger import log_agent_session
from core.memory_writer import update_brand, update_status, append_recent_session_to_agents_md


def run_automata(brand: str, action: str):
    print(f"\n🤖 Automata — running '{action}' for brand '{brand}'...\n")
    start = datetime.now()

    try:
        from agents.automata_core import run
        result = run.main(brand=brand, action=action)
        status = "success"
        actions = [f"Ran '{action}' pipeline for {brand}"]
        outputs = result.get("outputs", []) if isinstance(result, dict) else []
        next_steps = result.get("next_steps", []) if isinstance(result, dict) else []
    except ImportError as e:
        print(f"⚠️  Failed to load Automata core: {e}")
        status = "import_error"
        actions = [f"Attempted '{action}' for {brand} — import failed: {e}"]
        outputs = []
        next_steps = ["Fix import error in agents/automata_core"]
    except Exception as e:
        print(f"⚠️  Automata run failed: {e}")
        status = "error"
        actions = [f"Attempted '{action}' for {brand} — error: {e}"]
        outputs = []
        next_steps = [f"Debug error: {e}"]

    duration = (datetime.now() - start).seconds

    # Write rich Markdown session log to Brainiac2
    log_path = log_agent_session(
        agent_name="automata",
        session_data={"agent": "automata", "brand": brand, "action": action, "status": status},
        brand=brand,
        actions=actions,
        outputs=outputs,
        decisions=[],
        current_state=f"'{action}' pipeline {'completed' if status == 'success' else 'failed'} in {duration}s",
        next_steps=next_steps,
    )

    # Update curated memory layer
    update_brand(
        brand_name=brand,
        status="🟢 Active" if status == "success" else "🔴 Error",
        done=actions,
        assets=outputs,
        next_steps=next_steps,
    )
    append_recent_session_to_agents_md(
        agent_name="Automata",
        brand_or_project=brand,
        one_liner=f"Ran '{action}' — {status}",
    )

    print(f"\n✅ Session logged → {log_path}")
    print(f"📚 Memory updated → C:\\Brainiac2\\memory\\")


def run_openedswarm():
    print("\n🐝 OpenedSwarm — initializing agent swarm...\n")

    try:
        from agents.openedswarm_core.swarm import create_agency
        agency = create_agency()
        status = "initialized"
        actions = ["OpenedSwarm agency initialized successfully"]
    except ImportError as e:
        print(f"⚠️  Failed to load OpenedSwarm: {e}")
        status = "import_error"
        actions = [f"OpenedSwarm import failed: {e}"]

    log_path = log_agent_session(
        agent_name="openedswarm",
        session_data={"agent": "openedswarm", "status": status},
        project="automata-swarm",
        actions=actions,
        current_state=f"Swarm {status}",
    )
    append_recent_session_to_agents_md(
        agent_name="OpenedSwarm",
        brand_or_project="automata-swarm",
        one_liner=f"Agency {status}",
    )

    print(f"\n✅ Session logged → {log_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Automata — Unified Agent Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python core/runner.py --agent automata --brand Rasoi --action research
  python core/runner.py --agent openedswarm
        """,
    )
    parser.add_argument(
        "--agent",
        choices=["automata", "openedswarm"],
        required=True,
        help="Which agent to run",
    )
    parser.add_argument("--brand", help="Brand name (automata agent only)")
    parser.add_argument("--action", help="Action to run (automata agent only)")

    args = parser.parse_args()

    if args.agent == "automata":
        if not args.brand or not args.action:
            parser.error("--brand and --action are required for the automata agent")
        run_automata(args.brand, args.action)
    elif args.agent == "openedswarm":
        run_openedswarm()


if __name__ == "__main__":
    main()
