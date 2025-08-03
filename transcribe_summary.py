import argparse
import configparser
import math
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"

CONFIG_FILE = "config.cfg"
PROMPT_FILE = "summary_prompt.txt"
WHISPER_MODEL_CONFIG = "whisper_config.txt"
MAX_CHUNK_BYTES = 25 * 1024 * 1024


def _load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def load_config(path: Path = BASE_DIR / CONFIG_FILE) -> configparser.ConfigParser:
    """Load configuration from an INI file."""
    config = configparser.ConfigParser()
    with open(path, "r", encoding="utf-8") as f:
        config.read_file(f)
    return config


def load_whisper_model(config_path: Path = BASE_DIR / WHISPER_MODEL_CONFIG) -> str:
    """Return the first uncommented model name from the config file."""
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                return line
    raise ValueError("No Whisper model selected in config file")


def markdown_to_pdf(markdown_text: str, pdf_path: str) -> None:
    """Convert Markdown text to a PDF file with bookmarks."""
    styles = getSampleStyleSheet()
    heading1 = ParagraphStyle("Heading1", parent=styles["Heading1"])
    heading1.outlineLevel = 0
    heading2 = ParagraphStyle("Heading2", parent=styles["Heading2"])
    heading2.outlineLevel = 1
    body = styles["BodyText"]

    flowables = []
    list_items = []
    in_list = False

    lines = markdown_text.splitlines()
    for line in lines:
        line = line.rstrip()
        if line.startswith("```"):
            continue
        if not line:
            if in_list:
                flowables.append(ListFlowable(list_items, bulletType="bullet"))
                list_items = []
                in_list = False
            flowables.append(Spacer(1, 0.2 * inch))
            continue
        if line.startswith("### "):
            if in_list:
                flowables.append(ListFlowable(list_items, bulletType="bullet"))
                list_items = []
                in_list = False
            heading = Paragraph(line[4:], heading2)
            flowables.append(heading)
        elif line.startswith("## "):
            if in_list:
                flowables.append(ListFlowable(list_items, bulletType="bullet"))
                list_items = []
                in_list = False
            heading = Paragraph(line[3:], heading2)
            flowables.append(heading)
        elif line.startswith("# "):
            if in_list:
                flowables.append(ListFlowable(list_items, bulletType="bullet"))
                list_items = []
                in_list = False
            heading = Paragraph(line[2:], heading1)
            flowables.append(heading)
        elif line.startswith("- "):
            in_list = True
            list_items.append(ListItem(Paragraph(line[2:], body)))
        else:
            if in_list:
                flowables.append(ListFlowable(list_items, bulletType="bullet"))
                list_items = []
                in_list = False
            flowables.append(Paragraph(line, body))

    if in_list:
        flowables.append(ListFlowable(list_items, bulletType="bullet"))

    doc = SimpleDocTemplate(pdf_path, pagesize=LETTER)
    doc.build(flowables)


def strip_code_fences(text: str) -> str:
    """Remove surrounding Markdown code fences from text."""
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop opening fence
        lines = lines[1:]
        # Drop closing fence if present
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text
def transcribe(audio_path: str, model_name: str, method: str, api_key: Optional[str] = None) -> str:
    """Transcribe an audio file either locally or via the OpenAI API.

    If the audio file is larger than 25 MB and the API is used it is split into
    multiple segments using pydub before transcription. Language is detected
    automatically by the API.
    """

    if method == "api":
        if api_key is None:
            raise ValueError("API key required for API transcription")
        from openai import OpenAI
        from pydub import AudioSegment

        TEMP_DIR.mkdir(exist_ok=True)
        client = OpenAI(api_key=api_key)
        try:
            if os.path.getsize(audio_path) <= MAX_CHUNK_BYTES:
                print("Transcribing whole file via API...")
                with open(audio_path, "rb") as f:
                    result = client.audio.transcriptions.create(
                        model=model_name, file=f
                    )
                return result.text.strip()

            audio_format = Path(audio_path).suffix.lstrip(".").lower()
            export_format = {"m4a": "mp4", "aac": "adts"}.get(audio_format, audio_format)

            audio = AudioSegment.from_file(audio_path)
            num_chunks = math.ceil(os.path.getsize(audio_path) / MAX_CHUNK_BYTES)
            chunk_length_ms = len(audio) // num_chunks
            print(f"Transcribing audio in {num_chunks} chunks via API...")

            texts = []
            for i in range(num_chunks):
                start_ms = i * chunk_length_ms
                end_ms = min((i + 1) * chunk_length_ms, len(audio))
                chunk = audio[start_ms:end_ms]
                with tempfile.NamedTemporaryFile(
                    suffix=f".{audio_format}", dir=TEMP_DIR, delete=False
                ) as tmp:
                    tmp_path = tmp.name
                print(f"Transcribing chunk {i + 1}/{num_chunks} via API...")
                chunk.export(tmp_path, format=export_format)
                with open(tmp_path, "rb") as f:
                    result = client.audio.transcriptions.create(
                        model=model_name, file=f
                    )
                texts.append(result.text.strip())
                os.remove(tmp_path)
                print(f"Finished chunk {i + 1}/{num_chunks}")

            return " ".join(texts)
        finally:
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
    else:
        import whisper

        model = whisper.load_model(model_name)
        result = model.transcribe(audio_path)
        return result["text"].strip()


def summarize(
    prompt: str, transcript: str, model_name: str, api_key: str, language: str
) -> str:
    """Generate a summary of the transcript using a chat model."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    lang_text = "English" if language == "en" else "German"
    messages = [
        {
            "role": "system",
            "content": f"You are a helpful assistant that writes in {lang_text}.",
        },
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
        "--summary-model",
        help="Model to use for summarization (overrides config file)",
    )
    parser.add_argument(
        "--method",
        choices=["api", "local"],
        default=None,
        help="Transcription backend: 'api' for OpenAI API or 'local' for running Whisper locally",
    )
    parser.add_argument(
        "--language",
        choices=["en", "de"],
        default=None,
        help="Language for the generated summary (en or de)",
    )
    parser.add_argument(
        "--method",
        choices=["api", "local"],
        default="api",
        help="Transcription backend: 'api' for OpenAI API or 'local' for running Whisper locally",
    )
    parser.add_argument(
        "--language",
        choices=["en", "de"],
        default="en",
        help="Language for the generated summary (en or de)",
    )

    args = parser.parse_args()

    config = load_config()
    prompt = _load_text(args.prompt_file)
    whisper_model = config["whisper"]["model"]
    api_key = config["openai"]["api_key"]
    method = args.method or config["general"].get("method", "api")
    language = args.language or config["general"].get("language", "en")
    summary_model = args.summary_model or config["openai"]["summary_model"]
    print(
        f"Using model {whisper_model} via {'API' if method == 'api' else 'local'}"
    )
    print("Transcribing audio...")
    transcript = transcribe(
        args.audio,
        model_name=whisper_model,
        method=method,
        api_key=api_key if method == "api" else None,
    )
    print("Transcription complete.")

    print("Summarizing transcript...")
    summary = summarize(prompt, transcript, summary_model, api_key, language)
    summary = strip_code_fences(summary)
    print("Summary complete.")

    heading = "Summary" if language == "en" else "Zusammenfassung"
    markdown_content = f"# {heading}\n\n" + summary + "\n"
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    pdf_path = Path(args.output).with_suffix(".pdf")
    markdown_to_pdf(markdown_content, str(pdf_path))

    print(f"Summary written to {args.output}")
    print(f"PDF written to {pdf_path}")

if __name__ == "__main__":
    main()
