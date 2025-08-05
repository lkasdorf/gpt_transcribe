# gpt_transcribe

Transcribe audio files with Whisper and summarize the result using a chat model.
The script runs on Linux, macOS, and Windows.

## Installation

1. Install Python 3.8 or newer.
2. Install [ffmpeg](https://ffmpeg.org/).
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Windows: download a build from the ffmpeg website and add it to your `PATH`.
3. (Optional) Create and activate a virtual environment:
   - Linux/macOS: `python3 -m venv .venv && source .venv/bin/activate`
   - Windows: `python -m venv .venv && .venv\Scripts\activate`
4. Install Python dependencies before running the program. All required packages
   are listed in `requirements.txt` and need to be available on the system –
   they are no longer bundled with the application.

### Linux

```bash
sudo apt update && sudo apt install python3-venv ffmpeg
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### macOS

```bash
brew install python3 ffmpeg
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Windows

```powershell
REM Install Python 3.8+ and make sure pip is available
REM Install ffmpeg and add it to PATH
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

When `openai-whisper` is installed it will pull in the CPU build of PyTorch by
default. If you prefer a GPU-enabled build, install PyTorch separately from
<https://pytorch.org/> before running `pip install -r requirements.txt`.

## Usage
1. On first launch the program creates `config.cfg` and `summary_prompt.txt` from bundled defaults.
   - Edit `config.cfg` to set `api_key`, choose the transcription `method` and summary `language`,
     and pick Whisper models in the `[whisper_api]` and `[whisper_local]` sections.
   - The default summary prompt is stored in `summary_prompt.txt` and can be customized.
   - On Linux these files reside in `~/.config/GTP_Transcribe`.
   `config.cfg` is ignored by git so your API key stays private.
2. Run the script:

```bash
# Windows
python transcribe_summary.py path\to\audio.mp3 output.md --method api --language en

# Linux/macOS
python3 transcribe_summary.py path/to/audio.mp3 output.md --method api --language en
```

Use command-line flags to override the config file:

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

`batch_transcribe.py` reads defaults from `config.cfg`. Use `--method` or `--language`
to override them if needed.

Summaries will be written to the `output` directory with filenames in the
form `YYYYMMDD_NameOfTheFile.md` and a matching `.pdf` file. Successfully
processed audio files are tracked in `processed.log` along with file size,
duration, transcription method, transcription time and timestamp to avoid
duplicate work.

## GUI

Launch a simple desktop interface instead of the command line:

```bash
python gui.py
```

The GUI loads `config.cfg` and `summary_prompt.txt` at startup. Changes to the API key,
Whisper models or the summary prompt can be edited in the window and saved back to the
respective files. When an audio file is selected and transcribed, a Markdown file and
matching PDF are written to the chosen location.

## Compiling the program

Use [PyInstaller](https://pyinstaller.org/) to create a standalone executable. Include the
template config, prompt and README so the application can recreate defaults on first run:

```bash
# adjust the path separator for your platform (; on Windows, : on Linux/macOS)
pyinstaller gui.py --name gpt_transcribe --noconsole --onefile --add-data "config.template.cfg;." --add-data "summary_prompt.txt;." --add-data "README.md;." --icon logo/logo.ico
```

The resulting binary in `dist/` can be executed directly or packaged as shown below.

## Creating a Windows installer and GitHub release

1. Install [Inno Setup](https://jrsoftware.org/isinfo.php) and ensure `iscc.exe` is in your `PATH`.
2. Run the helper script that installs dependencies, builds the executable and compiles the installer:
   ```bat
   build_windows.bat
   ```
   The script installs packages from `requirements.txt`, installs PyInstaller and
   creates `dist\gpt_transcribe.exe` and `gpt_transcribe_setup.exe`.
3. Commit and push your changes, then create a GitHub release. Upload the generated
   installer or `dist\gpt_transcribe.exe` so others can download it.

## Creating a macOS app and DMG

A helper script `build_macos.sh` builds a standalone binary and packs it into a
compressed disk image:

```bash
./build_macos.sh
```

The script installs packages from `requirements.txt`, installs PyInstaller and
creates `dist/gpt_transcribe` and `dist/gpt_transcribe.dmg`.

## Creating a Linux AppImage

A helper script `build_appimage.sh` builds an AppImage with all Python dependencies and a static `ffmpeg`.

```bash
./build_appimage.sh
```

The script installs packages from `requirements.txt`, installs PyInstaller and
downloads `appimagetool` if needed. Downloaded archives are cached under
`packages/` so they are only fetched again when missing or outdated. The
resulting AppImage runs on any modern distribution and is written to `dist/`.

## Creating a Flatpak

`build_flatpak.sh` wraps `flatpak-builder` to produce a `gpt_transcribe.flatpak`
bundle that contains all Python dependencies and a static `ffmpeg` binary.

```bash
./build_flatpak.sh
```

Ensure `flatpak` and `flatpak-builder` are installed. The script installs the
required Tkinter extension automatically. The generated bundle runs on any
distribution with Flatpak support and is placed in `dist/`.
