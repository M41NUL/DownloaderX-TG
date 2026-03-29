"""
╔══════════════════════════════════════════╗
║    DOWNLOADER X — INSTAGRAM PLATFORM     ║
║  /ig command + yt-dlp downloader         ║
║  Videos, Reels, Posts — all supported    ║
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

logger = logging.getLogger("DownloaderX.instagram")
WAITING_KEY = "waiting_platform"
TMP_DIR     = "downloads"
COOKIES     = "cookies.txt"
os.makedirs(TMP_DIR, exist_ok=True)


async def ig_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_maintenance():
        await update.message.reply_text(MAINTENANCE_TEXT, parse_mode="Markdown")
        return
    context.user_data[WAITING_KEY] = "instagram"
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="dl_home")]]
    sent = await update.message.reply_text(
        "📸 *Instagram Downloader*\n\n"
        "Supported: Videos, Reels, Posts\n\n"
        "Please send me the Instagram link:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    context.user_data["waiting_msg_id"]  = sent.message_id
    context.user_data["waiting_chat_id"] = sent.chat.id


async def download_instagram(url: str) -> dict:
    uid      = uuid.uuid4().hex
    out_tmpl = os.path.join(TMP_DIR, f"ig_{uid}.%(ext)s")

    ydl_opts = {
        "outtmpl":             out_tmpl,
        "format":              "bestvideo[ext=mp4][filesize<45M]+bestaudio/best[ext=mp4][filesize<45M]/best",
        "merge_output_format": "mp4",
        "quiet":               True,
        "no_warnings":         True,
        "noplaylist":          True,
        "cookiefile":          COOKIES,
        "http_headers": {
            "User-Agent":      "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    loop = asyncio.get_event_loop()

    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    info = await loop.run_in_executor(None, _run)

    file_path = None
    for f in os.listdir(TMP_DIR):
        if f.startswith(f"ig_{uid}"):
            file_path = os.path.join(TMP_DIR, f)
            break

    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError("Downloaded file not found.")

    raw_dur  = info.get("duration", 0)
    duration = f"{int(raw_dur)//60}:{int(raw_dur)%60:02d}"
    size_mb  = os.path.getsize(file_path) / (1024 * 1024)

    increment_stat("instagram")

    return {
        "file_path": file_path,
        "title":     info.get("title", "Instagram Video"),
        "duration":  duration,
        "size":      f"{size_mb:.1f} MB",
    }
