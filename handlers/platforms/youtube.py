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
    loop     = asyncio.get_event_loop()

    # Each attempt: (format, use_cookies)
    attempts = [
        ("best[height<=720]", True),
        ("best[height<=480]", True),
        ("best[height<=360]", True),
        ("best",              True),
        ("best[height<=720]", False),
        ("best",              False),
        ("worst",             False),
    ]

    info = None
    last_error = None

    for fmt, use_cookies in attempts:
        ydl_opts = {
            "outtmpl":            out_tmpl,
            "format":             fmt,
            "quiet":              True,
            "no_warnings":        True,
            "noplaylist":         True,
            "nocheckcertificate": True,
            "ignoreerrors":       False,
            "retries":            3,
        }

        if use_cookies and os.path.exists(COOKIES):
            ydl_opts["cookiefile"] = COOKIES

        def _run(opts=ydl_opts):
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)

        try:
            info = await loop.run_in_executor(None, _run)
            logger.info(f"[YT] Success → format={fmt}, cookies={use_cookies}")
            break
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[YT] Failed → format={fmt}, cookies={use_cookies}: {e}")
            continue

    if info is None:
        raise RuntimeError(f"❌ Download failed!\n\n`{last_error[:300] if last_error else 'Unknown error'}`")

    file_path = None
    for f in sorted(os.listdir(TMP_DIR)):
        if f.startswith(f"yt_{uid}") and not f.endswith(".part"):
            file_path = os.path.join(TMP_DIR, f)
            break

    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError("Downloaded file not found.")

    raw_dur  = info.get("duration", 0) or 0
    duration = f"{int(raw_dur)//60}:{int(raw_dur)%60:02d}"
    size_mb  = os.path.getsize(file_path) / (1024 * 1024)

    increment_stat("youtube")

    return {
        "file_path": file_path,
        "title":     info.get("title", "YouTube Video"),
        "duration":  duration,
        "size":      f"{size_mb:.1f} MB",
    }
