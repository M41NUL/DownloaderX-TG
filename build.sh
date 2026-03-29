#!/usr/bin/env bash
# ── Downloader X — Render Build Script ───────────────────────────────────────

set -e

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "📦 Installing yt-dlp FFmpeg..."
pip install yt-dlp[default]

echo "✅ Build complete!"
