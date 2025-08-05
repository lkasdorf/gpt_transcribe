@echo off
REM Build standalone executable and Inno Setup installer for gpt_transcribe

pip install -r requirements.txt || goto :error
pip install pyinstaller || goto :error

REM include Whisper assets like mel_filters.npz so transcription works in the packaged app
pyinstaller gui.py --name gpt_transcribe --noconsole --onefile --collect-data whisper --add-data "config.template.cfg;." --add-data "summary_prompt.txt;." --add-data "README.md;." --icon logo/logo.ico || goto :error

REM compile installer if Inno Setup is available
where iscc >NUL 2>&1
if errorlevel 1 (
    echo.
    echo Inno Setup (iscc.exe) not found in PATH. Skipping installer creation.
    echo Download it from https://jrsoftware.org/isinfo.php and ensure iscc.exe is in PATH.
    goto :eof
)

iscc gpt_transcribe.iss || goto :error
goto :eof

:error
echo Build failed.
exit /b 1
