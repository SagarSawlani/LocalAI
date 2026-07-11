from pypdf import PdfReader
import docx

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
    return ""