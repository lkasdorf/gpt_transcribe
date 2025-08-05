#!/bin/bash

set -e

# Redirect all output to a log file
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/build_flatpak.log"
exec > >(tee "$LOG_FILE") 2>&1

# === SETTINGS ===
PACKAGES_DIR="./packages"
FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
FFMPEG_TAR="${PACKAGES_DIR}/ffmpeg-release-amd64-static.tar.xz"
FLATPAK_MANIFEST="io.github.gpt_transcribe.yaml"
DIST_DIR="./dist"
OUTPUT_FLATPAK="${DIST_DIR}/gpt_transcribe.flatpak"
FLATPAK_STATE_DIR="${PACKAGES_DIR}/flatpak-builder"
DISABLE_CACHE=${DISABLE_CACHE:-0}  # set to 1 to disable flatpak-builder cache

echo "📦 Starting Flatpak build for GPT Transcribe"

mkdir -p "$PACKAGES_DIR" "$FLATPAK_STATE_DIR" "$DIST_DIR"

# === Check: ffmpeg archive present? ===
if [ ! -f "$FFMPEG_TAR" ]; then
    echo "⬇️  Downloading ffmpeg ..."
    curl -L -o "$FFMPEG_TAR" "$FFMPEG_URL"
else
    echo "✅ ffmpeg archive already present."
fi

# === Ensure flatpak tools are available ===
if ! command -v flatpak >/dev/null 2>&1; then
    echo "❌ flatpak not found. Please install flatpak and flatpak-builder."
    exit 1
fi
if ! command -v flatpak-builder >/dev/null 2>&1; then
    echo "❌ flatpak-builder not found. Please install flatpak-builder."
    exit 1
fi

# Ensure Flathub remote exists (needed for potential dependencies)
if ! flatpak remote-list | grep -q '^flathub'; then
    echo "🔗 Adding Flathub remote ..."
    flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
fi

# === Build Flatpak ===
if [ "$DISABLE_CACHE" = "1" ]; then
    echo "⚠️  Cache disabled"
    flatpak-builder \
        --force-clean \
        --delete-build-dirs \
        --disable-cache \
        --state-dir="${FLATPAK_STATE_DIR}" \
        build-dir ${FLATPAK_MANIFEST}
else
    echo "🗃  Using Flatpak build cache"
    flatpak-builder \
        --force-clean \
        --state-dir="${FLATPAK_STATE_DIR}" \
        build-dir ${FLATPAK_MANIFEST}
fi

flatpak build-export repo build-dir
flatpak build-bundle repo "${OUTPUT_FLATPAK}" io.github.gpt_transcribe

echo "✅ Done: Flatpak created at ${OUTPUT_FLATPAK}"
