import os
import json
import shutil
import subprocess
import hashlib
from PIL import Image

SCAN_ROOT = "/storage/emulated/0"
IMAGE_EXT = {".jpg", ".jpeg", ".png"}
RESIZED_DIR = os.path.expanduser("~/tmp_resized_images")
CLIP_INDEX_DIR = os.path.expanduser("~/clip.cpp/build/")  # where images.paths/usearch live
MANIFEST_PATH = os.path.expanduser("~/clip_manifest.json")
CLIP_BUILD_BIN = os.path.expanduser("~/clip.cpp/build/bin/image-search-build")
CLIP_MODEL = os.path.expanduser("~/clip.cpp/models/clip-vit-b32-q5_1.gguf")
THREADS = "8"

EXCLUDE_DIRS = {"Android", ".thumbnails", ".cache", "cache", "node_modules", ".git"}


def find_images():
    for dirpath, dirnames, filenames in os.walk(SCAN_ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            if os.path.splitext(f)[1].lower() in IMAGE_EXT:
                yield os.path.join(dirpath, f)


def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        return json.load(open(MANIFEST_PATH))
    return {}


def save_manifest(manifest):
    json.dump(manifest, open(MANIFEST_PATH, "w"))


def file_signature(filepath):
    stat = os.stat(filepath)
    return f"{stat.st_size}_{stat.st_mtime}"


def main():
    # Always start with a clean resized dir so stale copies don't pollute the index
    if os.path.exists(RESIZED_DIR):
        shutil.rmtree(RESIZED_DIR)
    os.makedirs(RESIZED_DIR)
    os.makedirs(CLIP_INDEX_DIR, exist_ok=True)

    manifest = load_manifest()
    images = list(find_images())
    total = len(images)
    print(f"Found {total} images")

    to_process = []
    for path in images:
        sig = file_signature(path)
        if manifest.get(path) != sig:
            to_process.append((path, sig))

    print(f"{len(to_process)} new/changed images to process, {total - len(to_process)} already done")

    if not to_process:
        print("Nothing new to index.")
        return

    # Resize each new image into RESIZED_DIR
    resized_paths = []
    for idx, (path, sig) in enumerate(to_process, 1):
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((512, 512))
            out_name = hashlib.md5(path.encode()).hexdigest() + ".jpg"
            out_path = os.path.join(RESIZED_DIR, out_name)
            img.save(out_path, "JPEG", quality=85)
            resized_paths.append(out_path)
            manifest[path] = sig  # mark done once resized successfully
        except Exception as e:
            print(f"  [{idx}/{len(to_process)}] Failed on {path}: {e}")

        if idx % 100 == 0:
            print(f"  Resized {idx}/{len(to_process)}")
            save_manifest(manifest)  # incremental save for crash safety

    save_manifest(manifest)
    print(f"Resized {len(resized_paths)} images into {RESIZED_DIR}")

    if not resized_paths:
        print("No images were resized successfully, skipping indexing.")
        return

    # Run CLIP indexer — MUST run with cwd=CLIP_INDEX_DIR so images.paths and
    # images.usearch are saved where image-search and photo_search.py can find them
    print("Running image-search-build...")
    result = subprocess.run(
        [CLIP_BUILD_BIN, "-m", CLIP_MODEL, "-t", THREADS, RESIZED_DIR],
        cwd=CLIP_INDEX_DIR
    )

    if result.returncode != 0:
        print(f"ERROR: image-search-build failed with exit code {result.returncode}")
    else:
        print(f"Done! Index saved to: {CLIP_INDEX_DIR}")
        print("You can now search photos from the app or with:")
        print(f"  cd {CLIP_INDEX_DIR} && ./bin/image-search -m {CLIP_MODEL} -n 5 \"your query\"")


if __name__ == "__main__":
    main()
