# backend/document_search/routes.py (or wherever your docs routes live)
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import subprocess
from qa import answer_question_stream, answer_question
from embedder import embed_query
from vector_store import search

router = APIRouter(prefix="/docs")

@router.get("/search")
def search_documents(query: str, top_k: int = 5):
    """Fast, no LLM generation — just matching chunks."""
    vec = embed_query(query)
    results = search(vec, top_k=top_k)
    return {"results": results}

@router.post("/open")
def open_file(path: str):
    try:
        subprocess.run(["termux-open", path], check=True)
        return {"status": "opened", "path": path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/ask")
def ask_documents(query: str):
    """Full RAG answer, non-streaming (blocking, complete response)."""
    return answer_question(query)

@router.get("/ask/stream")
def ask_documents_stream(query: str):
    """Full RAG answer, streamed token-by-token."""
    return StreamingResponse(answer_question_stream(query), media_type="text/plain")