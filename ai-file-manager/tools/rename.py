from pathlib import Path

def rename_file(src: str, dest: str, confirm: bool = False):
    """
    Rename a file/folder (dest is the full new path, same directory, new name).
    """
    src_path = Path(src).expanduser()
    dest_path = Path(dest).expanduser()

    if not src_path.exists():
        return {"status": "error", "message": f"Source does not exist: {src}"}

    if dest_path.exists():
        return {"status": "error", "message": f"Destination already exists, refusing to overwrite: {dest_path}"}

    if not confirm:
        return {
            "status": "dry_run",
            "would_rename": str(src_path),
            "to": str(dest_path),
            "note": "Nothing was renamed. Pass confirm=True to execute."
        }

    src_path.rename(dest_path)

    return {"status": "success", "renamed": str(src_path), "to": str(dest_path)}


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 3:
        print("Usage: python rename.py <source> <new_full_path> [--confirm]")
        sys.exit(1)

    result = rename_file(sys.argv[1], sys.argv[2], confirm="--confirm" in sys.argv)
    print(json.dumps(result, indent=2))
