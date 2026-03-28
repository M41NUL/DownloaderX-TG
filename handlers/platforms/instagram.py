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
from handlers.admin import increment_stat

logger = logging.getLogger("DownloaderX.instagram")
WAITING_KEY = "waiting_platform"
TMP_DIR = "downloads"
os.makedirs(TMP_DIR, exist_ok=True)


async def ig_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[WAITING_KEY] = "instagram"
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="dl_home")]]
    await update.message.reply_text(
        "📸 *Instagram Downloader*\n\n"
        "Supported: Videos, Reels, Posts\n\n"
        "Please send me the Instagram link:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


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
        # Instagram needs specific headers to avoid 403
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT":             "1",
            "Connection":      "keep-alive",
        },
        # Some Instagram videos need this
        "extractor_args": {
            "instagram": {
                "include_feeds": ["reels", "posts"],
            }
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
