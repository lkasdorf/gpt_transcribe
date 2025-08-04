#!/bin/bash

set -e

# === EINSTELLUNGEN ===
APP_NAME="GPT_Transcribe"
DISPLAY_NAME="GPT Transcribe"
MAIN_SCRIPT="gui.py"
ICON_SOURCE="Logo/logo.png"
ICON_NAME="gpt_transcribe.png"
APPIMAGETOOL="appimagetool-x86_64.AppImage"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
DIST_DIR="./dist"
APPDIR="${APP_NAME}.AppDir"
OUTPUT_APPIMAGE="${DIST_DIR}/${APP_NAME}-x86_64.AppImage"

echo "📦 Starte AppImage-Build für $DISPLAY_NAME"

# === CHECK: appimagetool vorhanden? ===
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "⬇️  Lade appimagetool herunter ..."
    curl -L -o "$APPIMAGETOOL" "$APPIMAGETOOL_URL"
    chmod +x "$APPIMAGETOOL"
else
    echo "✅ appimagetool ist bereits vorhanden."
fi

# === CLEANUP ===
echo "🧹 Entferne alte Builds ..."
rm -rf build/ dist/ ${APPDIR} __pycache__ *.spec

# === Abhängigkeiten installieren ===
echo "📦 Installiere Python-Abhängigkeiten ..."
pip install -r requirements.txt
pip install pyinstaller

# === Kompilieren mit PyInstaller ===
echo "⚙️  Baue das Python-Programm mit PyInstaller ..."
pyinstaller --onefile ${MAIN_SCRIPT}

# === AppDir-Struktur vorbereiten ===
echo "📁 Erstelle AppDir-Struktur ..."
mkdir -p ${APPDIR}/usr/bin
cp ${DIST_DIR}/${MAIN_SCRIPT%.py} ${APPDIR}/usr/bin/gpt_transcribe
cp ${ICON_SOURCE} ${APPDIR}/${ICON_NAME}

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

# === Testen (optional) ===
echo "🚀 Starte Testlauf des AppImages ..."
${OUTPUT_APPIMAGE}

