from pathlib import Path

# Known base locations the LLM might refer to loosely.
# We search these when a path from the LLM isn't absolute.
SEARCH_ROOTS = [
    Path("~/storage").expanduser(),
    Path("~/storage/downloads").expanduser(),
    Path("~/storage/dcim").expanduser(),
    Path("~/storage/pictures").expanduser(),
    Path("~/storage/movies").expanduser(),
    Path("~/storage/music").expanduser(),
    Path("~/storage/shared").expanduser(),
]


def resolve_path(raw_path: str):
    """
    Try to turn a possibly-relative/fuzzy path from the LLM into
    a real, existing absolute path on disk.
    Returns the resolved Path, or None if nothing matched.
    """
    p = Path(raw_path).expanduser()

    # Already absolute and exists
    if p.is_absolute() and p.exists():
        return p

    # Try resolving relative to each known root
    for root in SEARCH_ROOTS:
        candidate = root / raw_path
        if candidate.exists():
            return candidate

    # Last resort: search by filename only, under ~/storage (shallow-ish)
    name = Path(raw_path).name
    storage_root = Path("~/storage").expanduser()
    if storage_root.exists():
        matches = list(storage_root.rglob(name))
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            return {"ambiguous": [str(m) for m in matches]}

    return None

def resolve_path_with_ambiguity(raw_path: str, choice_index: int = None):
    """
    Like resolve_path, but if there are multiple matches, lets the
    caller pick one by index. Returns (resolved_path_or_None, ambiguous_list_or_None).
    """
    p = Path(raw_path).expanduser()

    if p.is_absolute() and p.exists():
        return p, None

    for root in SEARCH_ROOTS:
        candidate = root / raw_path
        if candidate.exists():
            return candidate, None

    name = Path(raw_path).name
    storage_root = Path("~/storage").expanduser()
    if storage_root.exists():
        matches = list(storage_root.rglob(name))
        if len(matches) == 1:
            return matches[0], None
        elif len(matches) > 1:
            if choice_index is not None and 0 <= choice_index < len(matches):
                return matches[choice_index], None
            return None, matches

    return None, None

def resolve_dest(dest_raw: str):
    """
    Resolve a destination folder path the same way plan() does for move,
    so this logic isn't duplicated/drifted between planner and executor.
    """
    dest_resolved = Path(dest_raw).expanduser()
    if dest_resolved.is_absolute():
        return dest_resolved

    for root in SEARCH_ROOTS:
        candidate = root / dest_raw
        if candidate.exists() and candidate.is_dir():
            return candidate

    return Path("~/storage").expanduser() / dest_raw

def plan(intent: dict):
    """
    Take a raw intent dict from the LLM and turn it into a fully
    resolved, ready-to-execute plan. Returns a dict with either
    a resolved plan or an error explaining what's wrong.
    """
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
