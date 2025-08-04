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
template config and prompt so the application can recreate defaults on first run:

```bash
# adjust the path separator for your platform (; on Windows, : on Linux/macOS)
pyinstaller gui.py --name gpt_transcribe --noconsole --onefile \
  --add-data "config.template.cfg:." --add-data "summary_prompt.txt:."
```

The resulting binary in `dist/` can be executed directly or packaged as shown below.

## Creating a Windows installer and GitHub release

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build a self‑contained executable including the default config template and prompt:
   ```bash
   pyinstaller gui.py --name gpt_transcribe --noconsole --onefile \
     --add-data "config.template.cfg;." --add-data "summary_prompt.txt;."
   ```
   ```bash
   pyinstaller gui.py --name gpt_transcribe --noconsole --onefile --add-data "config.template.cfg;." --add-data "summary_prompt.txt;. --icon=logo/logo.ico"
   ```
   The executable is placed in the `dist` directory as `gpt_transcribe.exe`.
3. (Optional) Use a tool such as [Inno Setup](https://jrsoftware.org/isinfo.php) to turn `gpt_transcribe.exe`
   into a standard Windows installer.
4. Commit and push your changes, then create a GitHub release. Upload the generated
   installer or `gpt_transcribe.exe` from the `dist` directory as a release asset so others can
   download it.

## Creating a Linux AppImage

1. Install PyInstaller and download [AppImageTool](https://github.com/AppImage/AppImageKit/releases).
   ```bash
   pip install pyinstaller
   ```
2. Build the application directory with bundled defaults:
   ```bash
   pyinstaller gui.py --name gpt_transcribe --noconsole \
     --add-data "config.template.cfg:." --add-data "summary_prompt.txt:."
   ```
3. Rename the folder and add metadata:
   ```bash
   mv dist/gpt_transcribe gpt_transcribe.AppDir
   # add gpt_transcribe.desktop and an icon inside gpt_transcribe.AppDir
   ```
4. Create the AppImage:
   ```bash
   ./appimagetool gpt_transcribe.AppDir gpt_transcribe.AppImage
   ```

## Creating a Flatpak

1. Install `flatpak` and `flatpak-builder` on your system.
2. Build the application with PyInstaller including the config template and prompt:
   ```bash
   pyinstaller gui.py --name gpt_transcribe --noconsole \
     --add-data "config.template.cfg:." --add-data "summary_prompt.txt:."
   ```
3. Create a Flatpak manifest `io.github.gpt_transcribe.yaml` that installs the
   PyInstaller output. A minimal example:
   ```yaml
   app-id: io.github.gpt_transcribe
   runtime: org.freedesktop.Platform
   runtime-version: "23.08"
   sdk: org.freedesktop.Sdk
   command: gpt_transcribe
   modules:
     - name: gpt_transcribe
       buildsystem: simple
       build-commands:
         - install -Dm755 dist/gpt_transcribe /app/bin/gpt_transcribe
       sources:
         - type: dir
           path: dist
   ```
4. Build and bundle the Flatpak:
   ```bash
   flatpak-builder --force-clean build-dir io.github.gpt_transcribe.yaml
   flatpak build-bundle build-dir gpt_transcribe.flatpak io.github.gpt_transcribe
   ```
