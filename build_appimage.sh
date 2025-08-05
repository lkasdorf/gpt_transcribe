#!/bin/bash

set -e

# Redirect all output to a log file
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/build_appimage.log"
exec > >(tee "$LOG_FILE") 2>&1

# === SETTINGS ===
APP_NAME="GPT_Transcribe"
DISPLAY_NAME="GPT Transcribe"
MAIN_SCRIPT="gui.py"
ICON_SOURCE="logo/logo.png"
ICON_NAME="gpt_transcribe.png"
PACKAGES_DIR="./packages"
APPIMAGETOOL="${PACKAGES_DIR}/appimagetool-x86_64.AppImage"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
FFMPEG_TAR="${PACKAGES_DIR}/ffmpeg-release-amd64-static.tar.xz"
DIST_DIR="./dist"
APPDIR="${APP_NAME}.AppDir"
OUTPUT_APPIMAGE="${DIST_DIR}/${APP_NAME}-x86_64.AppImage"

echo "📦 Starting AppImage build for $DISPLAY_NAME"

mkdir -p "$PACKAGES_DIR"

# === Check: appimagetool present? ===
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "⬇️  Downloading appimagetool ..."
    curl -L -o "$APPIMAGETOOL" "$APPIMAGETOOL_URL"
    chmod +x "$APPIMAGETOOL"
else
    echo "✅ appimagetool already present."
fi

# === Check: ffmpeg present? ===
if [ ! -f "$FFMPEG_TAR" ]; then
    echo "⬇️  Downloading ffmpeg ..."
    curl -L -o "$FFMPEG_TAR" "$FFMPEG_URL"
else
    echo "✅ ffmpeg archive already present."
fi

# === Cleanup ===
echo "🧹 Removing old builds ..."
rm -rf build/ dist/ ${APPDIR} __pycache__ *.spec
mkdir -p "$DIST_DIR"

# === Prerequisites ===
echo "ℹ️  Python dependencies and PyInstaller must already be installed."

# Ensure audioop is present; install audioop-lts if missing
if ! python -c "import audioop" &>/dev/null; then
    echo "⬇️  Installing audioop-lts as a replacement for deprecated pyaudioop ..."
    pip install --no-cache-dir audioop-lts
fi

# Ensure Tkinter is available for the GUI
if ! python -c "import tkinter" &>/dev/null; then
    echo "⬇️  Installing python3-tk for Tkinter support ..."
    apt-get update
    apt-get install -y python3-tk
fi

# === Build with PyInstaller ===
echo "⚙️  Building the Python program with PyInstaller ..."
# Bundle Whisper's assets like mel_filters.npz
pyinstaller --onefile \
    --collect-data whisper \
    --add-data "config.template.cfg:." \
    --add-data "summary_prompt.txt:." \
    --add-data "README.md:." \
    --hidden-import=audioop \
    ${MAIN_SCRIPT}

# === Prepare AppDir structure ===
echo "📁 Creating AppDir structure ..."
mkdir -p ${APPDIR}/usr/bin
cp ${DIST_DIR}/${MAIN_SCRIPT%.py} ${APPDIR}/usr/bin/gpt_transcribe
cp ${ICON_SOURCE} ${APPDIR}/${ICON_NAME}

# Provide ffmpeg inside AppImage
TMP_FFMPEG=$(mktemp -d)
tar -xf "$FFMPEG_TAR" -C "$TMP_FFMPEG" --strip-components=1
cp "$TMP_FFMPEG/ffmpeg" "${APPDIR}/usr/bin/ffmpeg"
cp "$TMP_FFMPEG/ffprobe" "${APPDIR}/usr/bin/ffprobe"
rm -rf "$TMP_FFMPEG"

# === Create AppRun ===
echo "⚙️ Creating AppRun ..."
cat > ${APPDIR}/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/gpt_transcribe" "$@"
EOF
chmod +x ${APPDIR}/AppRun

# === Create .desktop file ===
echo "🖼 Creating .desktop file ..."
cat > ${APPDIR}/gpt_transcribe.desktop <<EOF
[Desktop Entry]
Type=Application
Name=${DISPLAY_NAME}
Exec=gpt_transcribe
Icon=${ICON_NAME%.png}
Comment=${DISPLAY_NAME} AppImage
Categories=Utility;
EOF

# Include AppStream metadata to avoid appimagetool warnings
mkdir -p ${APPDIR}/usr/share/metainfo
cp io.github.gpt_transcribe.metainfo.xml ${APPDIR}/usr/share/metainfo/io.github.gpt_transcribe.metainfo.xml

# === Create AppImage ===
echo "📦 Creating AppImage with $APPIMAGETOOL ..."
./$APPIMAGETOOL ${APPDIR} ${OUTPUT_APPIMAGE}

echo "✅ Done: AppImage created at ${OUTPUT_APPIMAGE}"

# === Test run (optional) ===
echo "🚀 Starting test run of the AppImage ..."
${OUTPUT_APPIMAGE}

