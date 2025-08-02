# gpt_transcribe

Transcribe audio files with Whisper and summarize the result using a chat model.

## Requirements
- Python 3.8+
- [openai-whisper](https://github.com/openai/whisper)
- [openai](https://pypi.org/project/openai/)

## Usage
1. Create `openai_api_key.txt` containing your OpenAI API key (this file is ignored by git).
2. Create `openai_model.txt` specifying the chat model (e.g., `gpt-3.5-turbo`).
3. Prepare a text file containing the prompt for the summary.
4. Run the script:

```bash
python transcribe_summary.py path/to/audio.wav prompt.txt output.md
```

Optionally select a different Whisper model:

```bash
python transcribe_summary.py audio.wav prompt.txt summary.md \
  --whisper-model base
```

The summary will be written to the specified Markdown file.
