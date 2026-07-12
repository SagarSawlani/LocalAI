# agent/tools/locate_file.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend/document_search")))
from embedder import embed_query
from vector_store import search

def locate_file(query: str, top_k: int = 5) -> dict:
    vec = embed_query(query)
    results = search(vec, top_k=top_k)
    # dedupe by path, keep best score per file
    seen = {}
    for r in results:
        if r["path"] not in seen or r["score"] > seen[r["path"]]["score"]:
            seen[r["path"]] = r
    files = sorted(seen.values(), key=lambda x: -x["score"])
    return {"tool": "locate_file", "results": files}