# backend/document_search/audio_routes.py
from fastapi import APIRouter, UploadFile, File
import shutil
import tempfile
import os
from extract_audio_text import extract_transcript

router = APIRouter(prefix="/audio")

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Accepts an audio file (any format ffmpeg supports: m4a, opus, wav, etc.)
    and returns the transcribed text.
    """
    suffix = os.path.splitext(file.filename)[1] or ".m4a"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        transcript = extract_transcript(tmp_path)
        return {"status": "success", "transcript": transcript}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        os.remove(tmp_path)
