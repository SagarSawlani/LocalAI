from pathlib import Path
from datetime import datetime

CATEGORY_MAP = {
    "images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic", ".svg"},
    "videos": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".3gp"},
    "documents": {".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"},
    "audio": {".mp3", ".wav", ".m4a", ".ogg", ".flac"},
    "archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "apps": {".apk"},
}


def categorize_extension(ext: str) -> str:
    ext = ext.lower()
    for category, extensions in CATEGORY_MAP.items():
        if ext in extensions:
            return category
    return "other"


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"


def storage_insights(path: str, top_n_largest: int = 5):
    """
    Recursively scan a directory and return a categorized breakdown:
    total size, file count per category, and the largest files overall.
    """
    base = Path(path).expanduser()
    if not base.exists():
        return {"error": f"Path does not exist: {path}"}

    categories = {}
    all_files = []
    total_size = 0
    total_files = 0
    errors = 0

    for entry in base.rglob("*"):
        if entry.is_dir():
            continue
        try:
            stat = entry.stat()
        except (PermissionError, FileNotFoundError):
            errors += 1
            continue

        size = stat.st_size
        ext = entry.suffix.lower()
        category = categorize_extension(ext)

        if category not in categories:
            categories[category] = {"count": 0, "size_bytes": 0}
        categories[category]["count"] += 1
        categories[category]["size_bytes"] += size

        total_size += size
        total_files += 1
        all_files.append({"path": str(entry), "size_bytes": size})

    # Human-readable summary per category, sorted biggest first
    category_summary = []
    for cat, data in sorted(categories.items(), key=lambda x: x[1]["size_bytes"], reverse=True):
        category_summary.append({
            "category": cat,
            "count": data["count"],
            "size_bytes": data["size_bytes"],
            "size_readable": human_size(data["size_bytes"])
        })

    # Largest individual files
    largest = sorted(all_files, key=lambda x: x["size_bytes"], reverse=True)[:top_n_largest]
    for f in largest:
        f["size_readable"] = human_size(f["size_bytes"])

    return {
        "scanned_path": str(base),
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_readable": human_size(total_size),
        "unreadable_files_skipped": errors,
        "by_category": category_summary,
        "largest_files": largest,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


if __name__ == "__main__":
    import sys
    import json

    target = sys.argv[1] if len(sys.argv) > 1 else "~/storage"
    result = storage_insights(target)
    print(json.dumps(result, indent=2))
