# gpt_transcribe

Transcribe audio files with Whisper and summarize the result using a chat model.

## Requirements
- Python 3.8+
- [openai-whisper](https://github.com/openai/whisper)
- [openai](https://pypi.org/project/openai/)
- [pydub](https://github.com/jiaaro/pydub) and [ffmpeg](https://ffmpeg.org/)

## Usage
1. Create `openai_api_key.txt` containing your OpenAI API key (this file is ignored by git).
2. Optionally create `openai_model.txt` specifying the chat model (e.g., `gpt-3.5-turbo`).
3. Create `summary_prompt.txt` containing the prompt for the summary.
4. Run the script:

```bash
python transcribe_summary.py path/to/audio.mp3 output.md
```

Optionally select different models or prompt:

```bash
python transcribe_summary.py audio.m4a summary.md \
  --whisper-model base --summary-model gpt-3.5-turbo \
  --prompt-file other_prompt.txt
```

Large MP3 or m4a files over 25 MB are automatically split into smaller chunks before transcription.

The summary will be written to the specified Markdown file.

