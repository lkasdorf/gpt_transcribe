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
3. Edit `whisper_config.txt` and uncomment the Whisper model you want to use. The file lists
   available API models (e.g., `whisper-1`) and local models (e.g., `base`, `small`).
4. Create `summary_prompt.txt` containing the prompt for the summary.
5. Run the script:

```bash
# Windows
python transcribe_summary.py path\to\audio.mp3 output.md --method api --language en

# Linux/macOS
python3 transcribe_summary.py path/to/audio.mp3 output.md --method api --language en
```

To run Whisper locally or change the output language:

```bash
# Local transcription with German summary
python3 transcribe_summary.py audio.m4a summary.md --method local --language de

# Custom prompt and summary model
python3 transcribe_summary.py audio.m4a summary.md \
  --summary-model gpt-3.5-turbo \
  --prompt-file other_prompt.txt
```

Large MP3 or m4a files over 25 MB are automatically split into smaller chunks before
API transcription.

When executed the script prints which model is used and whether transcription happens
locally or via the API. The summary will be written to the specified Markdown file and an accompanying
PDF file with bookmarks.

## Batch transcription

To process many audio files automatically, place them in the `audio` directory
and run:

```bash
python batch_transcribe.py --method api --language en
```

Summaries will be written to the `output` directory with filenames in the
form `YYYYMMDD_NameOfTheFile.md` and a matching `.pdf` file. Successfully
processed audio files are tracked in `processed.log` along with file size,
duration, transcription method, transcription time and timestamp to avoid
duplicate work.
