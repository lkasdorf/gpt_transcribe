"""Batch process audio files from the `audio` directory.

This script processes all audio files placed in the `audio` directory and
writes summarized Markdown and PDF files to the `output` directory. After a
file is processed its name is stored in `processed.log` to avoid duplicate
work.

The output filename follows the pattern ``YYYYMMDD_NameOfTheFile.md`` with a
matching ``.pdf`` file.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Set

from pydub import AudioSegment

import transcribe_summary

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
OUTPUT_DIR = BASE_DIR / "output"
LOG_FILE = BASE_DIR / "processed.log"
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}


def _load_processed() -> Set[str]:
    if not LOG_FILE.exists():
        return set()
    filenames: Set[str] = set()
    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            filenames.add(line.split(",", 1)[0])
    return filenames


def _append_processed(
    filename: str,
    size_bytes: int,
    duration_sec: float,
    method: str,
    elapsed: float,
) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(
            f"{filename},{size_bytes},{duration_sec:.2f},{method},{elapsed:.2f},{timestamp}\n"
        )


def _process_file(path: Path, method: str, language: str, whisper_model: str) -> None:
    """Transcribe a single audio file and write its summary."""
    print(
        f"Transcribing {path.name} using {whisper_model} via {method}..."
    )
    api_key = transcribe_summary._load_text(
        transcribe_summary.BASE_DIR / transcribe_summary.API_KEY_FILE
    )

    size_bytes = path.stat().st_size
    audio = AudioSegment.from_file(path)
    duration_sec = len(audio) / 1000
    start = time.time()
    transcript = transcribe_summary.transcribe(
        str(path),
        model_name=whisper_model,
        method=method,
        api_key=api_key if method == "api" else None,
    )
    elapsed = time.time() - start

    print("Creating summary...")
    prompt = transcribe_summary._load_text(
        transcribe_summary.BASE_DIR / transcribe_summary.PROMPT_FILE
    )
    summary_model = transcribe_summary._load_text(
        transcribe_summary.BASE_DIR / transcribe_summary.MODEL_FILE
    )
    summary = transcribe_summary.summarize(
        prompt, transcript, summary_model, api_key, language
    )
    summary = transcribe_summary.strip_code_fences(summary)

    now = datetime.now()
    output_name = f"{now:%Y%m%d}_{path.stem}.md"
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / output_name
    heading = "Summary" if language == "en" else "Zusammenfassung"
    markdown_content = f"# {heading}\n\n" + summary + "\n"
    with output_path.open("w", encoding="utf-8") as f:
        f.write(markdown_content)
    pdf_path = OUTPUT_DIR / f"{now:%Y%m%d}_{path.stem}.pdf"
    transcribe_summary.markdown_to_pdf(markdown_content, str(pdf_path))
    _append_processed(path.name, size_bytes, duration_sec, method, elapsed)
    print(f"Finished: {output_path}")
    print(f"PDF saved to {pdf_path}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch transcribe audio files and summarize them."
    )
    parser.add_argument(
        "--method",
        choices=["api", "local"],
        default="api",
        help="Transcription backend: 'api' or 'local'",
    )
    parser.add_argument(
        "--language",
        choices=["en", "de"],
        default="en",
        help="Language for the generated summaries",
    )
    args = parser.parse_args()

    whisper_model = transcribe_summary.load_whisper_model()

    AUDIO_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    processed = _load_processed()
    for audio_file in AUDIO_DIR.iterdir():
        if not audio_file.is_file():
            continue
        if audio_file.suffix.lower() not in AUDIO_EXTS:
            continue
        if audio_file.name in processed:
            print(f"{audio_file.name} has already been processed.")
            continue
        _process_file(audio_file, args.method, args.language, whisper_model)


if __name__ == "__main__":
    main()
