# gpt_transcribe

Transcribe audio files with Whisper and summarize the result using a chat model.
The script runs on both Linux and Windows.

## Installation

1. Install Python 3.8 or newer.
2. Install [ffmpeg](https://ffmpeg.org/).
   - Linux: `sudo apt install ffmpeg`
   - Windows: download a build from the ffmpeg website and add it to your `PATH`.
3. (Optional) Create and activate a virtual environment:
   - Linux/macOS: `python3 -m venv .venv && source .venv/bin/activate`
   - Windows: `python -m venv .venv && .venv\Scripts\activate`
4. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage
1. Create `openai_api_key.txt` containing your OpenAI API key (this file is ignored by git).
2. Optionally create `openai_model.txt` specifying the chat model (e.g., `gpt-3.5-turbo`).
3. Create `summary_prompt.txt` containing the prompt for the summary.
4. Run the script:

```bash
# Windows
python transcribe_summary.py path\to\audio.mp3 output.md

# Linux/macOS
python3 transcribe_summary.py path/to/audio.mp3 output.md
```

Optionally select different models or prompt:

```bash
# Windows (use ^ for line continuation)
python transcribe_summary.py audio.m4a summary.md ^
  --whisper-model base --summary-model gpt-3.5-turbo ^
  --prompt-file other_prompt.txt

# Linux/macOS
python3 transcribe_summary.py audio.m4a summary.md \
  --whisper-model base --summary-model gpt-3.5-turbo \
  --prompt-file other_prompt.txt
```

Large MP3 or m4a files over 25 MB are automatically split into smaller chunks before transcription.

The summary will be written to the specified Markdown file and an accompanying
PDF file with bookmarks.

## Batch transcription

To process many audio files automatically, place them in the `audio` directory
and run:

```bash
python batch_transcribe.py
```

Summaries will be written to the `output` directory with filenames in the
form `YYYYMMDD_NameOfTheFile.md` and a matching `.pdf` file. Successfully

processed audio files are tracked in `processed.log` to avoid duplicate work.