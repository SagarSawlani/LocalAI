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

        src_resolved = resolve_path(src_raw)
        if src_resolved is None:
            return {"status": "error", "reason": f"Could not find source file: {src_raw}"}
        if isinstance(src_resolved, dict):
            return {"status": "error", "reason": f"Ambiguous source '{src_raw}', matches: {src_resolved['ambiguous']}"}

        # Destination: doesn't need to exist yet, but its parent folder should
        dest_resolved = Path(dest_raw).expanduser()
        if not dest_resolved.is_absolute():
            # try resolving as an existing folder first
            found = None
            for root in SEARCH_ROOTS:
                candidate = root / dest_raw
                if candidate.exists() and candidate.is_dir():
                    found = candidate
                    break
            dest_resolved = found if found else Path("~/storage").expanduser() / dest_raw

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