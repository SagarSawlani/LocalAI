import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scanner import find_documents
from extract_text import extract_text
from embedder import embed_document
from vector_store import add_chunk

def chunk_text(text, chunk_size=500):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def main():
    files = list(find_documents())
    print(f"Found {len(files)} files")

    for filepath in files:
        print(f"Indexing: {filepath}")
        text = extract_text(filepath)
        if not text.strip():
            print("  (no text extracted, skipping)")
            continue

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            vec = embed_document(chunk)
            add_chunk(vec, {"path": filepath, "chunk_index": i, "text": chunk[:200]})
        print(f"  indexed {len(chunks)} chunk(s)")

if __name__ == "__main__":
    main()