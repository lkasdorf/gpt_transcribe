@echo off
REM Build standalone executable and Inno Setup installer for gpt_transcribe

REM Python-Abhängigkeiten und PyInstaller müssen bereits installiert sein
pyinstaller gui.py --name gpt_transcribe --noconsole --onefile --add-data "config.template.cfg;." --add-data "summary_prompt.txt;." --add-data "README.md;." --icon logo/logo.ico || goto :error

iscc gpt_transcribe.iss
goto :eof

:error
echo Build failed.
exit /b 1
