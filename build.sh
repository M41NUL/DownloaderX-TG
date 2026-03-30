#!/usr/bin/env bash

set -e

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "📦 Installing yt-dlp..."
pip install yt-dlp[default]

echo "⚙️ Downloading and setting up FFmpeg for Render..."
wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz

mv ffmpeg-*-static/ffmpeg .
mv ffmpeg-*-static/ffprobe .

chmod +x ffmpeg ffprobe

rm -rf ffmpeg-*-static ffmpeg-release-amd64-static.tar.xz

echo "✅ Build complete! FFmpeg is ready."
