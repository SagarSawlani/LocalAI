import requests
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
        response = requests.post(LLAMA_SERVER_URL, json=payload, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"answer": f"Could not reach LLM server: {e}", "sources": []}

    data = response.json()
    answer_text = data["choices"][0]["message"]["content"].strip()

    sources = [{"path": c["path"], "score": c["score"]} for c in chunks]

    return {"answer": answer_text, "sources": sources}


if __name__ == "__main__":
    import sys, json

    query = " ".join(sys.argv[1:])
    if not query:
        print("Usage: python qa.py <question>")
        sys.exit(1)

    result = answer_question(query)
    print(json.dumps(result, indent=2))