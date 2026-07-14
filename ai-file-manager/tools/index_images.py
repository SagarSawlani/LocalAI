import os
import json
import subprocess
import hashlib
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

import sys
SCAN_ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else "/storage/emulated/0"
IMAGE_EXT = {".jpg", ".jpeg", ".png"}
RESIZED_DIR = os.path.expanduser("~/tmp_resized_images")
CLIP_INDEX_DIR = os.path.expanduser("~/clip.cpp/build/")  # where images.paths/usearch live
MANIFEST_PATH = os.path.expanduser("~/clip_manifest.json")
MAPPING_PATH = os.path.expanduser("~/clip_mapping.json")
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

def load_mapping():
    if os.path.exists(MAPPING_PATH):
        return json.load(open(MAPPING_PATH))
    return {}

def save_mapping(mapping):
    json.dump(mapping, open(MAPPING_PATH, "w"))


def file_signature(filepath):
    stat = os.stat(filepath)
    return f"{stat.st_size}_{stat.st_mtime}"


def main():
    os.makedirs(RESIZED_DIR, exist_ok=True)
    os.makedirs(CLIP_INDEX_DIR, exist_ok=True)

    manifest = load_manifest()
    mapping = load_mapping()
    images = list(find_images())
    total = len(images)
    print(f"Found {total} images")

    to_process = []
    for path in images:
        sig = file_signature(path)
        if manifest.get(path) != sig:
            to_process.append((path, sig))

    print(f"{len(to_process)} new/changed images to process, {total - len(to_process)} already done")

    # We only skip resizing if there are no new images, BUT we might still need to rebuild the index 
    # if this script was run to just refresh the images.paths file.
    
    resized_paths = []
    if to_process:
        for idx, (path, sig) in enumerate(to_process, 1):
            try:
                img = Image.open(path).convert("RGB")
                img.thumbnail((512, 512))
                out_name = hashlib.md5(path.encode()).hexdigest() + ".jpg"
                out_path = os.path.join(RESIZED_DIR, out_name)
                img.save(out_path, "JPEG", quality=85)
                resized_paths.append(out_path)
                
                manifest[path] = sig  
                mapping[out_path] = path  # Store the reverse mapping!
            except Exception as e:
                print(f"  [{idx}/{len(to_process)}] Failed on {path}: {e}")

            if idx % 100 == 0:
                print(f"  Resized {idx}/{len(to_process)}")
                save_manifest(manifest)
                save_mapping(mapping)

        save_manifest(manifest)
        save_mapping(mapping)
        print(f"Resized {len(resized_paths)} images into {RESIZED_DIR}")

    # Run CLIP indexer — MUST run with cwd=CLIP_INDEX_DIR
    print("Running image-search-build...")
    result = subprocess.run(
        [CLIP_BUILD_BIN, "-m", CLIP_MODEL, "-t", THREADS, RESIZED_DIR],
        cwd=CLIP_INDEX_DIR
    )

    if result.returncode != 0:
        print(f"ERROR: image-search-build failed with exit code {result.returncode}")
        return

    # REWRITE images.paths so that it contains the ORIGINAL paths, not the resized thumbnail paths
    images_paths_file = os.path.join(CLIP_INDEX_DIR, "images.paths")
    if os.path.exists(images_paths_file):
        with open(images_paths_file, "r") as f:
            lines = f.readlines()
        
        with open(images_paths_file, "w") as f:
            for line in lines:
                line = line.strip()
                # If the line is a resized image path, replace it with the original path
                if line in mapping:
                    f.write(mapping[line] + "\n")
                else:
                    f.write(line + "\n")
                    
        print("Restored original image paths in the index.")
    
    print(f"Done! Index saved to: {CLIP_INDEX_DIR}")


if __name__ == "__main__":
    main()
