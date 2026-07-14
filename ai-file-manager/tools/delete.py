from pathlib import Path
import shutil

def delete_file(path: str, confirm: bool = False):
    """
    Delete a file or folder. Dry-run by default — nothing happens
    unless confirm=True is explicitly passed.
    """
    target = Path(path).expanduser()

    if not target.exists():
        return {"status": "error", "message": f"Path does not exist: {path}"}

    is_dir = target.is_dir()

    if not confirm:
        return {
            "status": "dry_run",
            "would_delete": str(target),
            "type": "folder" if is_dir else "file",
            "note": "Nothing was deleted. Pass confirm=True / --confirm to execute."
        }

    try:
        if is_dir:
            shutil.rmtree(target)
        else:
            target.unlink()
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete: {e}"}

    return {"status": "success", "deleted": str(target), "type": "folder" if is_dir else "file"}


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python delete.py <path> [--confirm]")
        sys.exit(1)

    result = delete_file(sys.argv[1], confirm="--confirm" in sys.argv)
    print(json.dumps(result, indent=2))
