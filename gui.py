#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from pathlib import Path
from datetime import datetime
import threading

import os
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

SUMMARY_MODELS = [
    # Curated list of commonly available chat models; GUI allows free text too
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1",
    "gpt-4.1-mini",
    # Also include GPT-5 options if user has access
    "gpt-5-mini",
    "gpt-5",
    "gpt-5-pro",
]


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

def apply_dark_theme(style: ttk.Style) -> None:
    """Apply a professional dark theme inspired by modern editors (Cursor/VS Code)."""
    # Palette
    BG = '#1e1e1e'
    SURFACE = '#252526'
    BORDER = '#333333'
    TEXT = '#d4d4d4'
    MUTED = '#9aa0a6'
    ENTRY_BG = '#2a2a2a'
    ACCENT = '#3b82f6'
    POSITIVE = '#10b981'
    DANGER = '#ef4444'
    SELECTION = '#094771'

    # Base theme
    style.theme_use('clam')

    # Frames and labels
    style.configure('TFrame', background=BG)
    style.configure('Card.TFrame', background=SURFACE, borderwidth=1, relief='solid')
    style.configure('TLabel', background=SURFACE, foreground=TEXT, font=('Segoe UI', 10))
    style.configure('Title.TLabel', background=SURFACE, foreground=TEXT, font=('Segoe UI', 18, 'bold'))
    style.configure('Header.TLabel', background=SURFACE, foreground=TEXT, font=('Segoe UI', 11, 'bold'))
    style.configure('Info.TLabel', background=SURFACE, foreground=MUTED, font=('Segoe UI', 9))
    style.configure('Success.TLabel', background=SURFACE, foreground=POSITIVE, font=('Segoe UI', 9))
    style.configure('Error.TLabel', background=SURFACE, foreground=DANGER, font=('Segoe UI', 9))

    # LabelFrames
    style.configure('Card.TLabelframe', background=SURFACE, foreground=TEXT, bordercolor=BORDER, relief='solid', borderwidth=1)
    style.configure('Card.TLabelframe.Label', background=SURFACE, foreground=TEXT, font=('Segoe UI', 10, 'bold'))

    # Entry and combobox
    style.configure('TEntry', fieldbackground=ENTRY_BG, background=SURFACE, foreground=TEXT, bordercolor=BORDER)
    style.configure('TCombobox', fieldbackground=ENTRY_BG, background=ENTRY_BG, foreground=TEXT, arrowcolor=TEXT, bordercolor=BORDER)

    # Buttons
    style.configure('TButton', background=SURFACE, foreground=TEXT, borderwidth=1, focusthickness=0, padding=(12, 6))
    style.map('TButton', background=[('active', '#2f2f2f')])
    style.configure('Primary.TButton', background=ACCENT, foreground='white', borderwidth=0, padding=(14, 8), font=('Segoe UI', 10, 'bold'))
    style.map('Primary.TButton', background=[('active', '#2563eb')])
    style.configure('Accent.TButton', background=ACCENT, foreground='white', borderwidth=0, padding=(12, 6))
    style.map('Accent.TButton', background=[('active', '#2563eb')])
    style.configure('Positive.TButton', background=POSITIVE, foreground='white', borderwidth=0, padding=(12, 6))
    style.map('Positive.TButton', background=[('active', '#059669')])
    style.configure('Danger.TButton', background=DANGER, foreground='white', borderwidth=0, padding=(12, 6))
    style.map('Danger.TButton', background=[('active', '#dc2626')])

    # Progressbar
    style.configure('Modern.Horizontal.TProgressbar', background=ACCENT, troughcolor=BG, bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT)

    # Scrollbar
    style.configure('Vertical.TScrollbar', background=SURFACE, troughcolor=BG, bordercolor=BORDER, arrowcolor=TEXT)

    # Return palette (used by widget configs that are not ttk-styleable)
    style._cursor_palette = {
        'BG': BG, 'SURFACE': SURFACE, 'BORDER': BORDER, 'TEXT': TEXT, 'MUTED': MUTED,
        'ENTRY_BG': ENTRY_BG, 'ACCENT': ACCENT, 'POSITIVE': POSITIVE, 'DANGER': DANGER, 'SELECTION': SELECTION,
    }


class TranscribeGUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title("GPT Transcribe")
        master.minsize(760, 560)
        
        # Configure grid weights
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        
        # Apply dark theme
        style = ttk.Style()
        apply_dark_theme(style)
        palette = style._cursor_palette
        master.configure(bg=palette['BG'])

        self.config = transcribe_summary.load_config(CONFIG_PATH)
        transcribe_summary.ensure_prompt(PROMPT_PATH)

        self.audio_files: list[str] = []
        self.output_dir_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready to transcribe")

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
        # Main container with padding
        main_frame = ttk.Frame(self.master, style='Card.TFrame', padding=20)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="GPT Transcribe", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")

        # Audio Files Section
        audio_frame = ttk.LabelFrame(main_frame, text="Audio Files", padding=15, style='Card.TLabelframe')
        audio_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        audio_frame.columnconfigure(1, weight=1)

        ttk.Label(audio_frame, text="Selected Files:", style='Header.TLabel').grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        
        # Create a frame for the listbox and scrollbar
        list_frame = ttk.Frame(audio_frame)
        list_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        
        self.audio_list = tk.Listbox(
            list_frame, 
            height=6, 
            font=('Segoe UI', 9),
            selectmode='extended',
            relief='flat',
            bd=0,
            bg=palette['ENTRY_BG'],
            fg=palette['TEXT'],
            highlightthickness=1,
            highlightcolor=palette['BORDER'],
            highlightbackground=palette['BORDER'],
            selectbackground=palette['SELECTION'],
            selectforeground=palette['TEXT']
        )
        self.audio_list.grid(row=0, column=0, sticky="ew")
        
        # Add scrollbar to listbox
        audio_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.audio_list.yview, style='Vertical.TScrollbar')
        audio_scrollbar.grid(row=0, column=1, sticky="ns")
        self.audio_list.configure(yscrollcommand=audio_scrollbar.set)
        
        # Buttons frame
        button_frame = ttk.Frame(audio_frame, style='TFrame')
        button_frame.grid(row=2, column=0, columnspan=2, sticky="w")
        
        ttk.Button(
            button_frame,
            text="📁 Add Audio Files",
            style='Accent.TButton',
            command=self.select_audio,
            cursor='hand2',
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="🗑️ Clear All",
            style='Danger.TButton',
            command=self.clear_audio_files,
            cursor='hand2',
        ).pack(side="left")

        # Output Directory Section
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding=15, style='Card.TLabelframe')
        output_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Output Directory:", style='Header.TLabel').grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        
        output_entry_frame = ttk.Frame(output_frame, style='TFrame')
        output_entry_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        output_entry_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(
            output_entry_frame, 
            textvariable=self.output_dir_var, 
            font=('Segoe UI', 9)
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        ttk.Button(
            output_entry_frame,
            text="📂 Browse",
            style='Positive.TButton',
            command=self.select_output_dir,
            cursor='hand2',
        ).grid(row=0, column=1)

        # Transcription Settings Section
        settings_frame = ttk.LabelFrame(main_frame, text="Transcription Settings", padding=15, style='Card.TLabelframe')
        settings_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        settings_frame.columnconfigure(1, weight=1)

        ttk.Label(settings_frame, text="Method:", style='Header.TLabel').grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.method_var = tk.StringVar(
            value=self.config["general"].get("method", "api")
        )
        method_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.method_var,
            values=["api", "local"],
            state="readonly",
            font=('Segoe UI', 9)
        )
        method_combo.grid(row=1, column=0, sticky="w")

        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=15, style='Card.TLabelframe')
        progress_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        progress_frame.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(
            progress_frame, 
            style='Modern.Horizontal.TProgressbar',
            mode="determinate"
        )
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Status and action buttons
        action_frame = ttk.Frame(main_frame, style='TFrame')
        action_frame.grid(row=5, column=0, columnspan=3, sticky="ew")
        action_frame.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(
            action_frame, 
            textvariable=self.status_var, 
            style='Info.TLabel'
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        ttk.Button(
            action_frame,
            text="🎤 Start Transcription",
            style='Primary.TButton',
            command=self.start_transcription,
            cursor='hand2',
        ).grid(row=0, column=1, sticky="e")

    def clear_audio_files(self):
        """Clear all selected audio files"""
        self.audio_files.clear()
        self.audio_list.delete(0, tk.END)
        self.set_status("Ready to transcribe")

    def set_status(self, text: str) -> None:
        self.master.after(0, self.status_var.set, text)

    def step_progress(self) -> None:
        self.master.after(0, self.progress.step)

    def show_info(self, title: str, msg: str) -> None:
        self.master.after(0, lambda: messagebox.showinfo(title, msg))

    def show_error(self, title: str, msg: str) -> None:
        self.master.after(0, lambda: messagebox.showerror(title, msg))

    def select_audio(self) -> None:
        raw_paths = filedialog.askopenfilenames(filetypes=AUDIO_EXTS)
        if raw_paths:
            if isinstance(raw_paths, str):
                paths = self.master.tk.splitlist(raw_paths)
            else:
                paths = raw_paths
            self.audio_files = [str(Path(p).resolve()) for p in paths]
            self.audio_list.delete(0, tk.END)
            for p in self.audio_files:
                self.audio_list.insert(tk.END, Path(p).name)
            
            # Update status
            count = len(self.audio_files)
            self.set_status(f"Ready to transcribe {count} file{'s' if count != 1 else ''}")

    def select_output_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_dir_var.set(str(Path(path).resolve()))

    def start_transcription(self) -> None:
        if not self.audio_files:
            messagebox.showwarning("No files", "Please select one or more audio files.")
            return
        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showwarning("No output", "Please select an output directory.")
            return
        missing = [p for p in self.audio_files if not Path(p).is_file()]
        if missing:
            messagebox.showerror("Missing file", f"Audio file not found: {missing[0]}")
            return
        if not Path(output_dir).is_dir():
            messagebox.showerror(
                "Missing output", f"Output directory not found: {output_dir}"
            )
            return
        self.progress["value"] = 0
        # For grouped transcription we have ~1 step per file (transcribe), then summarize, then write
        self.progress["maximum"] = (len(self.audio_files) + 2) if len(self.audio_files) > 1 else (len(self.audio_files) * 3)
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

            if len(self.audio_files) > 1:
                # Group mode: transcribe all files and summarize once
                combined_transcript_parts: list[str] = []
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
                    combined_transcript_parts.append(
                        f"\n\n=== {Path(audio).name} ===\n\n{transcript}\n"
                    )
                    self.step_progress()

                combined_transcript = "".join(combined_transcript_parts).strip()
                self.set_status("Summarizing (all files)...")
                summary = transcribe_summary.summarize(
                    prompt, combined_transcript, summary_model, api_key, language
                )
                summary = transcribe_summary.strip_code_fences(summary)
                self.step_progress()

                # Write single combined output
                self.set_status("Writing output...")
                heading = "Summary" if language == "en" else "Zusammenfassung"
                markdown_content = f"# {heading}\n\n{summary}\n"
                first_stem = Path(self.audio_files[0]).stem
                base = f"{datetime.now():%Y%m%d_%H%M%S}_{first_stem}_and_{len(self.audio_files)-1}_more"
                out_md = Path(output_dir) / f"{base}.md"
                with open(out_md, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                out_txt = Path(output_dir) / f"{base}.txt"
                with open(out_txt, "w", encoding="utf-8") as f:
                    f.write(combined_transcript)
                pdf_path = out_md.with_suffix(".pdf")
                transcribe_summary.markdown_to_pdf(markdown_content, str(pdf_path))
                self.step_progress()
                self.set_status("✅ Transcription completed successfully!")
                self.show_info("Finished", f"Summary written to {out_md}")
            else:
                # Single-file behavior unchanged
                audio = self.audio_files[0]
                self.set_status("Transcribing 1/1")

                def update(msg: str):
                    self.set_status(f"{msg} (1/1)")

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
                out_txt = Path(output_dir) / (Path(audio).stem + ".txt")
                with open(out_txt, "w", encoding="utf-8") as f:
                    f.write(transcript)
                pdf_path = out_md.with_suffix(".pdf")
                transcribe_summary.markdown_to_pdf(markdown_content, str(pdf_path))
                self.step_progress()
                self.set_status("✅ Transcription completed successfully!")
                self.show_info("Finished", f"Summary written to {out_md}")
        except Exception as e:
            self.set_status("❌ Error occurred during transcription")
            self.show_error("Error", str(e))

    def open_settings(self) -> None:
        SettingsWindow(self)

    def show_docs(self) -> None:
        doc_win = tk.Toplevel(self.master)
        doc_win.title("Documentation")
        doc_win.configure(bg=palette['BG'])
        doc_win.minsize(800, 600)
        
        # Create a modern text widget with better styling
        text_frame = ttk.Frame(doc_win, style='Card.TFrame', padding=10)
        text_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        text = scrolledtext.ScrolledText(
            text_frame, 
            width=80, 
            height=30,
            font=('Consolas', 10),
            bg=palette['ENTRY_BG'],
            fg=palette['TEXT'],
            relief='flat',
            bd=0
        )
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
        self.title("Settings - GPT Transcribe")
        self.minsize(700, 500)
        self.configure(bg='#f5f5f5')
        self.resizable(True, True)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.config = transcribe_summary.load_config(CONFIG_PATH)
        prompt_text = transcribe_summary._load_text(PROMPT_PATH)
        api_models, local_models = load_whisper_models()

        # Main container
        main_frame = ttk.Frame(self, style='Card.TFrame', padding=20)
        main_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=20, pady=20)
        main_frame.columnconfigure(1, weight=1)

        # Title
        ttk.Label(main_frame, text="Settings", style='Title.TLabel').grid(
            row=0, column=0, columnspan=3, pady=(0, 20), sticky="w"
        )

        # API Key
        ttk.Label(main_frame, text="API Key:", style='Header.TLabel').grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=5
        )
        # Prefer config key; fall back to OPENAI_API_KEY
        key_from_cfg = self.config["openai"].get("api_key", "").strip()
        if not key_from_cfg or key_from_cfg == "YOUR_API_KEY":
            key_from_cfg = os.getenv("OPENAI_API_KEY", "")
        self.api_key_var = tk.StringVar(value=key_from_cfg)
        ttk.Entry(
            main_frame, 
            textvariable=self.api_key_var, 
            width=60,
            font=('Segoe UI', 9),
            show="*"
        ).grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)

        # Summary Model
        ttk.Label(main_frame, text="Summary Model:", style='Header.TLabel').grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.summary_model_var = tk.StringVar(
            value=self.config["openai"].get("summary_model", "")
        )
        self.summary_model_cb = ttk.Combobox(
            main_frame,
            textvariable=self.summary_model_var,
            values=SUMMARY_MODELS,
            state="normal",  # allow free text for future models
            font=('Segoe UI', 9)
        )
        self.summary_model_cb.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)

        # Whisper API Model
        ttk.Label(main_frame, text="Whisper API Model:", style='Header.TLabel').grid(
            row=3, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.api_model_var = tk.StringVar(
            value=self.config["whisper_api"].get("model", "")
        )
        self.api_model_cb = ttk.Combobox(
            main_frame,
            textvariable=self.api_model_var,
            values=api_models,
            state="readonly",
            font=('Segoe UI', 9)
        )
        self.api_model_cb.grid(row=3, column=1, columnspan=2, sticky="ew", pady=5)

        # Whisper Local Model
        ttk.Label(main_frame, text="Whisper Local Model:", style='Header.TLabel').grid(
            row=4, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.local_model_var = tk.StringVar(
            value=self.config["whisper_local"].get("model", "")
        )
        self.local_model_cb = ttk.Combobox(
            main_frame,
            textvariable=self.local_model_var,
            values=local_models,
            state="readonly",
            font=('Segoe UI', 9)
        )
        self.local_model_cb.grid(row=4, column=1, columnspan=2, sticky="ew", pady=5)

        # Summary Prompt
        ttk.Label(main_frame, text="Summary Prompt:", style='Header.TLabel').grid(
            row=5, column=0, sticky="nw", padx=(0, 10), pady=(20, 5)
        )
        
        prompt_frame = ttk.Frame(main_frame)
        prompt_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=5)
        prompt_frame.columnconfigure(0, weight=1)
        prompt_frame.rowconfigure(0, weight=1)
        
        self.prompt_box = scrolledtext.ScrolledText(
            prompt_frame, 
            height=12, 
            width=60,
            font=('Consolas', 9),
            bg='white',
            fg='#2c3e50',
            relief='solid',
            bd=1
        )
        self.prompt_box.grid(row=0, column=0, sticky="nsew")
        self.prompt_box.insert("1.0", prompt_text)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        button_frame.columnconfigure(1, weight=1)

        ModernButton(
            button_frame, 
            text="💾 Save Settings", 
            command=self.save_settings,
            bg='#27ae60',
            fg='white'
        ).grid(row=0, column=2, sticky="e")

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
        messagebox.showinfo("Saved", "Configuration updated successfully!")
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

