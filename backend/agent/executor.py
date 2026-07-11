import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "tools"))

from llm import get_intent
from planner import plan
from move import move_file
from scan import scan_directory


def execute(natural_language_query: str, auto_confirm: bool = False):
    intent = get_intent(natural_language_query)
    plan_result = plan(intent)

    if plan_result["status"] != "ready":
        return {"status": "failed", "stage": "planning", "detail": plan_result}

    tool = plan_result["tool"]

    if tool == "move":
        print(f"\nPlanned action: MOVE")
        print(f"  from: {plan_result['src']}")
        print(f"  to:   {plan_result['dest']}")

        if not auto_confirm:
            answer = input("Proceed? (y/n): ").strip().lower()
            if answer != "y":
                return {"status": "cancelled", "detail": plan_result}

        result = move_file(plan_result["src"], plan_result["dest"], confirm=True)
        return {"status": "executed", "tool": "move", "result": result}

    elif tool == "scan":
        result = scan_directory(plan_result["path"])
        return {"status": "executed", "tool": "scan", "result": result}

    return {"status": "failed", "stage": "execution", "detail": "Unhandled tool"}


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    if not query:
        print("Usage: python executor.py <natural language command>")
        sys.exit(1)

    result = execute(query)
    print("\n--- Result ---")
    print(json.dumps(result, indent=2, default=str))