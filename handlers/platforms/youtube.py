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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]


def _get_cookie_file():
    paths = [
        COOKIES,
        "/opt/render/project/src/cookies.txt",
        os.path.join(os.path.dirname(__file__), "..", "..", "cookies.txt"),
    ]
    for p in paths:
        p = os.path.abspath(p)
        if os.path.exists(p):
            logger.info(f"[YT] Cookies found: {p}")
            return p
    logger.warning("[YT] No cookies.txt found")
    return None


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
    uid         = uuid.uuid4().hex
    out_tmpl    = os.path.join(TMP_DIR, f"yt_{uid}.%(ext)s")
    loop        = asyncio.get_event_loop()
    cookie_file = _get_cookie_file()

    # Format IDs that don't need FFmpeg (pre-merged):
    # 22  = 720p mp4 (video+audio)
    # 18  = 360p mp4 (video+audio)
    # 59  = 480p mp4 (video+audio)
    # 135 = 480p video only (needs ffmpeg) — skip
    # best[ext=mp4][vcodec^=avc1] = H.264 mp4 with audio
    attempts = [
        "22",
        "59",
        "18",
        "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/22/18",
        "best[ext=mp4][vcodec^=avc1]",
        "best[ext=mp4]",
        "best",
        "worst",
    ]

    info       = None
    last_error = None

    for i, fmt in enumerate(attempts):
        ua = USER_AGENTS[i % len(USER_AGENTS)]
        ydl_opts = {
            "outtmpl":            out_tmpl,
            "format":             fmt,
            "quiet":              True,
            "no_warnings":        True,
            "noplaylist":         True,
            "nocheckcertificate": True,
            "ignoreerrors":       False,
            "retries":            3,
            "http_headers": {
                "User-Agent":      ua,
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        def _run(opts=ydl_opts):
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)

        try:
            info = await loop.run_in_executor(None, _run)
            logger.info(f"[YT] ✅ fmt={fmt}")
            break
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[YT] ❌ fmt={fmt}: {str(e)[:100]}")
            continue

    if info is None:
        raise RuntimeError(
            f"❌ Download failed!\n\n`{last_error[:300] if last_error else 'Unknown error'}`"
        )

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
