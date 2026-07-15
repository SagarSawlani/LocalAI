import requests
import json
from embedder import embed_query
from vector_store import search

LLAMA_SERVER_URL = "http://localhost:8080/v1/chat/completions"

SYSTEM_PROMPT = """You are a helpful assistant answering questions about the user's personal documents.

You will be given a user question and several retrieved text excerpts from their files, each labeled with its source file path.

Answer the question using ONLY the information in the excerpts below. Be concise and direct.
If the excerpts don't contain enough information to answer, say so clearly instead of guessing.
When relevant, mention which file the answer came from.
"""

def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[Excerpt {i} — from {c['path']}]\n{c['text']}")
    return "\n\n".join(parts)


def answer_question(query: str, top_k: int = 5) -> dict:
    """Non-streaming version — returns a plain dict with the full answer + sources."""
    query_vec = embed_query(query)
    chunks = search(query_vec, top_k=top_k)

    if not chunks:
        return {
            "answer": "I couldn't find any indexed documents relevant to that question.",
            "sources": []
        }

    context = build_context(chunks)

    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {query}\n\nExcerpts:\n{context}"}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(LLAMA_SERVER_URL, json=payload, timeout=360)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"answer": f"Could not reach LLM server: {e}", "sources": []}

    data = response.json()
    answer_text = data["choices"][0]["message"]["content"].strip()
    sources = [{"path": c["path"], "score": c["score"]} for c in chunks]

    return {"answer": answer_text, "sources": sources}


def answer_question_stream(query: str, top_k: int = 5):
    """Streaming version — yields text chunks as they arrive. For CLI/direct use only."""
    query_vec = embed_query(query)
    chunks = search(query_vec, top_k=top_k)

    if not chunks:
        yield "I couldn't find any indexed documents relevant to that question."
        return

    context = build_context(chunks)

    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {query}\n\nExcerpts:\n{context}"}
        ],
        "temperature": 0.2,
        "stream": True
    }

    with requests.post(LLAMA_SERVER_URL, json=payload, stream=True, timeout=360) as response:
        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                chunk = json.loads(data_str)
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    yield delta
                    
    # Yield sources at the very end using a special delimiter
    unique_paths = list(set([c["path"] for c in chunks]))
    if unique_paths:
        yield "\n\n__SOURCES__\n" + "\n".join(unique_paths)


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:])
    if not query:
        print("Usage: python qa.py <question>")
        sys.exit(1)
    for token in answer_question_stream(query):
        print(token, end="", flush=True)
    print()