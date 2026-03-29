"""
╔══════════════════════════════════════════╗
║      DOWNLOADER X — TIKTOK PLATFORM      ║
║  /tt command + yt-dlp downloader         ║
║  Videos, Photos, Slideshows supported    ║
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

logger = logging.getLogger("DownloaderX.tiktok")
WAITING_KEY = "waiting_platform"
TMP_DIR     = "downloads"
COOKIES     = "cookies.txt"
os.makedirs(TMP_DIR, exist_ok=True)


async def tt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[WAITING_KEY] = "tiktok"
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="dl_home")]]
    sent = await update.message.reply_text(
        "🎵 *TikTok Downloader*\n\n"
        "Supported: Videos, Photos, Slideshows\n\n"
        "Please send me the TikTok link:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    context.user_data["waiting_msg_id"]  = sent.message_id
    context.user_data["waiting_chat_id"] = sent.chat.id


async def download_tiktok(url: str) -> dict:
    uid      = uuid.uuid4().hex
    out_tmpl = os.path.join(TMP_DIR, f"tt_{uid}.%(ext)s")

    ydl_opts = {
        "outtmpl":             out_tmpl,
        "format":              "bestvideo[vcodec!=h265][filesize<45M]+bestaudio/best[filesize<45M]/best",
        "merge_output_format": "mp4",
        "quiet":               True,
        "no_warnings":         True,
        "noplaylist":          True,
        "cookiefile":          COOKIES,
        "http_headers": {
            "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer":         "https://www.tiktok.com/",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    loop = asyncio.get_event_loop()

    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info = await loop.run_in_executor(None, _run)
    except Exception:
        # Fallback without format filter
        ydl_opts["format"] = "best"
        def _fallback():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)
        info = await loop.run_in_executor(None, _fallback)

    file_path = None
    for f in os.listdir(TMP_DIR):
        if f.startswith(f"tt_{uid}"):
            file_path = os.path.join(TMP_DIR, f)
            break

    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError("Downloaded file not found.")

    raw_dur  = info.get("duration", 0)
    duration = f"{int(raw_dur)//60}:{int(raw_dur)%60:02d}"
    size_mb  = os.path.getsize(file_path) / (1024 * 1024)

    increment_stat("tiktok")

    return {
        "file_path": file_path,
        "title":     info.get("title", "TikTok Video"),
        "duration":  duration,
        "size":      f"{size_mb:.1f} MB",
    }
