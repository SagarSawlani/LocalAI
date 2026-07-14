import subprocess
from pathlib import Path

CLIP_DIR = Path.home() / "clip.cpp" / "build"

IMAGE_SEARCH = CLIP_DIR / "bin" / "image-search"
IMAGE_INDEX = CLIP_DIR / "bin" / "image-search-build"

MODEL = Path.home() / "clip.cpp" / "models" / "clip-vit-b32-q5_1.gguf"


def index_photos(directory: str):
    cmd = [
        str(IMAGE_INDEX),
        "-m",
        str(MODEL),
        directory,
    ]

    result = subprocess.run(
        cmd,
        cwd=CLIP_DIR,
        capture_output=True,
        text=True,
    )

    return result.stdout, result.stderr, result.returncode


def search_photos(query: str, top_k: int = 5):
    cmd = [
        str(IMAGE_SEARCH),
        "-n",
        str(top_k),
        query,
    ]

    result = subprocess.run(
        cmd,
        cwd=CLIP_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    photos = []

    parsing = False

    for line in result.stdout.splitlines():

        if line.startswith("distance"):
            parsing = True
            continue

        if not parsing:
            continue

        line = line.strip()

        if not line:
            continue

        parts = line.split(maxsplit=1)

        if len(parts) != 2:
            continue

        distance, path = parts

        photos.append({
            "distance": float(distance),
            "path": path
        })

    return photos
