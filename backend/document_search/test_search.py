import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from embedder import embed_query
from vector_store import search

query = "what is the turnboc code to draw a circle?"  # change to something relevant to your test PDFs
vec = embed_query(query)
results = search(vec)

for r in results:
    print(f"{r['score']:.3f}  {r['path']}  chunk {r['chunk_index']}")
    print(f"   {r['text'][:100]}")