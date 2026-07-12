import os
from pathlib import Path
from datetime import datetime

def scan_directory(path: str, recursive: bool = False):
    """
    Scan a directory and return a list of file info dicts.
    """
    base = Path(path).expanduser()
    if not base.exists():
        return {"error": f"Path does not exist: {path}"}

    results = []
    walker = base.rglob("*") if recursive else base.glob("*")

    for entry in walker:
        try:
            stat = entry.stat()
            results.append({
                "name": entry.name,
                "path": str(entry),
                "is_dir": entry.is_dir(),
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "extension": entry.suffix.lower() if entry.is_file() else None,
            })
        except (PermissionError, FileNotFoundError):
            continue

    return results


if __name__ == "__main__":
    import sys
    import json

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    recursive = "-r" in sys.argv

    output = scan_directory(target, recursive=recursive)
    print(json.dumps(output, indent=2))
