import os

SCAN_ROOT = "/storage/emulated/0/Download"

EXCLUDE_DIRS = {
    "Android", ".thumbnails", ".cache", "cache",
    "node_modules", ".git", "LOST.DIR"
}

SUPPORTED_EXT = {".pdf", ".docx", ".txt"}

def find_documents():
    for dirpath, dirnames, filenames in os.walk(SCAN_ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXT:
                yield os.path.join(dirpath, f)

if __name__ == "__main__":
    print(list(find_documents()))