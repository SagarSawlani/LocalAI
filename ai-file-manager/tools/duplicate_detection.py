import hashlib
from pathlib import Path
from collections import defaultdict

def hash_file(path: Path, chunk_size: int = 8192) -> str:
    """MD5 hash of file content, read in chunks (safe for large files)."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(path: str):
    """
    Scan a directory recursively, group files by content hash,
    return groups where more than one file shares the same content.
    """
    base = Path(path).expanduser()
    if not base.exists():
        return {"error": f"Path does not exist: {path}"}

    size_groups = defaultdict(list)
    for entry in base.rglob("*"):
        if entry.is_file():
            try:
                size_groups[entry.stat().st_size].append(entry)
            except (PermissionError, FileNotFoundError):
                continue

    hash_groups = defaultdict(list)
    for size, files in size_groups.items():
        if len(files) < 2:
            continue
        for f in files:
            try:
                file_hash = hash_file(f)
                hash_groups[file_hash].append(f)
            except (PermissionError, FileNotFoundError):
                continue

    duplicate_sets = []
    total_wasted_bytes = 0

    for file_hash, files in hash_groups.items():
        if len(files) > 1:
            size = files[0].stat().st_size
            wasted = size * (len(files) - 1)
            total_wasted_bytes += wasted
            duplicate_sets.append({
                "hash": file_hash,
                "size_bytes": size,
                "count": len(files),
                "files": [str(f) for f in files],
                "wasted_bytes": wasted
            })

    duplicate_sets.sort(key=lambda x: x["wasted_bytes"], reverse=True)

    return {
        "scanned_path": str(base),
        "duplicate_sets_found": len(duplicate_sets),
        "total_wasted_bytes": total_wasted_bytes,
        "duplicate_sets": duplicate_sets
    }


if __name__ == "__main__":
    import sys
    import json

    target = sys.argv[1] if len(sys.argv) > 1 else "~/storage"
    result = find_duplicates(target)
    print(json.dumps(result, indent=2))
