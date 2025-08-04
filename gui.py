import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
import transcribe_summary

BASE_DIR = transcribe_summary.BASE_DIR
CONFIG_PATH = BASE_DIR / transcribe_summary.CONFIG_FILE
PROMPT_PATH = BASE_DIR / transcribe_summary.PROMPT_FILE

AUDIO_EXTS = [
    ("Audio Files", "*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.wma"),
    ("All Files", "*.*"),
]


class TranscribeGUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title("gpt_transcribe")
        master.resizable(False, False)

        try:
            self.config = transcribe_summary.load_config(CONFIG_PATH)
        except FileNotFoundError as e:
            messagebox.showerror("Configuration", str(e))
            master.destroy()
            return
        transcribe_summary.ensure_prompt(PROMPT_PATH)
        prompt_text = transcribe_summary._load_text(PROMPT_PATH)

        # Configuration fields
        tk.Label(master, text="API Key").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.api_key_var = tk.StringVar(value=self.config["openai"].get("api_key", ""))
        tk.Entry(master, textvariable=self.api_key_var, width=40).grid(row=0, column=1, columnspan=2, sticky="we", pady=2)

        tk.Label(master, text="Summary Model").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.summary_model_var = tk.StringVar(value=self.config["openai"].get("summary_model", ""))
        tk.Entry(master, textvariable=self.summary_model_var).grid(row=1, column=1, columnspan=2, sticky="we", pady=2)

        tk.Label(master, text="Whisper API Model").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.api_model_var = tk.StringVar(value=self.config["whisper_api"].get("model", ""))
        tk.Entry(master, textvariable=self.api_model_var).grid(row=2, column=1, columnspan=2, sticky="we", pady=2)

        tk.Label(master, text="Whisper Local Model").grid(row=3, column=0, sticky="e", padx=5, pady=2)
        self.local_model_var = tk.StringVar(value=self.config["whisper_local"].get("model", ""))
        tk.Entry(master, textvariable=self.local_model_var).grid(row=3, column=1, columnspan=2, sticky="we", pady=2)

        tk.Label(master, text="Summary Prompt").grid(row=4, column=0, sticky="ne", padx=5, pady=2)
        self.prompt_box = tk.Text(master, height=5, width=40)
        self.prompt_box.grid(row=4, column=1, columnspan=2, sticky="we", pady=2)
        self.prompt_box.insert("1.0", prompt_text)

        tk.Button(master, text="Save Config", command=self.save_config).grid(row=5, column=2, sticky="e", pady=5)

        # Audio selection
        tk.Label(master, text="Audio File").grid(row=6, column=0, sticky="e", padx=5, pady=2)
        self.audio_path_var = tk.StringVar()
        tk.Entry(master, textvariable=self.audio_path_var, width=30).grid(row=6, column=1, sticky="we", pady=2)
        tk.Button(master, text="Browse", command=self.select_audio).grid(row=6, column=2, pady=2)

        tk.Button(master, text="Transcribe", command=self.start_transcription).grid(row=7, column=1, pady=5)
        self.status_var = tk.StringVar()
        tk.Label(master, textvariable=self.status_var).grid(row=7, column=2, sticky="w")

    def save_config(self) -> None:
        self.config["openai"]["api_key"] = self.api_key_var.get().strip()
        self.config["openai"]["summary_model"] = self.summary_model_var.get().strip()
        self.config["whisper_api"]["model"] = self.api_model_var.get().strip()
        self.config["whisper_local"]["model"] = self.local_model_var.get().strip()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            self.config.write(f)
        with open(PROMPT_PATH, "w", encoding="utf-8") as f:
            f.write(self.prompt_box.get("1.0", "end").strip())
        messagebox.showinfo("Saved", "Configuration updated.")

    def select_audio(self) -> None:
        path = filedialog.askopenfilename(filetypes=AUDIO_EXTS)
        if path:
            self.audio_path_var.set(path)

    def start_transcription(self) -> None:
        audio = self.audio_path_var.get()
        if not audio:
            messagebox.showwarning("No file", "Please select an audio file.")
            return
        output = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")])
        if not output:
            return
        threading.Thread(target=self.transcribe, args=(audio, output), daemon=True).start()

    def transcribe(self, audio: str, output: str) -> None:
        self.status_var.set("Working...")
        try:
            cfg = transcribe_summary.load_config(CONFIG_PATH)
            method = cfg["general"].get("method", "api")
            language = cfg["general"].get("language", "en")
            api_key = cfg["openai"]["api_key"]
            summary_model = cfg["openai"]["summary_model"]
            whisper_section = "whisper_api" if method == "api" else "whisper_local"
            whisper_model = cfg[whisper_section]["model"]
            prompt = transcribe_summary._load_text(PROMPT_PATH)

            transcript = transcribe_summary.transcribe(
                audio,
                model_name=whisper_model,
                method=method,
                api_key=api_key if method == "api" else None,
            )
            summary = transcribe_summary.summarize(prompt, transcript, summary_model, api_key, language)
            summary = transcribe_summary.strip_code_fences(summary)
            heading = "Summary" if language == "en" else "Zusammenfassung"
            markdown_content = f"# {heading}\n\n{summary}\n"
            with open(output, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            pdf_path = Path(output).with_suffix(".pdf")
            transcribe_summary.markdown_to_pdf(markdown_content, str(pdf_path))
            self.status_var.set("Done")
            messagebox.showinfo("Finished", f"Summary written to {output}\nPDF written to {pdf_path}")
        except Exception as e:
            self.status_var.set("Error")
            messagebox.showerror("Error", str(e))


def main() -> None:
    root = tk.Tk()
    TranscribeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
