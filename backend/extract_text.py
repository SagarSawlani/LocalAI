from pypdf import PdfReader
import docx
import sys
import os

# Ensure the parent directory is in sys.path to allow document_search imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from document_search.extract_audio_text import extract_transcript

MAX_PAGES = 500  # tune as you like

def extract_text(filepath: str) -> str:
    if filepath.endswith(".pdf"):
        reader = PdfReader(filepath)
        if len(reader.pages) > MAX_PAGES:
            print(f"  Skipping (too large: {len(reader.pages)} pages)")
            return ""
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif filepath.endswith(".docx"):
        doc = docx.Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    elif filepath.endswith(".txt"):
        return open(filepath, encoding="utf-8", errors="ignore").read()
    elif filepath.lower().endswith((".mp3", ".m4a", ".opus", ".wav")):
        print(f"  (transcribing audio...)")
        return extract_transcript(filepath)
    return ""