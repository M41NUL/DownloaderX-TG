"""
╔══════════════════════════════════════════╗
║     DOWNLOADER X — FACEBOOK PLATFORM     ║
║  /fb command + yt-dlp downloader         ║
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

logger = logging.getLogger("DownloaderX.facebook")
WAITING_KEY = "waiting_platform"
TMP_DIR = "downloads"
os.makedirs(TMP_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# /fb command
# ─────────────────────────────────────────────────────────────────────────────
async def fb_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[WAITING_KEY] = "facebook"
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="dl_home")]]
    await update.message.reply_text(
        "📘 *Facebook Downloader*\n\n"
        "Please send me the Facebook video link:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Core downloader
# ─────────────────────────────────────────────────────────────────────────────
async def download_facebook(url: str) -> dict:
    uid      = uuid.uuid4().hex
    out_tmpl = os.path.join(TMP_DIR, f"fb_{uid}.%(ext)s")

    ydl_opts = {
        "outtmpl":             out_tmpl,
        "format":              "bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet":               True,
        "no_warnings":         True,
        "noplaylist":          True,
    }

    loop = asyncio.get_event_loop()

    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    info = await loop.run_in_executor(None, _run)

    file_path = None
    for f in os.listdir(TMP_DIR):
        if f.startswith(f"fb_{uid}"):
            file_path = os.path.join(TMP_DIR, f)
            break

    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError("Downloaded file not found.")

    raw_dur  = info.get("duration", 0)
    minutes  = int(raw_dur) // 60
    seconds  = int(raw_dur) % 60
    duration = f"{minutes}:{seconds:02d}"

    size_mb  = os.path.getsize(file_path) / (1024 * 1024)
    size_str = f"{size_mb:.1f} MB"

    increment_stat("facebook")

    return {
        "file_path": file_path,
        "title":     info.get("title", "Facebook Video"),
        "duration":  duration,
        "size":      size_str,
    }
