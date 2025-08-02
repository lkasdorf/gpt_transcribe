import argparse
import whisper
from openai import OpenAI



API_KEY_FILE = "openai_api_key.txt"
MODEL_FILE = "openai_model.txt"


def _load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


=======

def transcribe(audio_path: str, model_name: str = "base") -> str:
    """Transcribe an audio file using Whisper."""
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)
    return result["text"].strip()



def summarize(prompt: str, transcript: str, model_name: str, api_key: str) -> str:
    """Generate a summary of the transcript using a chat model."""
    client = OpenAI(api_key=api_key)
=======
def summarize(prompt: str, transcript: str, model_name: str = "gpt-3.5-turbo") -> str:
    """Generate a summary of the transcript using a chat model."""
    client = OpenAI()

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
    parser.add_argument("prompt_file", help="File containing the summary prompt")
    parser.add_argument("output", help="Destination markdown file")
    parser.add_argument(
        "--whisper-model",
        default="base",
        help="Name of the Whisper model to use (default: base)",
    )

=======
    parser.add_argument(
        "--summary-model",
        default="gpt-3.5-turbo",
        help="Model to use for summarization",
    )

    args = parser.parse_args()

    with open(args.prompt_file, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    transcript = transcribe(args.audio, model_name=args.whisper_model)

    api_key = _load_text(API_KEY_FILE)
    summary_model = _load_text(MODEL_FILE)
    summary = summarize(prompt, transcript, summary_model, api_key)
=======
    summary = summarize(prompt, transcript, model_name=args.summary_model)


    with open(args.output, "w", encoding="utf-8") as f:
        f.write("# Summary\n\n")
        f.write(summary)
        f.write("\n")

    print(f"Summary written to {args.output}")


if __name__ == "__main__":
    main()
