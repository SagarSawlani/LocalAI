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
            save_manifest(manifest)
            continue

        chunks = chunk_text(text)
        print(f"  {len(chunks)} chunk(s) to process")
        for i, chunk in enumerate(chunks):
            print(f"    chunk {i+1}/{len(chunks)}: {chunk[:80]!r}")
            vec = embed_document(chunk)
            if vec is None:
                print(f"      SKIPPED (embedding failed)")
                continue
            add_chunk(vec, {"path": filepath, "chunk_index": i, "text": chunk[:200]})

        manifest[filepath] = file_signature(filepath)
        save_manifest(manifest)
        new_count += 1
        print(f"  indexed {len(chunks)} chunk(s)")

    print(f"Done. Newly indexed: {new_count}, skipped (unchanged): {len(files) - new_count}")

if __name__ == "__main__":
    main()cd 