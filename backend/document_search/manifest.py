import json, os

MANIFEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "manifest.json")

def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        return json.load(open(MANIFEST_PATH))
    return {}

def save_manifest(manifest):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    json.dump(manifest, open(MANIFEST_PATH, "w"))

def file_signature(filepath):
    stat = os.stat(filepath)
    return f"{stat.st_size}_{stat.st_mtime}"

def needs_indexing(filepath, manifest):
    return manifest.get(filepath) != file_signature(filepath)