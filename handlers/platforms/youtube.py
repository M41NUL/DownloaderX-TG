"""
╔══════════════════════════════════════════╗
║     DOWNLOADER X — YOUTUBE PLATFORM      ║
║  /yt command + yt-dlp downloader         ║
║  Author    : Md. Mainul Islam            ║
║  Copyright : (c) 2026 MAINUL - X        ║
╚══════════════════════════════════════════╝
"""

import asyncio
import logging
import os
import uuid
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.admin import increment_stat

logger = logging.getLogger("DownloaderX.youtube")
WAITING_KEY = "waiting_platform"
TMP_DIR = "downloads"
os.makedirs(TMP_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# /yt command
# ─────────────────────────────────────────────────────────────────────────────
async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set waiting state then ask user for the link."""
    context.user_data[WAITING_KEY] = "youtube"
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="dl_home")]]
    await update.message.reply_text(
        "▶️ *YouTube Downloader*\n\n"
        "Please send me the YouTube video link:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Core downloader (called by downloads.py → process_download)
# ─────────────────────────────────────────────────────────────────────────────
async def download_youtube(url: str) -> dict:
    """
    Downloads a YouTube video using yt-dlp.
    Returns dict: {file_path, title, duration, size}
    """
    uid       = uuid.uuid4().hex
    out_tmpl  = os.path.join(TMP_DIR, f"yt_{uid}.%(ext)s")

    ydl_opts = {
        "outtmpl":         out_tmpl,
        "format":          "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet":           True,
        "no_warnings":     True,
        "noplaylist":      True,
    }

    loop = asyncio.get_event_loop()

    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info

    info = await loop.run_in_executor(None, _run)

    # Resolve actual file path
    file_path = None
    for f in os.listdir(TMP_DIR):
        if f.startswith(f"yt_{uid}"):
            file_path = os.path.join(TMP_DIR, f)
            break

    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError("Downloaded file not found.")

    # Duration formatting
    raw_dur  = info.get("duration", 0)
    minutes  = int(raw_dur) // 60
    seconds  = int(raw_dur) % 60
    duration = f"{minutes}:{seconds:02d}"

    # Size formatting
    raw_size = os.path.getsize(file_path)
    size_mb  = raw_size / (1024 * 1024)
    size_str = f"{size_mb:.1f} MB"

    increment_stat("youtube")

    return {
        "file_path": file_path,
        "title":     info.get("title", "Unknown"),
        "duration":  duration,
        "size":      size_str,
    }
