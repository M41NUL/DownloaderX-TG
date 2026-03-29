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


def _build_ydl_opts(out_tmpl: str, client: str, has_ffmpeg: bool) -> dict:
    """প্রতিটা client এর জন্য আলাদা opts তৈরি করে।"""

    # Client অনুযায়ী User-Agent
    ua_map = {
        "web":          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/134.0.0.0 Safari/537.36",
        "web_embedded": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/134.0.0.0 Safari/537.36",
        "ios":          "com.google.ios.youtube/19.09.3 (iPhone16,2; U; CPU iOS 17_0 like Mac OS X)",
        "mweb":         "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "tv_embedded":  "Mozilla/5.0 (SMART-TV; Linux; Tizen 5.0) AppleWebKit/537.36 Chrome/79.0.0.0 Safari/537.36",
    }

    opts = {
        "outtmpl":            out_tmpl,
        "format":             "best",
        "format_sort":        ["res:720", "ext:mp4:m4a"],
        "quiet":              True,
        "no_warnings":        True,
        "noplaylist":         True,
        "nocheckcertificate": True,
        "cookiefile":         COOKIES if os.path.exists(COOKIES) else None,

        "extractor_args": {
            "youtube": {
                "player_client": [client],
            }
        },

        "http_headers": {
            "User-Agent": ua_map.get(client, ua_map["web"]),
        },

        "socket_timeout":   30,
        "retries":          5,
        "fragment_retries": 5,
    }

    if has_ffmpeg:
        opts["merge_output_format"] = "mp4"

    return opts


async def download_youtube(url: str) -> dict:
    uid      = uuid.uuid4().hex
    out_tmpl = os.path.join(TMP_DIR, f"yt_{uid}.%(ext)s")
    has_ffmpeg = shutil.which("ffmpeg") is not None

    # ✅ Client fallback list — একটা block হলে পরেরটা try করবে
    clients = ["web", "web_embedded", "ios", "mweb", "tv_embedded"]

    loop = asyncio.get_event_loop()
    info      = None
    last_err  = None

    for client in clients:
        ydl_opts = _build_ydl_opts(out_tmpl, client, has_ffmpeg)

        def _run(opts=ydl_opts):
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)

        try:
            logger.info(f"Trying YouTube client: {client}")
            info = await loop.run_in_executor(None, _run)
            logger.info(f"Success with client: {client}")
            break  # সফল হলে loop থেকে বের হও

        except yt_dlp.utils.DownloadError as e:
            last_err = str(e)
            logger.warning(f"Client [{client}] failed: {last_err[:80]}")

            # Fatal error হলে বাকি client try করার দরকার নেই
            if any(k in last_err for k in ["Private video", "age", "Sign in", "This video is unavailable"]):
                break
            continue

    # সব client fail হলে
    if info is None:
        if last_err:
            if "Sign in" in last_err or "age" in last_err.lower():
                raise RuntimeError("⛔ This video requires login or is age-restricted.")
            elif "private" in last_err.lower():
                raise RuntimeError("🔒 This video is private.")
            elif "unavailable" in last_err.lower():
                raise RuntimeError("❌ This video is unavailable in this region.")
            else:
                raise RuntimeError("❌ YouTube download failed. Please try again later.")
        else:
            raise RuntimeError("❌ Unknown error during download.")

    # ✅ .part ফাইল বাদ দিয়ে সঠিক ফাইল খোঁজা
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
