import numpy as np
import json
import os

VEC_PATH = "data/doc_vectors.npy"
META_PATH = "data/doc_metadata.json"

def load_store():
    if os.path.exists(VEC_PATH):
        vectors = np.load(VEC_PATH)
        metadata = json.load(open(META_PATH))
    else:
        vectors = np.zeros((0, 768))
        metadata = []
    return vectors, metadata

def save_store(vectors, metadata):
    os.makedirs("data", exist_ok=True)
    np.save(VEC_PATH, vectors)
    json.dump(metadata, open(META_PATH, "w"))

def add_chunk(vector, meta):
    vectors, metadata = load_store()
    vectors = np.vstack([vectors, vector])
    metadata.append(meta)
    save_store(vectors, metadata)

def search(query_vector, top_k=5):
    vectors, metadata = load_store()
    if len(vectors) == 0:
        return []
    query_vector = np.array(query_vector)
    sims = vectors @ query_vector / (
        np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_vector) + 1e-8
    )
    top_idx = np.argsort(sims)[::-1][:top_k]
    return [{"score": float(sims[i]), **metadata[i]} for i in top_idx]