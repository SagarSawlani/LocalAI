import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scanner import find_documents
from extract_text import extract_text
from embedder import embed_document
from vector_store import add_chunk
from manifest import load_manifest, save_manifest, needs_indexing, file_signature

def chunk_text(text, chunk_size=350):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def main():
    manifest = load_manifest()
    files = list(find_documents())
    total = len(files)
    print(f"Found {total} files")

    new_count = 0
    for idx, filepath in enumerate(files, 1):
        if not needs_indexing(filepath, manifest):
            continue

        print(f"[{idx}/{total}] Indexing: {filepath}")
        text = extract_text(filepath)
        if not text.strip():
            print("  (no text extracted, skipping)")
            manifest[filepath] = file_signature(filepath)
            continue

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            vec = embed_document(chunk)
            add_chunk(vec, {"path": filepath, "chunk_index": i, "text": chunk[:200]})
        manifest[filepath] = file_signature(filepath)
        new_count += 1
        print(f"  indexed {len(chunks)} chunk(s)")

    save_manifest(manifest)
    print(f"Done. Newly indexed: {new_count}, skipped (unchanged): {len(files) - new_count}")

if __name__ == "__main__":
    main()