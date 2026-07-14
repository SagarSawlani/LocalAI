# agent/tools/locate_file.py
import sys, os
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend/document_search")))
from embedder import embed_query
from vector_store import search

STORAGE_ROOT = Path("/storage/emulated/0")
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".pptx", ".xlsx", ".csv", ".md"}

# Only scan these known document directories — avoids hanging on full phone scan
DOCUMENT_ROOTS = [
    STORAGE_ROOT / "Documents",
    STORAGE_ROOT / "Downloads",
    STORAGE_ROOT / "Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Documents",
    STORAGE_ROOT / "Telegram",
    STORAGE_ROOT / "MyFiles",
]


def _filename_search(query: str, top_k: int = 5) -> list:
    """Scan known document directories for files whose names contain query keywords."""
    keywords = [w.lower() for w in query.split() if len(w) > 2]
    if not keywords:
        return []

    matches = []
    for root in DOCUMENT_ROOTS:
        if not root.exists():
            continue
        for f in root.rglob("*"):
            if f.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            name_lower = f.name.lower()
            hits = sum(1 for kw in keywords if kw in name_lower)
            if hits > 0:
                matches.append((hits, str(f)))

    matches.sort(key=lambda x: -x[0])
    return [{"path": path, "score": hits / len(keywords), "source": "filename"}
            for hits, path in matches[:top_k]]


def locate_file(query: str, top_k: int = 5) -> dict:
    # Step 1: Try filename-based search first (fast, no embedding server needed)
    filename_results = _filename_search(query, top_k=top_k)
    if filename_results:
        return {"tool": "locate_file", "results": filename_results}

    # Step 2: Fall back to vector/semantic search
    try:
        vec = embed_query(query)
        results = search(vec, top_k=top_k)
    except Exception:
        return {"tool": "locate_file", "results": []}

    # Dedupe by path, keep best score per file
    seen = {}
    for r in results:
        if r["path"] not in seen or r["score"] > seen[r["path"]]["score"]:
            seen[r["path"]] = r
    files = sorted(seen.values(), key=lambda x: -x["score"])
    return {"tool": "locate_file", "results": files}