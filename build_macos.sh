#!/bin/bash
set -e

# Build standalone macOS binary and DMG for gpt_transcribe

pip3 install -r requirements.txt
pip3 install pyinstaller

pyinstaller gui.py --name gpt_transcribe --noconsole --onefile \
    --collect-data whisper \  # bundle Whisper's assets like mel_filters.npz
    --add-data "config.template.cfg:." \
    --add-data "summary_prompt.txt:." \
    --add-data "README.md:."

# Create a compressed disk image containing the build
mkdir -p dist
rm -f dist/gpt_transcribe.dmg
hdiutil create -volname gpt_transcribe -srcfolder dist \
    -ov -format UDZO dist/gpt_transcribe.dmg
