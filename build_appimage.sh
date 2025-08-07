#!/bin/bash

set -euo pipefail

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
PACKAGES_DIR="$(pwd)/packages"
APPIMAGETOOL="${PACKAGES_DIR}/appimagetool-x86_64.AppImage"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
FFMPEG_TAR="${PACKAGES_DIR}/ffmpeg-release-amd64-static.tar.xz"
DIST_DIR="$(pwd)/dist"
APPDIR="${APP_NAME}.AppDir"
OUTPUT_APPIMAGE="${DIST_DIR}/${APP_NAME}-x86_64.AppImage"
USE_DOCKER=${USE_DOCKER:-1}
DOCKER_IMAGE=${DOCKER_IMAGE:-ubuntu:20.04}

echo "📦 Starting AppImage build for $DISPLAY_NAME"

mkdir -p "$PACKAGES_DIR" "$DIST_DIR"

if command -v docker >/dev/null 2>&1 && [ "$USE_DOCKER" = "1" ]; then
  echo "🐳 Building inside Docker container ($DOCKER_IMAGE) for broad glibc compatibility ..."

  docker run --rm \
    -e DEBIAN_FRONTEND=noninteractive \
    -e HOST_UID="$(id -u)" \
    -e HOST_GID="$(id -g)" \
    -v "$(pwd)":"/src":Z \
    -w "/src" \
    "$DOCKER_IMAGE" bash -eu -o pipefail -c '
      # Re-declare paths for container context
      APP_NAME="GPT_Transcribe"; DISPLAY_NAME="GPT Transcribe"; MAIN_SCRIPT="gui.py"; \
      PACKAGES_DIR="/src/packages"; DIST_DIR="/src/dist"; APPDIR="${APP_NAME}.AppDir"; \
      APPIMAGETOOL="$PACKAGES_DIR/appimagetool-x86_64.AppImage"; \
      APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"; \
      FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"; \
      FFMPEG_TAR="$PACKAGES_DIR/ffmpeg-release-amd64-static.tar.xz"; \
      ICON_SOURCE="/src/logo/logo.png"; ICON_NAME="gpt_transcribe.png"; \
      
      apt-get update && \
      apt-get install -y --no-install-recommends \
        python3 python3-venv python3-pip python3-tk python3-dev libpython3.8 libpython3.8-dev \
        curl ca-certificates patchelf xz-utils \
        tcl tk \
        build-essential && \
      python3 -m pip install --upgrade pip && \
      python3 -m venv /tmp/.venv && . /tmp/.venv/bin/activate && \
      pip install --no-cache-dir -r /src/requirements.txt pyinstaller && \
      # Ensure appimagetool and ffmpeg archives
      mkdir -p "$PACKAGES_DIR" "$DIST_DIR" && \
      if [ ! -f "$APPIMAGETOOL" ]; then curl -L -o "$APPIMAGETOOL" "$APPIMAGETOOL_URL"; chmod +x "$APPIMAGETOOL"; fi && \
      if [ ! -f "$FFMPEG_TAR" ]; then curl -L -o "$FFMPEG_TAR" "$FFMPEG_URL"; fi && \
      # Clean old artifacts
      rm -rf build/ "$DIST_DIR/${APP_NAME}"* "$APPDIR" __pycache__ *.spec && \
      # Build PyInstaller onefile and bundle whisper data
      pyinstaller --onefile \
        --collect-data whisper \
        --add-data "/src/config.template.cfg:." \
        --add-data "/src/summary_prompt.txt:." \
        --add-data "/src/README.md:." \
        --hidden-import=audioop \
        "/src/${MAIN_SCRIPT}" && \
      # Prepare AppDir
      mkdir -p ${APPDIR}/usr/bin ${APPDIR}/usr/lib ${APPDIR}/usr/share/applications ${APPDIR}/usr/share/metainfo ${APPDIR}/usr/share/icons/hicolor/256x256/apps && \
      cp "$DIST_DIR/${MAIN_SCRIPT%.py}" ${APPDIR}/usr/bin/gpt_transcribe && \
      # Copy Tcl/Tk runtimes and data (best-effort)
      cp /usr/lib/x86_64-linux-gnu/libtcl8.6.so ${APPDIR}/usr/lib/ || true && \
      cp /usr/lib/x86_64-linux-gnu/libtk8.6.so ${APPDIR}/usr/lib/ || true && \
      cp -r /usr/lib/tcl8.6 ${APPDIR}/usr/lib/ || true && \
      cp -r /usr/lib/tk8.6 ${APPDIR}/usr/lib/ || true && \
      # Fallback paths used on some Ubuntu images
      cp -r /usr/share/tcltk/tcl8.6 ${APPDIR}/usr/lib/ || true && \
      cp -r /usr/share/tcltk/tk8.6 ${APPDIR}/usr/lib/ || true && \
      # Provide ffmpeg inside AppImage
      TMP_FFMPEG=$(mktemp -d) && \
      tar -xf "$FFMPEG_TAR" -C "$TMP_FFMPEG" --strip-components=1 && \
      cp "$TMP_FFMPEG/ffmpeg" "${APPDIR}/usr/bin/ffmpeg" && \
      cp "$TMP_FFMPEG/ffprobe" "${APPDIR}/usr/bin/ffprobe" && \
      rm -rf "$TMP_FFMPEG" && \
      # Icon and desktop files
      cp "$ICON_SOURCE" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/${ICON_NAME}" && \
      cp "$ICON_SOURCE" "${APPDIR}/gpt_transcribe.png" && \
      cat > ${APPDIR}/gpt_transcribe.desktop <<EOF
 [Desktop Entry]
 Type=Application
 Name=${DISPLAY_NAME}
 Exec=gpt_transcribe
 Icon=gpt_transcribe
 Comment=${DISPLAY_NAME} AppImage
 Categories=Utility;
 EOF
      cp /src/io.github.gpt_transcribe.metainfo.xml ${APPDIR}/usr/share/metainfo/io.github.gpt_transcribe.metainfo.xml && \
      # AppRun with env for Tcl/Tk and rpath
      cat > ${APPDIR}/AppRun << 'EOF'
#!/bin/bash
set -e
HERE="$(dirname "$(readlink -f "\$0")")"
export PATH="\$HERE/usr/bin:\$PATH"
export LD_LIBRARY_PATH="\$HERE/usr/lib:\${LD_LIBRARY_PATH:-}"
export TCL_LIBRARY="\$HERE/usr/lib/tcl8.6"
export TK_LIBRARY="\$HERE/usr/lib/tk8.6"
exec "\$HERE/usr/bin/gpt_transcribe" "\$@"
EOF
      chmod +x ${APPDIR}/AppRun && \
      # Build AppImage
      "$APPIMAGETOOL" ${APPDIR} ${OUTPUT_APPIMAGE}
      # Restore host ownership for created files
      chown -R "$HOST_UID:$HOST_GID" /src/dist /src/packages || true
    '

  echo "✅ Done: AppImage created at ${OUTPUT_APPIMAGE}"
else
  echo "⚠️  Docker not available or disabled. Building natively (compatibility may be reduced)."

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

  echo "🧹 Removing old builds ..."
  rm -rf build/ dist/ ${APPDIR} __pycache__ *.spec
  mkdir -p "$DIST_DIR"

  echo "⚙️  Building the Python program with PyInstaller ..."
  pyinstaller --onefile \
      --collect-data whisper \
      --add-data "config.template.cfg:." \
      --add-data "summary_prompt.txt:." \
      --add-data "README.md:." \
      --hidden-import=audioop \
      ${MAIN_SCRIPT}

  echo "📁 Creating AppDir structure ..."
  mkdir -p ${APPDIR}/usr/bin ${APPDIR}/usr/lib ${APPDIR}/usr/share/applications ${APPDIR}/usr/share/metainfo ${APPDIR}/usr/share/icons/hicolor/256x256/apps
  cp ${DIST_DIR}/${MAIN_SCRIPT%.py} ${APPDIR}/usr/bin/gpt_transcribe
  # Try to include Tcl/Tk
  cp /usr/lib/x86_64-linux-gnu/libtcl*.so ${APPDIR}/usr/lib/ 2>/dev/null || true
  cp /usr/lib/x86_64-linux-gnu/libtk*.so ${APPDIR}/usr/lib/ 2>/dev/null || true
  cp -r /usr/lib/tcl* ${APPDIR}/usr/lib/ 2>/dev/null || true
  cp -r /usr/lib/tk* ${APPDIR}/usr/lib/ 2>/dev/null || true
  
  # Provide ffmpeg inside AppImage
  TMP_FFMPEG=$(mktemp -d)
  tar -xf "$FFMPEG_TAR" -C "$TMP_FFMPEG" --strip-components=1
  cp "$TMP_FFMPEG/ffmpeg" "${APPDIR}/usr/bin/ffmpeg"
  cp "$TMP_FFMPEG/ffprobe" "${APPDIR}/usr/bin/ffprobe"
  rm -rf "$TMP_FFMPEG"

  # AppRun
  cat > ${APPDIR}/AppRun << 'EOF'
#!/bin/bash
set -e
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
export LD_LIBRARY_PATH="$HERE/usr/lib:${LD_LIBRARY_PATH:-}"
export TCL_LIBRARY="$HERE/usr/lib/tcl8.6"
export TK_LIBRARY="$HERE/usr/lib/tk8.6"
exec "$HERE/usr/bin/gpt_transcribe" "$@"
EOF
  chmod +x ${APPDIR}/AppRun

  # .desktop and icon
  cat > ${APPDIR}/gpt_transcribe.desktop <<EOF
[Desktop Entry]
Type=Application
Name=${DISPLAY_NAME}
Exec=gpt_transcribe
Icon=gpt_transcribe
Comment=${DISPLAY_NAME} AppImage
Categories=Utility;
EOF
  cp ${ICON_SOURCE} ${APPDIR}/usr/share/icons/hicolor/256x256/apps/${ICON_NAME}
  cp ${ICON_SOURCE} ${APPDIR}/gpt_transcribe.png
  cp io.github.gpt_transcribe.metainfo.xml ${APPDIR}/usr/share/metainfo/io.github.gpt_transcribe.metainfo.xml

  echo "📦 Creating AppImage with $APPIMAGETOOL ..."
  "$APPIMAGETOOL" ${APPDIR} ${OUTPUT_APPIMAGE}

  echo "✅ Done: AppImage created at ${OUTPUT_APPIMAGE}"
fi

