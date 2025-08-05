#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from pathlib import Path
import threading

import transcribe_summary

BASE_DIR = transcribe_summary.BASE_DIR
CONFIG_PATH = BASE_DIR / transcribe_summary.CONFIG_FILE
PROMPT_PATH = BASE_DIR / transcribe_summary.PROMPT_FILE
CONFIG_TEMPLATE_PATH = (
    transcribe_summary.RESOURCE_DIR / transcribe_summary.CONFIG_TEMPLATE
)
README_PATH = transcribe_summary.RESOURCE_DIR / "README.md"

AUDIO_EXTS = [
    ("Audio Files", "*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.wma"),
    ("All Files", "*.*"),
]

SUMMARY_MODELS = ["gpt-4o-mini", "gpt-4o"]


def load_whisper_models(
    config_path: Path = CONFIG_PATH, template_path: Path = CONFIG_TEMPLATE_PATH
):
    def parse(path: Path):
        api, local = [], []
        current = None
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("[") and stripped.endswith("]"):
                    section = stripped.strip("[]")
                    if section == "whisper_api":
                        current = "api"
                    elif section == "whisper_local":
                        current = "local"
                    else:
                        current = None
                    continue
                stripped = stripped.lstrip("#").strip()
                if stripped.startswith("model") and "=" in stripped and current:
                    model = stripped.split("=", 1)[1].strip()
                    if current == "api":
                        api.append(model)
                    else:
                        local.append(model)
        return api, local

    api_models, local_models = set(), set()
    for p in (template_path, config_path):
        if p.exists():
            api, local = parse(p)
            api_models.update(api)
            local_models.update(local)
    return sorted(api_models), sorted(local_models)


class TranscribeGUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title("gpt_transcribe")
        master.minsize(500, 250)
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        ttk.Style().theme_use("clam")

        self.config = transcribe_summary.load_config(CONFIG_PATH)
        transcribe_summary.ensure_prompt(PROMPT_PATH)

        self.audio_files: list[str] = []
        self.output_dir_var = tk.StringVar()
        self.status_var = tk.StringVar()

        self.create_menu()
        self.create_main_widgets()

    def create_menu(self) -> None:
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        app_menu = tk.Menu(menubar, tearoff=0)
        app_menu.add_command(label="Settings", command=self.open_settings)
        app_menu.add_command(label="Documentation", command=self.show_docs)
        app_menu.add_separator()
        app_menu.add_command(label="Quit", command=self.master.quit)
        menubar.add_cascade(label="Menu", menu=app_menu)

    def create_main_widgets(self) -> None:
        frame = ttk.Frame(self.master, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Audio Files").grid(
            row=0, column=0, sticky="ne", padx=5, pady=2
        )
        self.audio_list = tk.Listbox(frame, width=40, height=5)
        self.audio_list.grid(row=0, column=1, padx=5, pady=2, sticky="we")
        ttk.Button(frame, text="Browse", command=self.select_audio).grid(
            row=0, column=2, padx=5, pady=2, sticky="nw"
        )

        ttk.Label(frame, text="Output Directory").grid(
            row=1, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(frame, textvariable=self.output_dir_var, width=30).grid(
            row=1, column=1, sticky="we", pady=2
        )
        ttk.Button(frame, text="Browse", command=self.select_output_dir).grid(
            row=1, column=2, padx=5, pady=2
        )

        ttk.Label(frame, text="Method").grid(
            row=2, column=0, sticky="e", padx=5, pady=2
        )
        self.method_var = tk.StringVar(
            value=self.config["general"].get("method", "api")
        )
        ttk.Combobox(
            frame,
            textvariable=self.method_var,
            values=["api", "local"],
            state="readonly",
        ).grid(row=2, column=1, sticky="we", pady=2)

        self.progress = ttk.Progressbar(
            frame, length=200, mode="determinate"
        )
        self.progress.grid(row=3, column=0, columnspan=3, sticky="we", padx=5, pady=10)

        ttk.Button(frame, text="Transcribe", command=self.start_transcription).grid(
            row=4, column=1, pady=5, sticky="e"
        )
        ttk.Label(frame, textvariable=self.status_var).grid(
            row=4, column=2, sticky="w"
        )

    def set_status(self, text: str) -> None:
        self.master.after(0, self.status_var.set, text)

    def step_progress(self) -> None:
        self.master.after(0, self.progress.step)

    def show_info(self, title: str, msg: str) -> None:
        self.master.after(0, lambda: messagebox.showinfo(title, msg))

    def show_error(self, title: str, msg: str) -> None:
        self.master.after(0, lambda: messagebox.showerror(title, msg))

    def select_audio(self) -> None:
        paths = filedialog.askopenfilenames(filetypes=AUDIO_EXTS)
        if paths:
            self.audio_files = list(paths)
            self.audio_list.delete(0, tk.END)
            for p in self.audio_files:
                self.audio_list.insert(tk.END, Path(p).name)

    def select_output_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_dir_var.set(path)

    def start_transcription(self) -> None:
        if not self.audio_files:
            messagebox.showwarning("No files", "Please select one or more audio files.")
            return
        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showwarning("No output", "Please select an output directory.")
            return
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.audio_files) * 3
        threading.Thread(
            target=self.transcribe_all, args=(output_dir,), daemon=True
        ).start()

    def transcribe_all(self, output_dir: str) -> None:
        self.set_status("Working...")
        try:
            method = self.method_var.get()
            language = self.config["general"].get("language", "en")
            api_key = self.config["openai"]["api_key"]
            summary_model = self.config["openai"]["summary_model"]
            whisper_section = "whisper_api" if method == "api" else "whisper_local"
            whisper_model = self.config[whisper_section]["model"]
            prompt = transcribe_summary._load_text(PROMPT_PATH)

            for idx, audio in enumerate(self.audio_files, 1):
                self.set_status(f"Transcribing {idx}/{len(self.audio_files)}")

                def update(msg: str, i=idx):
                    self.set_status(f"{msg} ({i}/{len(self.audio_files)})")

                transcript = transcribe_summary.transcribe(
                    audio,
                    model_name=whisper_model,
                    method=method,
                    api_key=api_key if method == "api" else None,
                    progress_cb=update,
                )
                self.step_progress()
                self.set_status("Summarizing...")
                summary = transcribe_summary.summarize(
                    prompt, transcript, summary_model, api_key, language
                )
                summary = transcribe_summary.strip_code_fences(summary)
                self.step_progress()
                self.set_status("Writing output...")
                heading = "Summary" if language == "en" else "Zusammenfassung"
                markdown_content = f"# {heading}\n\n{summary}\n"
                out_md = Path(output_dir) / (Path(audio).stem + ".md")
                with open(out_md, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                pdf_path = out_md.with_suffix(".pdf")
                transcribe_summary.markdown_to_pdf(markdown_content, str(pdf_path))
                self.step_progress()

            self.set_status("Done")
            self.show_info("Finished", f"Summaries written to {output_dir}")
        except Exception as e:
            self.set_status("Error")
            self.show_error("Error", str(e))

    def open_settings(self) -> None:
        SettingsWindow(self)

    def show_docs(self) -> None:
        doc_win = tk.Toplevel(self.master)
        doc_win.title("Documentation")
        text = scrolledtext.ScrolledText(doc_win, width=80, height=30)
        text.pack(fill="both", expand=True)
        try:
            content = transcribe_summary._load_text(README_PATH)
        except Exception as e:
            content = str(e)
        text.insert("1.0", content)
        text.configure(state="disabled")


class SettingsWindow(tk.Toplevel):
    def __init__(self, app: TranscribeGUI) -> None:
        super().__init__(app.master)
        self.app = app
        self.title("Settings")
        self.minsize(600, 400)
        self.resizable(True, True)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.config = transcribe_summary.load_config(CONFIG_PATH)
        prompt_text = transcribe_summary._load_text(PROMPT_PATH)
        api_models, local_models = load_whisper_models()

        ttk.Label(self, text="API Key").grid(
            row=0, column=0, sticky="e", padx=5, pady=2
        )
        self.api_key_var = tk.StringVar(
            value=self.config["openai"].get("api_key", "")
        )
        ttk.Entry(self, textvariable=self.api_key_var, width=60).grid(
            row=0, column=1, columnspan=2, sticky="we", pady=2
        )

        ttk.Label(self, text="Summary Model").grid(
            row=1, column=0, sticky="e", padx=5, pady=2
        )
        self.summary_model_var = tk.StringVar(
            value=self.config["openai"].get("summary_model", "")
        )
        self.summary_model_cb = ttk.Combobox(
            self,
            textvariable=self.summary_model_var,
            values=SUMMARY_MODELS,
            state="readonly",
        )
        self.summary_model_cb.grid(row=1, column=1, columnspan=2, sticky="we", pady=2)

        ttk.Label(self, text="Whisper API Model").grid(
            row=2, column=0, sticky="e", padx=5, pady=2
        )
        self.api_model_var = tk.StringVar(
            value=self.config["whisper_api"].get("model", "")
        )
        self.api_model_cb = ttk.Combobox(
            self,
            textvariable=self.api_model_var,
            values=api_models,
            state="readonly",
        )
        self.api_model_cb.grid(row=2, column=1, columnspan=2, sticky="we", pady=2)

        ttk.Label(self, text="Whisper Local Model").grid(
            row=3, column=0, sticky="e", padx=5, pady=2
        )
        self.local_model_var = tk.StringVar(
            value=self.config["whisper_local"].get("model", "")
        )
        self.local_model_cb = ttk.Combobox(
            self,
            textvariable=self.local_model_var,
            values=local_models,
            state="readonly",
        )
        self.local_model_cb.grid(row=3, column=1, columnspan=2, sticky="we", pady=2)

        ttk.Label(self, text="Summary Prompt").grid(
            row=4, column=0, sticky="ne", padx=5, pady=2
        )
        self.prompt_box = scrolledtext.ScrolledText(self, height=10, width=60)
        self.prompt_box.grid(
            row=4, column=1, columnspan=2, sticky="nsew", padx=5, pady=2
        )
        self.prompt_box.insert("1.0", prompt_text)

        ttk.Button(self, text="Save", command=self.save_settings).grid(
            row=5, column=2, sticky="e", pady=5
        )

    def save_settings(self) -> None:
        self.config["openai"]["api_key"] = self.api_key_var.get().strip()
        self.config["openai"]["summary_model"] = (
            self.summary_model_var.get().strip()
        )
        self.config["whisper_api"]["model"] = self.api_model_var.get().strip()
        self.config["whisper_local"]["model"] = self.local_model_var.get().strip()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            self.config.write(f)
        with open(PROMPT_PATH, "w", encoding="utf-8") as f:
            f.write(self.prompt_box.get("1.0", "end").strip())
        self.app.config = self.config
        messagebox.showinfo("Saved", "Configuration updated.")
        self.destroy()


def main() -> None:
    root = tk.Tk()
    if not transcribe_summary.check_ffmpeg():
        messagebox.showwarning(
            "ffmpeg missing",
            "ffmpeg is not installed or not found in PATH.",
        )
    TranscribeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

