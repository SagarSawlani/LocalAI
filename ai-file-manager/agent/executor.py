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
from locate_file import locate_file
from search_documents import search_documents

def execute(natural_language_query: str, auto_confirm: bool = False, choice_index: int = None):
    intent = get_intent(natural_language_query)
    plan_result = plan(intent)

    if plan_result["status"] == "ambiguous":
        if choice_index is None:
            # API-safe: return the choices instead of blocking on input()
            return {"status": "needs_choice", "detail": plan_result}

        try:
            chosen_src = plan_result["matches"][choice_index]
        except (IndexError, TypeError):
            return {"status": "cancelled", "detail": "Invalid selection"}

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
        if not auto_confirm:
            return {"status": "needs_confirmation", "tool": "move", "plan": plan_result}
        result = move_file(plan_result["src"], plan_result["dest"], confirm=True)
        return {"status": "executed", "tool": "move", "result": result}

    elif tool == "rename":
        if not auto_confirm:
            return {"status": "needs_confirmation", "tool": "rename", "plan": plan_result}
        result = rename_file(plan_result["src"], plan_result["dest"], confirm=True)
        return {"status": "executed", "tool": "rename", "result": result}

    elif tool == "scan":
        result = scan_directory(plan_result["path"])
        return {"status": "executed", "tool": "scan", "result": result}

    elif tool == "insights":
        result = storage_insights(plan_result["path"])
        return {"status": "executed", "tool": "insights", "result": result}

    elif tool == "locate_file":
        result = locate_file(plan_result["query"])
        return {"status": "executed", "tool": "locate_file", "result": result}

    elif tool == "search_documents":
        result = search_documents(plan_result["query"])
        return {"status": "executed", "tool": "search_documents", "result": result}

    return {"status": "failed", "stage": "execution", "detail": "Unhandled tool"}


if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    if not query:
        print("Usage: python executor.py <natural language command>")
        sys.exit(1)

    result = execute(query)

    # CLI-only: interactively handle needs_confirmation / needs_choice
    if result["status"] == "needs_choice":
        print("\nMultiple files match. Which one did you mean?")
        for i, m in enumerate(result["detail"]["matches"]):
            print(f"  [{i}] {m}")
        choice = input("Enter number (or 'c' to cancel): ").strip()
        if choice.lower() != "c":
            result = execute(query, auto_confirm=True, choice_index=int(choice))

    elif result["status"] == "needs_confirmation":
        print(f"\nPlanned action: {result['tool'].upper()}")
        print(json.dumps(result["plan"], indent=2))
        answer = input("Proceed? (y/n): ").strip().lower()
        if answer == "y":
            result = execute(query, auto_confirm=True)
        else:
            result = {"status": "cancelled", "detail": result["plan"]}

    print("\n--- Result ---")
    print(json.dumps(result, indent=2, default=str))