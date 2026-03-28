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


async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[WAITING_KEY] = "youtube"
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="dl_home")]]
    await update.message.reply_text(
        "▶️ *YouTube Downloader*\n\n"
        "Please send me the YouTube video or Shorts link:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def download_youtube(url: str) -> dict:
    uid      = uuid.uuid4().hex
    out_tmpl = os.path.join(TMP_DIR, f"yt_{uid}.%(ext)s")

    ydl_opts = {
        "outtmpl":             out_tmpl,
        "format":              "bestvideo[ext=mp4][filesize<45M]+bestaudio[ext=m4a]/best[ext=mp4][filesize<45M]/best",
        "merge_output_format": "mp4",
        "quiet":               True,
        "no_warnings":         True,
        "noplaylist":          True,
        # Bypass bot detection
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "web"],
            }
        },
        "http_headers": {
            "User-Agent": (
                "com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X)"
            ),
        },
        # Avoid 403 errors
        "sleep_interval":      1,
        "max_sleep_interval":  3,
    }

    loop = asyncio.get_event_loop()

    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    info = await loop.run_in_executor(None, _run)

    file_path = None
    for f in os.listdir(TMP_DIR):
        if f.startswith(f"yt_{uid}"):
            file_path = os.path.join(TMP_DIR, f)
            break

    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError("Downloaded file not found.")

    raw_dur  = info.get("duration", 0)
    duration = f"{int(raw_dur)//60}:{int(raw_dur)%60:02d}"
    size_mb  = os.path.getsize(file_path) / (1024 * 1024)

    increment_stat("youtube")

    return {
        "file_path": file_path,
        "title":     info.get("title", "YouTube Video"),
        "duration":  duration,
        "size":      f"{size_mb:.1f} MB",
    }
