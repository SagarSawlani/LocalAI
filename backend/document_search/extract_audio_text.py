import subprocess
import tempfile
import os

# Point these to the absolute paths where you compiled whisper and downloaded the model
WHISPER_BIN = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
MODEL_PATH = os.path.expanduser("~/models/ggml-base-q5_1.bin")

def extract_transcript(audio_path: str) -> str:
    """Converts any audio file to 16kHz WAV and runs whisper to get the text."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = os.path.join(tmpdir, "audio.wav")
        
        # 1. Use ffmpeg to convert to 16kHz, mono, 16-bit PCM WAV
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_path,
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            wav_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 2. Run whisper-cli
        # -otxt tells whisper to generate an 'audio.wav.txt' file with the transcript
        subprocess.run([
            WHISPER_BIN,
            "-m", MODEL_PATH,
            "-f", wav_path,
            "-otxt"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 3. Read the resulting transcript
        txt_path = wav_path + ".txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                # whisper sometimes includes [BLANK_AUDIO] tokens, you might want to filter them out
                transcript = f.read().strip()
                return transcript
        else:
            return ""

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        transcript = extract_transcript(sys.argv[1])
        print("--- Transcript ---")
        print(transcript)
    else:
        print("Usage: python extract_audio_text.py <audio_file_path>")
