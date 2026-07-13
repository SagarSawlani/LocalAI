from pathlib import Path
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))
from locate_file import locate_file

SEARCH_ROOTS = [
    Path("/storage/emulated/0"),
]


def resolve_path(raw_path: str):
    p = Path(raw_path).expanduser()

    if p.is_absolute() and p.exists():
        return p

    for root in SEARCH_ROOTS:
        candidate = root / raw_path
        if candidate.exists():
            return candidate

    name = Path(raw_path).name
    storage_root = Path("/storage/emulated/0")
    if storage_root.exists():
        matches = list(storage_root.rglob(name))
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            return {"ambiguous": [str(m) for m in matches]}

    return None


def resolve_path_with_ambiguity(raw_path: str, choice_index: int = None):
    p = Path(raw_path).expanduser()

    if p.is_absolute() and p.exists():
        return p, None

    for root in SEARCH_ROOTS:
        candidate = root / raw_path
        if candidate.exists():
            return candidate, None

    storage_root = Path("/storage/emulated/0")
    name = Path(raw_path).name

    # Try exact match with the name as-is
    matches = list(storage_root.rglob(name)) if storage_root.exists() else []

    # If no extension was given, also try common document extensions
    if not matches and not Path(name).suffix:
        for ext in [".pdf", ".docx", ".txt"]:
            matches.extend(storage_root.rglob(name + ext))

    if len(matches) == 1:
        return matches[0], None
    elif len(matches) > 1:
        if choice_index is not None and 0 <= choice_index < len(matches):
            return matches[choice_index], None
        return None, matches

    # Exact match failed entirely — fall back to semantic search
    semantic_result = locate_file(raw_path, top_k=3)
    semantic_matches = semantic_result.get("results", [])

    if len(semantic_matches) == 1:
        return Path(semantic_matches[0]["path"]), None
    elif len(semantic_matches) > 1:
        good_matches = [m for m in semantic_matches if m["score"] > 0.5]
        if len(good_matches) == 1:
            return Path(good_matches[0]["path"]), None
        elif len(good_matches) > 1:
            if choice_index is not None and 0 <= choice_index < len(good_matches):
                return Path(good_matches[choice_index]["path"]), None
            return None, [m["path"] for m in good_matches]

    return None, None

KNOWN_FOLDERS = {
    "downloads": "/storage/emulated/0/Download",
    "download": "/storage/emulated/0/Download",
    "documents": "/storage/emulated/0/Documents",
    "pictures": "/storage/emulated/0/Pictures",
    "dcim": "/storage/emulated/0/DCIM",
    "movies": "/storage/emulated/0/Movies",
    "music": "/storage/emulated/0/Music",
}

def resolve_dest(dest_raw: str):
    dest_resolved = Path(dest_raw).expanduser()
    if dest_resolved.is_absolute():
        return dest_resolved

    lower = dest_raw.strip().lower()
    if lower in KNOWN_FOLDERS:
        return Path(KNOWN_FOLDERS[lower])

    for root in SEARCH_ROOTS:
        candidate = root / dest_raw
        if candidate.exists() and candidate.is_dir():
            return candidate

    return Path("/storage/emulated/0") / dest_raw

def plan(intent: dict):
    tool = intent.get("tool")

    if tool == "move":
        src_raw = intent.get("src")
        dest_raw = intent.get("dest")

        if not src_raw or not dest_raw:
            return {"status": "error", "reason": "Missing src or dest in intent"}

        src_resolved, ambiguous = resolve_path_with_ambiguity(src_raw)
        if ambiguous:
            return {
                "status": "ambiguous",
                "tool": "move",
                "matches": [str(m) for m in ambiguous],
                "dest": dest_raw
            }
        if src_resolved is None:
            return {"status": "error", "reason": f"Could not find source file: {src_raw}"}

        dest_resolved = resolve_dest(dest_raw)

        return {
            "status": "ready",
            "tool": "move",
            "src": str(src_resolved),
            "dest": str(dest_resolved)
        }

    elif tool == "scan":
        path_raw = intent.get("path")
        if not path_raw:
            return {"status": "error", "reason": "Missing path in intent"}

        resolved = resolve_path(path_raw)
        if resolved is None:
            return {"status": "error", "reason": f"Could not find path: {path_raw}"}
        if isinstance(resolved, dict):
            return {"status": "error", "reason": f"Ambiguous path '{path_raw}', matches: {resolved['ambiguous']}"}

        return {"status": "ready", "tool": "scan", "path": str(resolved)}

    elif tool == "insights":
        path_raw = intent.get("path")
        if not path_raw:
            return {"status": "error", "reason": "Missing path in intent"}

        resolved = resolve_path(path_raw)
        if resolved is None:
            return {"status": "error", "reason": f"Could not find path: {path_raw}"}
        if isinstance(resolved, dict):
            return {"status": "error", "reason": f"Ambiguous path '{path_raw}', matches: {resolved['ambiguous']}"}

        return {"status": "ready", "tool": "insights", "path": str(resolved)}

    elif tool == "rename":
        src_raw = intent.get("src")
        new_name = intent.get("new_name")

        if not src_raw or not new_name:
            return {"status": "error", "reason": "Missing src or new_name in intent"}

        src_resolved, ambiguous = resolve_path_with_ambiguity(src_raw)
        if ambiguous:
            return {
                "status": "ambiguous",
                "tool": "rename",
                "matches": [str(m) for m in ambiguous],
                "new_name": new_name
            }
        if src_resolved is None:
            return {"status": "error", "reason": f"Could not find file: {src_raw}"}

        dest_resolved = src_resolved.parent / new_name

        return {
            "status": "ready",
            "tool": "rename",
            "src": str(src_resolved),
            "dest": str(dest_resolved)
        }

    elif tool == "locate_file":
        query = intent.get("query")
        if not query:
            return {"status": "error", "reason": "Missing query in intent"}
        return {"status": "ready", "tool": "locate_file", "query": query}

    elif tool == "search_documents":
        query = intent.get("query")
        if not query:
            return {"status": "error", "reason": "Missing query in intent"}
        return {"status": "ready", "tool": "search_documents", "query": query}

    elif tool == "unknown" or tool == "error":
        return {"status": "error", "reason": intent.get("reason", "Unknown intent")}

    else:
        return {"status": "error", "reason": f"Unrecognized tool: {tool}"}


if __name__ == "__main__":
    import sys
    import json
    sys.path.append(str(Path(__file__).parent))
    from llm import get_intent

    query = " ".join(sys.argv[1:])
    if not query:
        print("Usage: python planner.py <natural language command>")
        sys.exit(1)

    intent = get_intent(query)
    result = plan(intent)
    print(json.dumps(result, indent=2))