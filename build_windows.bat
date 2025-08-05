@echo off
REM Build standalone executable and Inno Setup installer for gpt_transcribe

pip install -r requirements.txt || goto :error
pip install pyinstaller || goto :error

REM include Whisper assets like mel_filters.npz so transcription works in the packaged app
pyinstaller gui.py --name gpt_transcribe --noconsole --onefile --collect-data whisper --add-data "config.template.cfg;." --add-data "summary_prompt.txt;." --add-data "README.md;." --icon logo/logo.ico || goto :error

iscc gpt_transcribe.iss
goto :eof

:error
echo Build failed.
exit /b 1
