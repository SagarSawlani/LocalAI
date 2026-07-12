import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "tools"))

from llm import get_intent
from planner import plan, resolve_dest
from move import move_file
from scan import scan_directory
from rename import rename_file
from storage_insights import storage_insights

def execute(natural_language_query: str, auto_confirm: bool = False):
    intent = get_intent(natural_language_query)
    plan_result = plan(intent)

    if plan_result["status"] == "ambiguous":
        print(f"\nMultiple files match. Which one did you mean?")
        for i, m in enumerate(plan_result["matches"]):
            print(f"  [{i}] {m}")
        if auto_confirm:
            return {"status": "cancelled", "detail": "Ambiguous match, cannot auto-confirm"}
        choice = input("Enter number (or 'c' to cancel): ").strip()
        if choice.lower() == "c":
            return {"status": "cancelled", "detail": plan_result}
        try:
            idx = int(choice)
            chosen_src = plan_result["matches"][idx]
        except (ValueError, IndexError):
            return {"status": "cancelled", "detail": "Invalid selection"}

        # Rebuild a resolved plan using the chosen path
        if plan_result["tool"] == "move":
            resolved_dest = resolve_dest(plan_result["dest"])
            plan_result = {"status": "ready", "tool": "move", "src": chosen_src, "dest": str(resolved_dest)}
        elif plan_result["tool"] == "rename":
            new_name = plan_result["new_name"]
            dest = str(Path(chosen_src).parent / new_name)
            plan_result = {"status": "ready", "tool": "rename", "src": chosen_src, "dest": dest}

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

    elif tool == "insights":
        result = storage_insights(plan_result["path"])
        return {"status": "executed", "tool": "insights", "result": result}

    elif tool == "rename":
        print(f"\nPlanned action: RENAME")
        print(f"  from: {plan_result['src']}")
        print(f"  to:   {plan_result['dest']}")

        if not auto_confirm:
            answer = input("Proceed? (y/n): ").strip().lower()
            if answer != "y":
                return {"status": "cancelled", "detail": plan_result}

        result = rename_file(plan_result["src"], plan_result["dest"], confirm=True)
        return {"status": "executed", "tool": "rename", "result": result}

    return {"status": "failed", "stage": "execution", "detail": "Unhandled tool"}


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    if not query:
        print("Usage: python executor.py <natural language command>")
        sys.exit(1)

    result = execute(query)
    print("\n--- Result ---")
    print(json.dumps(result, indent=2, default=str))
