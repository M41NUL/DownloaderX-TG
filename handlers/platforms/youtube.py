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

# Multiple User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
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

    # Attempts: (format, use_po_token, use_cookies, user_agent_index)
    attempts = [
        ("best[height<=720]", True,  cookie_file, 0),
        ("best[height<=720]", True,  cookie_file, 1),
        ("best[height<=480]", True,  cookie_file, 2),
        ("best",              True,  cookie_file, 3),
        ("best[height<=720]", False, cookie_file, 0),
        ("best",              False, cookie_file, 1),
        ("best[height<=720]", True,  None,        0),
        ("best[height<=720]", True,  None,        4),
        ("best",              True,  None,        2),
        ("best[height<=480]", False, None,        1),
        ("best",              False, None,        3),
        ("worst",             False, None,        0),
    ]

    info       = None
    last_error = None

    for fmt, use_po, cookies, ua_idx in attempts:
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
                "User-Agent":      USER_AGENTS[ua_idx],
                "Accept-Language": "en-US,en;q=0.9",
                "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        }

        if cookies:
            ydl_opts["cookiefile"] = cookies

        if use_po:
            ydl_opts["extractor_args"] = {
                "youtube": {
                    "player_client": ["web"],
                    "po_token":      ["web+auto"],
                }
            }

        def _run(opts=ydl_opts):
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)

        try:
            info = await loop.run_in_executor(None, _run)
            logger.info(f"[YT] ✅ fmt={fmt} po={use_po} cookies={'yes' if cookies else 'no'} ua={ua_idx}")
            break
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[YT] ❌ fmt={fmt} ua={ua_idx}: {str(e)[:100]}")
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
