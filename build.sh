#!/usr/bin/env bash
# ── Downloader X — Render Build Script ───────────────────────────────────────
# Installs ffmpeg (needed by yt-dlp for merging video+audio)

set -e

echo "📦 Installing ffmpeg..."
apt-get update -y && apt-get install -y ffmpeg

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Build complete!"
