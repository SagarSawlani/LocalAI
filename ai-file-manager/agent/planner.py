from pathlib import Path
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools")))
from tools.locate_file import locate_file

SEARCH_ROOTS = [
    Path("/storage/emulated/0"),
]

def resolve_path_with_ambiguity(raw_path: str, choice_index: int = None):
    p = Path(raw_path).expanduser()

    if p.is_absolute() and p.exists():
        return p, None

    for root in SEARCH_ROOTS:
        candidate = root / raw_path
        if candidate.exists():
            return candidate, None

    # Exact filename search
    name = Path(raw_path).name
    storage_root = Path("/storage/emulated/0")
    if storage_root.exists():
        matches = list(storage_root.rglob(name))
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
        # Only treat as real candidates if reasonably confident
        good_matches = [m for m in semantic_matches if m["score"] > 0.5]
        if len(good_matches) == 1:
            return Path(good_matches[0]["path"]), None
        elif len(good_matches) > 1:
            if choice_index is not None and 0 <= choice_index < len(good_matches):
                return Path(good_matches[choice_index]["path"]), None
            return None, [m["path"] for m in good_matches]

    return None, None