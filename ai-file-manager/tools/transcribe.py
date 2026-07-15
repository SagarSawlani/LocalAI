import subprocess
import tempfile
from pathlib import Path

WHISPER_BIN = Path("~/whisper.cpp/build/bin/whisper-cli").expanduser()
WHISPER_MODEL = Path("~/whisper.cpp/models/ggml-base-q5_1.bin").expanduser()

def convert_to_wav(input_path: Path, output_path: Path):
    """Convert any audio format to 16kHz mono WAV using ffmpeg."""
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path), "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(output_path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")


def transcribe(audio_path: str) -> dict:
    """
    Transcribe an audio file (any format ffmpeg supports) using whisper.cpp.
    Returns a dict with the transcript text and metadata.
    """
    src = Path(audio_path).expanduser()
    if not src.exists():
        return {"status": "error", "message": f"File does not exist: {audio_path}"}

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "audio.wav"

        try:
            # Skip conversion if already a WAV
            if src.suffix.lower() == ".wav":
                wav_path = src
            else:
                convert_to_wav(src, wav_path)
        except RuntimeError as e:
            return {"status": "error", "message": str(e)}

        # whisper-cli writes output to <wav_path>.txt when using -otxt
        result = subprocess.run(
            [str(WHISPER_BIN), "-m", str(WHISPER_MODEL), "-f", str(wav_path), "-nt", "-otxt", "-of", str(Path(tmpdir) / "transcript")],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            return {"status": "error", "message": f"whisper-cli failed: {result.stderr}"}

        transcript_file = Path(tmpdir) / "transcript.txt"
        if not transcript_file.exists():
            return {"status": "error", "message": "Transcript file was not created"}

        text = transcript_file.read_text().strip()

        return {
            "status": "success",
            "source_file": str(src),
            "transcript": text
        }


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file_path>")
        sys.exit(1)

    result = transcribe(sys.argv[1])
    print(json.dumps(result, indent=2))
