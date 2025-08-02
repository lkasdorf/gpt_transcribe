import argparse
import math
import os
import shutil
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"

API_KEY_FILE = "openai_api_key.txt"
MODEL_FILE = "openai_model.txt"
PROMPT_FILE = "summary_prompt.txt"
MAX_CHUNK_BYTES = 25 * 1024 * 1024


def _load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def transcribe(audio_path: str, model_name: str = "base") -> str:
    """Transcribe an audio file using Whisper.

    If the audio file is larger than 25 MB it is split into multiple
    segments using pydub before transcription.
    """

    import whisper
    from pydub import AudioSegment

    TEMP_DIR.mkdir(exist_ok=True)
    try:
        model = whisper.load_model(model_name)

        if os.path.getsize(audio_path) <= MAX_CHUNK_BYTES:
            print("Transcribing whole file...")
            # force FP32 on CPU to suppress FP16 warning
            result = model.transcribe(audio_path, fp16=False)
            return result["text"].strip()

        audio_format = Path(audio_path).suffix.lstrip(".").lower()
        export_format = {"m4a": "mp4", "aac": "adts"}.get(audio_format, audio_format)

        audio = AudioSegment.from_file(audio_path)
        num_chunks = math.ceil(os.path.getsize(audio_path) / MAX_CHUNK_BYTES)
        chunk_length_ms = len(audio) // num_chunks
        print(f"Transcribing audio in {num_chunks} chunks...")

        texts = []
        for i in range(num_chunks):
            start_ms = i * chunk_length_ms
            end_ms = min((i + 1) * chunk_length_ms, len(audio))
            chunk = audio[start_ms:end_ms]
            with tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}", dir=TEMP_DIR, delete=False
            ) as tmp:
                tmp_path = tmp.name
            print(f"Transcribing chunk {i + 1}/{num_chunks}...")
            chunk.export(tmp_path, format=export_format)
            # force FP32 on CPU to suppress FP16 warning
            result = model.transcribe(tmp_path, fp16=False)
            texts.append(result["text"].strip())
            os.remove(tmp_path)
            print(f"Finished chunk {i + 1}/{num_chunks}")

        return " ".join(texts)
    finally:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)


def summarize(prompt: str, transcript: str, model_name: str, api_key: str) -> str:
    """Generate a summary of the transcript using a chat model."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": f"{prompt}\n\nTranscript:\n{transcript}",
        },
    ]
    response = client.chat.completions.create(model=model_name, messages=messages)
    return response.choices[0].message.content.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe audio with Whisper and summarize the result."
    )
    parser.add_argument("audio", help="Path to the audio file to transcribe")
    parser.add_argument("output", help="Destination markdown file")
    parser.add_argument(
        "--prompt-file",
        default=PROMPT_FILE,
        help="File containing the summary prompt (default: summary_prompt.txt)",
    )
    parser.add_argument(
        "--whisper-model",
        default="base",
        help="Name of the Whisper model to use (default: base)",
    )

    parser.add_argument(
        "--summary-model",
        help="Model to use for summarization (overrides openai_model.txt)",
    )

    args = parser.parse_args()

    prompt = _load_text(args.prompt_file)
    print("Transcribing audio...")
    transcript = transcribe(args.audio, model_name=args.whisper_model)
    print("Transcription complete.")

    print("Summarizing transcript...")
    api_key = _load_text(API_KEY_FILE)
    summary_model = args.summary_model or _load_text(MODEL_FILE)
    summary = summarize(prompt, transcript, summary_model, api_key)
    print("Summary complete.")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("# Summary\n\n")
        f.write(summary)
        f.write("\n")

    print(f"Summary written to {args.output}")

if __name__ == "__main__":
    main()
