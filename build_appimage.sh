#!/bin/bash

set -e

# === EINSTELLUNGEN ===
APP_NAME="GPT_Transcribe"
DISPLAY_NAME="GPT Transcribe"
MAIN_SCRIPT="gui.py"
ICON_SOURCE="logo/logo.png"
ICON_NAME="gpt_transcribe.png"
APPIMAGETOOL="appimagetool-x86_64.AppImage"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
FFMPEG_TAR="ffmpeg-release-amd64-static.tar.xz"
FLATPAK_MANIFEST="io.github.gpt_transcribe.yaml"
DIST_DIR="./dist"
APPDIR="${APP_NAME}.AppDir"
OUTPUT_APPIMAGE="${DIST_DIR}/${APP_NAME}-x86_64.AppImage"
OUTPUT_FLATPAK="${DIST_DIR}/gpt_transcribe.flatpak"
DISABLE_CACHE=${DISABLE_CACHE:-1}  # set to 0 to reuse flatpak-builder cache

echo "📦 Starte AppImage-Build für $DISPLAY_NAME"

# === CHECK: appimagetool vorhanden? ===
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "⬇️  Lade appimagetool herunter ..."
    curl -L -o "$APPIMAGETOOL" "$APPIMAGETOOL_URL"
    chmod +x "$APPIMAGETOOL"
else
    echo "✅ appimagetool ist bereits vorhanden."
fi

# === CHECK: ffmpeg vorhanden? ===
if [ ! -f "$FFMPEG_TAR" ]; then
    echo "⬇️  Lade ffmpeg herunter ..."
    curl -L -o "$FFMPEG_TAR" "$FFMPEG_URL"
else
    echo "✅ ffmpeg-Archiv ist bereits vorhanden."
fi

# === CLEANUP ===
echo "🧹 Entferne alte Builds ..."
rm -rf build/ dist/ ${APPDIR} __pycache__ *.spec

# === Abhängigkeiten voraussetzen ===
echo "ℹ️  Python-Abhängigkeiten und PyInstaller müssen bereits installiert sein."

# === Kompilieren mit PyInstaller ===
echo "⚙️  Baue das Python-Programm mit PyInstaller ..."
pyinstaller --onefile \
    --add-data "config.template.cfg:." \
    --add-data "summary_prompt.txt:." \
    --add-data "README.md:." \
    ${MAIN_SCRIPT}

# === AppDir-Struktur vorbereiten ===
echo "📁 Erstelle AppDir-Struktur ..."
mkdir -p ${APPDIR}/usr/bin
cp ${DIST_DIR}/${MAIN_SCRIPT%.py} ${APPDIR}/usr/bin/gpt_transcribe
cp ${ICON_SOURCE} ${APPDIR}/${ICON_NAME}

# ffmpeg in AppImage bereitstellen
TMP_FFMPEG=$(mktemp -d)
tar -xf "$FFMPEG_TAR" -C "$TMP_FFMPEG" --strip-components=1
cp "$TMP_FFMPEG/ffmpeg" "${APPDIR}/usr/bin/ffmpeg"
cp "$TMP_FFMPEG/ffprobe" "${APPDIR}/usr/bin/ffprobe"
rm -rf "$TMP_FFMPEG"

# === AppRun erstellen ===
echo "⚙️ Erstelle AppRun ..."
cat > ${APPDIR}/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/gpt_transcribe" "$@"
EOF
chmod +x ${APPDIR}/AppRun

# === .desktop Datei erstellen ===
echo "🖼 Erstelle .desktop-Datei ..."
cat > ${APPDIR}/gpt_transcribe.desktop <<EOF
[Desktop Entry]
Type=Application
Name=${DISPLAY_NAME}
Exec=gpt_transcribe
Icon=${ICON_NAME%.png}
Comment=${DISPLAY_NAME} AppImage
Categories=Utility;
EOF

# === AppImage erstellen ===
echo "📦 Erstelle AppImage mit $APPIMAGETOOL ..."
./$APPIMAGETOOL ${APPDIR} ${OUTPUT_APPIMAGE}

echo "✅ Fertig: AppImage erstellt unter ${OUTPUT_APPIMAGE}"

# === Flatpak erstellen ===
echo "📦 Erstelle Flatpak ..."
if [ "$DISABLE_CACHE" = "1" ]; then
    echo "⚠️  Cache deaktiviert – 'Pruning cache' wird übersprungen"
    flatpak-builder \
        --repo=repo \
        --force-clean \
        --delete-build-dirs \
        --disable-cache \
        build-dir ${FLATPAK_MANIFEST}
else
    echo "🗃  Verwende Flatpak-Build-Cache"
    flatpak-builder \
        --repo=repo \
        --force-clean \
        build-dir ${FLATPAK_MANIFEST}
fi
flatpak build-bundle repo "${OUTPUT_FLATPAK}" io.github.gpt_transcribe
echo "✅ Fertig: Flatpak erstellt unter ${OUTPUT_FLATPAK}"

# === Testen (optional) ===
echo "🚀 Starte Testlauf des AppImages ..."
${OUTPUT_APPIMAGE}

