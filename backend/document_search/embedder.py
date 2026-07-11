# embedder.py
import requests

EMBED_URL = "http://127.0.0.1:8081/v1/embeddings"

def get_embedding(text: str) -> list[float] | None:
    try:
        resp = requests.post(EMBED_URL, json={"input": text})
        data = resp.json()
        if "data" not in data:
            print(f"  [embedding error] {data.get('error', {}).get('message', 'unknown error')}")
            return None
        return data["data"][0]["embedding"]
    except Exception as e:
        print(f"  [embedding exception] {e}")
        return None

def embed_document(text: str) -> list[float] | None:
    return get_embedding(f"search_document: {text}")

def embed_query(text: str) -> list[float] | None:
    return get_embedding(f"search_query: {text}")