import shutil
from pathlib import Path

def move_file(src: str, dest: str, confirm: bool = False):
    """
    Move a file or folder from src to dest.
    If confirm=False, just reports what would happen (dry run).
    """
    src_path = Path(src).expanduser()
    dest_path = Path(dest).expanduser()

    if not src_path.exists():
        return {"status": "error", "message": f"Source does not exist: {src}"}

    # If dest is a directory, the file will land inside it with the same name
    final_dest = dest_path / src_path.name if dest_path.is_dir() else dest_path

    if final_dest.exists():
        return {
            "status": "error",
            "message": f"Destination already exists, refusing to overwrite: {final_dest}"
        }

    if not confirm:
        return {
            "status": "dry_run",
            "would_move": str(src_path),
            "to": str(final_dest),
            "note": "Nothing was moved. Pass confirm=True / --confirm to execute."
        }

    # Make sure parent dirs exist
    final_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_path), str(final_dest))

    return {
        "status": "success",
        "moved": str(src_path),
        "to": str(final_dest)
    }


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 3:
        print("Usage: python move.py <source> <destination> [--confirm]")
        sys.exit(1)

    source = sys.argv[1]
    destination = sys.argv[2]
    do_confirm = "--confirm" in sys.argv

    result = move_file(source, destination, confirm=do_confirm)
    print(json.dumps(result, indent=2))
