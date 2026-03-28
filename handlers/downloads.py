"""
╔══════════════════════════════════════════╗
║      DOWNLOADER X — DOWNLOADS HANDLER    ║
║  Processing bar, video send, captions    ║
║  Author    : Md. Mainul Islam            ║
║  Copyright : (c) 2026 MAINUL - X        ║
╚══════════════════════════════════════════╝
"""

import asyncio
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import BOT_NAME, GITHUB_URL, VIDEO_DELETE_DELAY, PROCESSING_EDIT_DELAY
from handlers.platforms.youtube   import download_youtube
from handlers.platforms.facebook  import download_facebook
from handlers.platforms.instagram import download_instagram
from handlers.platforms.tiktok    import download_tiktok

logger = logging.getLogger("DownloaderX.downloads")

WAITING_KEY = "waiting_platform"

# ── Progress bar frames ───────────────────────────────────────────────────────
PROGRESS_FRAMES = [
    "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜  0%",
    "🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜ 10%",
    "🟩🟩⬜⬜⬜⬜⬜⬜⬜⬜ 20%",
    "🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜ 30%",
    "🟩🟩🟩🟩⬜⬜⬜⬜⬜⬜ 40%",
    "🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50%",
    "🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜ 60%",
    "🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜ 70%",
    "🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜ 80%",
    "🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜ 90%",
    "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% ✅",
]

PLATFORM_EMOJI = {
    "youtube":   "▶️ YouTube",
    "facebook":  "📘 Facebook",
    "instagram": "📸 Instagram",
    "tiktok":    "🎵 TikTok",
}

DOWNLOADER_MAP = {
    "youtube":   download_youtube,
    "facebook":  download_facebook,
    "instagram": download_instagram,
    "tiktok":    download_tiktok,
}


# ─────────────────────────────────────────────────────────────────────────────
# Inline button callback  (dl_platform_youtube / dl_platform_facebook / etc.)
# ─────────────────────────────────────────────────────────────────────────────
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data  # e.g. "dl_platform_youtube"

    # ── Home button ───────────────────────────────────────────────────────────
    if data == "dl_home":
        from handlers.logic import handle_start
        # Fake a message update so handle_start can reply
        await query.message.delete()
        await handle_start(update, context)
        return

    # ── Platform button ───────────────────────────────────────────────────────
    if data.startswith("dl_platform_"):
        platform = data.replace("dl_platform_", "")
        context.user_data[WAITING_KEY] = platform

        platform_label = PLATFORM_EMOJI.get(platform, platform.title())
        await query.message.reply_text(
            f"🔗 *{platform_label} Download*\n\n"
            f"Please send me the video link now.",
            parse_mode="Markdown",
        )
        return


# ─────────────────────────────────────────────────────────────────────────────
# Core download function called by auto_detect + platform commands
# ─────────────────────────────────────────────────────────────────────────────
async def process_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    platform: str,
    url: str,
) -> None:
    """
    1. Send animated processing bar (single message, edited in-place).
    2. Run the platform-specific downloader.
    3. Delete the processing message.
    4. Send the video with a rich caption.
    """
    chat_id  = update.effective_chat.id
    platform_label = PLATFORM_EMOJI.get(platform, platform.title())

    # ── Step 1 : Send processing bar ─────────────────────────────────────────
    proc_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"📥 *Downloading from {platform_label}*\n\n{PROGRESS_FRAMES[0]}",
        parse_mode="Markdown",
    )

    # Animate progress bar
    for frame in PROGRESS_FRAMES[1:]:
        await asyncio.sleep(PROCESSING_EDIT_DELAY)
        try:
            await proc_msg.edit_text(
                f"📥 *Downloading from {platform_label}*\n\n{frame}",
                parse_mode="Markdown",
            )
        except Exception:
            pass

    # ── Step 2 : Call downloader ──────────────────────────────────────────────
    downloader = DOWNLOADER_MAP.get(platform)
    if not downloader:
        await proc_msg.edit_text("❌ Unsupported platform.")
        return

    try:
        result = await downloader(url)
        # result = {
        #   "file_path": str,
        #   "title": str,
        #   "duration": str,   e.g. "3:45"
        #   "size": str,       e.g. "12.4 MB"
        # }
    except Exception as e:
        logger.error(f"Download error [{platform}]: {e}")
        await proc_msg.edit_text(
            f"❌ *Download failed!*\n\n`{e}`",
            parse_mode="Markdown",
        )
        return

    # ── Step 3 : Delete processing message (after short delay) ───────────────
    await asyncio.sleep(VIDEO_DELETE_DELAY)
    try:
        await proc_msg.delete()
    except Exception:
        pass

    # ── Step 4 : Send video + final caption ───────────────────────────────────
    caption = (
        f"✅ *Download Complete!*\n\n"
        f"🎬 *Title     :* {result.get('title', 'N/A')}\n"
        f"⏱️ *Duration  :* {result.get('duration', 'N/A')}\n"
        f"📦 *Size      :* {result.get('size', 'N/A')}\n"
        f"📡 *Platform  :* {platform_label}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Bot       :* {BOT_NAME}\n"
        f"👨‍💻 *Dev       :* [M41NUL]({GITHUB_URL})\n"
        f"_Powered by MAINUL - X_"
    )

    file_path = result.get("file_path")
    try:
        with open(file_path, "rb") as video_file:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption=caption,
                parse_mode="Markdown",
                supports_streaming=True,
            )
    except Exception as e:
        logger.error(f"Failed to send video: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Could not send video.\n`{e}`",
            parse_mode="Markdown",
        )
    finally:
        # Clean up temp file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
