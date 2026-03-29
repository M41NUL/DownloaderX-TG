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

    ydl_opts = {
        "outtmpl":            out_tmpl,
        # "best" always picks an available format - no more format errors
        "format":             "best",
        "format_sort":        ["res:720", "ext:mp4:m4a"],
        "quiet":              True,
        "no_warnings":        True,
        "noplaylist":         True,
        "cookiefile":         COOKIES if os.path.exists(COOKIES) else None,
        "nocheckcertificate": True,

        # Android client unlocks maximum formats in 2026
        "extractor_args": {
            "youtube": {
                "player_client": ["android"],
            }
        },

        "http_headers": {
            "User-Agent": (
                "com.google.android.youtube/19.09.37 "
                "(Linux; U; Android 11) gzip"
            ),
        },

        "socket_timeout":   30,
        "retries":          10,
        "fragment_retries": 10,
    }

    if has_ffmpeg:
        ydl_opts["merge_output_format"] = "mp4"

    loop = asyncio.get_event_loop()

    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info = await loop.run_in_executor(None, _run)
    except yt_dlp.utils.DownloadError as e:
        err_str = str(e)
        logger.error(f"yt-dlp DownloadError: {err_str}")

        if "Sign in" in err_str or "age" in err_str.lower():
            raise RuntimeError("⛔ This video requires login or is age-restricted.")
        elif "private" in err_str.lower():
            raise RuntimeError("🔒 This video is private.")
        elif "unavailable" in err_str.lower():
            raise RuntimeError("❌ This video is unavailable in this region.")
        else:
            raise RuntimeError(f"YouTube download failed:\n`{err_str}`")

    # Find the final file (skip .part files)
    file_path = None
    for f in sorted(os.listdir(TMP_DIR)):
        if f.startswith(f"yt_{uid}") and not f.endswith(".part"):
            file_path = os.path.join(TMP_DIR, f)
            break

    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError("Downloaded file not found after yt-dlp run.")

    # Video metadata
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
