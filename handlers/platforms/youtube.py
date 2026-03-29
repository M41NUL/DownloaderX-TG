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
import shutil
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.admin import increment_stat, is_maintenance
from config import MAINTENANCE_TEXT

logger = logging.getLogger("DownloaderX.youtube")

WAITING_KEY = "waiting_platform"
TMP_DIR     = "downloads"
COOKIES     = "cookies.txt"

os.makedirs(TMP_DIR, exist_ok=True)


async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_maintenance():
        await update.message.reply_text(MAINTENANCE_TEXT, parse_mode="Markdown")
        return

    context.user_data[WAITING_KEY] = "youtube"
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="dl_home")]]

    sent = await update.message.reply_text(
        "▶️ *YouTube Downloader*\n\n"
        "Please send me the YouTube video or Shorts link:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    context.user_data["waiting_msg_id"]  = sent.message_id
    context.user_data["waiting_chat_id"] = sent.chat.id


async def download_youtube(url: str) -> dict:
    uid      = uuid.uuid4().hex
    out_tmpl = os.path.join(TMP_DIR, f"yt_{uid}.%(ext)s")

    has_ffmpeg = shutil.which("ffmpeg") is not None

    
    if has_ffmpeg:
        fmt = (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]"
            "/bestvideo+bestaudio"
            "/best[ext=mp4]"
            "/best"
        )
    else:
        fmt = (
            "best[ext=mp4]"
            "/best[height<=720][ext=mp4]"
            "/best[height<=480]"
            "/best"
        )

    ydl_opts = {
        "outtmpl":             out_tmpl,
        "format":              fmt,
        "merge_output_format": "mp4",
        "quiet":               True,
        "no_warnings":         True,
        "noplaylist":          True,
        "cookiefile":          COOKIES if os.path.exists(COOKIES) else None,
        "nocheckcertificate":  True,

        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "web"],
            }
        },

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/134.0.0.0 Mobile Safari/537.36"
            ),
        },

        "socket_timeout":    30,
        "retries":           5,
        "fragment_retries":  5,
        "sleep_interval":    1,
        "max_sleep_interval": 3,
    }

    loop = asyncio.get_event_loop()

    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info = await loop.run_in_executor(None, _run)
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp DownloadError: {e}")
        raise RuntimeError(f"YouTube download failed: {e}")

    
    file_path = None
    for f in sorted(os.listdir(TMP_DIR)):
        if f.startswith(f"yt_{uid}") and not f.endswith(".part"):
            file_path = os.path.join(TMP_DIR, f)
            break

    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError("Downloaded file not found after yt-dlp run.")

    raw_dur  = info.get("duration", 0) or 0
    duration = f"{int(raw_dur) // 60}:{int(raw_dur) % 60:02d}"
    size_mb  = os.path.getsize(file_path) / (1024 * 1024)

    increment_stat("youtube")

    return {
        "file_path": file_path,
        "title":     info.get("title", "YouTube Video"),
        "duration":  duration,
        "size":      f"{size_mb:.1f} MB",
    }
