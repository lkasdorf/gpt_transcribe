"""Batch process audio files from the `audio` directory.

This script processes all audio files placed in the `audio` directory and
writes summarized Markdown files to the `output` directory. After a file is
processed its name is stored in `processed.log` to avoid duplicate work.

The output filename follows the pattern ``YYYYMMDD_NameOfTheFile.md``.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Set

import transcribe_summary

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
OUTPUT_DIR = BASE_DIR / "output"
LOG_FILE = BASE_DIR / "processed.log"
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}


def _load_processed() -> Set[str]:
    if not LOG_FILE.exists():
        return set()
    with LOG_FILE.open("r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def _append_processed(filename: str) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{filename}\n")


def _process_file(path: Path) -> None:
    print(f"Transkribiere {path.name} ...")
    transcript = transcribe_summary.transcribe(str(path))
    print("Erstelle Zusammenfassung ...")
    prompt = transcribe_summary._load_text(
        transcribe_summary.BASE_DIR / transcribe_summary.PROMPT_FILE
    )
    api_key = transcribe_summary._load_text(
        transcribe_summary.BASE_DIR / transcribe_summary.API_KEY_FILE
    )
    summary_model = transcribe_summary._load_text(
        transcribe_summary.BASE_DIR / transcribe_summary.MODEL_FILE
    )
    summary = transcribe_summary.summarize(
        prompt, transcript, summary_model, api_key
    )
    now = datetime.now()
    output_name = f"{now:%Y%m%d}_{path.stem}.md"
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / output_name
    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Summary\n\n")
        f.write(summary)
        f.write("\n")
    _append_processed(path.name)
    print(f"Fertig: {output_path}")


def main() -> None:
    AUDIO_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    processed = _load_processed()
    for audio_file in AUDIO_DIR.iterdir():
        if not audio_file.is_file():
            continue
        if audio_file.suffix.lower() not in AUDIO_EXTS:
            continue
        if audio_file.name in processed:
            print(f"{audio_file.name} is already processed.")
            continue
        _process_file(audio_file)


if __name__ == "__main__":
    main()
