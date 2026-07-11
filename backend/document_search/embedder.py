import requests

EMBED_URL = "http://127.0.0.1:8081/v1/embeddings"

def get_embedding(text: str) -> list[float]:
    resp = requests.post(EMBED_URL, json={"input": text})
    print("STATUS:", resp.status_code)
    print("RESPONSE:", resp.text)
    return resp.json()["data"][0]["embedding"]
def embed_document(text: str) -> list[float]:
    return get_embedding(f"search_document: {text}")

def embed_query(text: str) -> list[float]:
    return get_embedding(f"search_query: {text}")