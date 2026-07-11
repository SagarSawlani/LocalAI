# document_search/manifest.py
import json, os, hashlib

MANIFEST_PATH = "data/manifest.json"

def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        return json.load(open(MANIFEST_PATH))
    return {}

def save_manifest(manifest):
    json.dump(manifest, open(MANIFEST_PATH, "w"))

def file_signature(filepath):
    stat = os.stat(filepath)
    return f"{stat.st_size}_{stat.st_mtime}"

def needs_indexing(filepath, manifest):
    sig = file_signature(filepath)
    return manifest.get(filepath) != sig