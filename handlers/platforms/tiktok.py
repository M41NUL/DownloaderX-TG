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
from handlers.admin import increment_stat, is_maintenance
from config import MAINTENANCE_TEXT

logger = logging.getLogger("DownloaderX.tiktok")

WAITING_KEY = "waiting_platform"
TMP_DIR     = "downloads"
COOKIES     = "cookies.txt"

os.makedirs(TMP_DIR, exist_ok=True)


async def tt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_maintenance():
        await update.message.reply_text(MAINTENANCE_TEXT, parse_mode="Markdown")
        return

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


    fmt = (
        "download_addr-0"          
        "/play_addr-0"             
        "/best[ext=mp4][acodec!=none]"  
        "/best[acodec!=none]"      
        "/best[ext=mp4]"           
        "/best"
    )

    ydl_opts = {
        "outtmpl":            out_tmpl,
        "format":             fmt,
        "quiet":              True,
        "no_warnings":        True,
        "noplaylist":         True,
        "cookiefile":         COOKIES if os.path.exists(COOKIES) else None,
        "nocheckcertificate": True,
        "retries":            10,
        "fragment_retries":   10,
        "http_headers": {
            "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
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
    except yt_dlp.utils.DownloadError as e:
        err = str(e)
        logger.error(f"[TikTok] DownloadError: {err}")
        raise RuntimeError(f"❌ TikTok download failed!\n\n`{err[:200]}`")


    file_path = None
    for f in sorted(os.listdir(TMP_DIR)):
        if f.startswith(f"tt_{uid}") and not f.endswith(".part"):
            file_path = os.path.join(TMP_DIR, f)
            break

    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError("Downloaded file not found.")

    raw_dur  = info.get("duration", 0) or 0
    duration = f"{int(raw_dur) // 60}:{int(raw_dur) % 60:02d}"
    size_mb  = os.path.getsize(file_path) / (1024 * 1024)

    increment_stat("tiktok")

    return {
        "file_path": file_path,
        "title":     info.get("title", "TikTok Video"),
        "duration":  duration,
        "size":      f"{size_mb:.1f} MB",
    }
