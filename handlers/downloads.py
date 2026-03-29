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
from telegram import Update
from telegram.ext import ContextTypes
from config import BOT_NAME, GITHUB_URL, VIDEO_DELETE_DELAY, PROCESSING_EDIT_DELAY
from handlers.platforms.youtube   import download_youtube
from handlers.platforms.facebook  import download_facebook
from handlers.platforms.instagram import download_instagram
from handlers.platforms.tiktok    import download_tiktok

logger = logging.getLogger("DownloaderX.downloads")

WAITING_KEY = "waiting_platform"

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

# ── Spinner frames (download চলাকালীন) ───────────────────────────────────────
SPINNER_FRAMES = ["⏳", "⌛", "⏳", "⌛"]


# ── Inline button callback ────────────────────────────────────────────────────
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "dl_home":
        from handlers.logic import handle_start
        await query.message.delete()
        await handle_start(update, context)
        return

    if data.startswith("dl_platform_"):
        platform = data.replace("dl_platform_", "")
        context.user_data[WAITING_KEY] = platform

        platform_label = PLATFORM_EMOJI.get(platform, platform.title())
        sent = await query.message.reply_text(
            f"🔗 *{platform_label} Download*\n\n"
            f"Please send me the video link now.",
            parse_mode="Markdown",
        )
        context.user_data["waiting_msg_id"]  = sent.message_id
        context.user_data["waiting_chat_id"] = sent.chat.id
        return


# ── Core download ─────────────────────────────────────────────────────────────
async def process_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    platform: str,
    url: str,
) -> None:
    chat_id        = update.effective_chat.id
    platform_label = PLATFORM_EMOJI.get(platform, platform.title())

    # ── Step 1: Processing message পাঠাও ─────────────────────────────────────
    proc_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"📥 *Downloading from {platform_label}*\n\n"
            f"⏳ Please wait..."
        ),
        parse_mode="Markdown",
    )

    # ── Step 2: Download + spinner একসাথে চালাও ──────────────────────────────
    downloader = DOWNLOADER_MAP.get(platform)
    if not downloader:
        await proc_msg.edit_text("❌ Unsupported platform.")
        return

    # Download task
    download_task = asyncio.create_task(downloader(url))

    # Spinner task — download শেষ না হওয়া পর্যন্ত চলবে
    async def _spinner():
        i = 0
        while not download_task.done():
            frame = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
            try:
                await proc_msg.edit_text(
                    f"📥 *Downloading from {platform_label}*\n\n"
                    f"{frame} Please wait...",
                    parse_mode="Markdown",
                )
            except Exception:
                pass
            await asyncio.sleep(PROCESSING_EDIT_DELAY)
            i += 1

    spinner_task = asyncio.create_task(_spinner())

    # Download শেষ হওয়ার জন্য অপেক্ষা করো
    try:
        result = await download_task
    except Exception as e:
        spinner_task.cancel()
        logger.error(f"Download error [{platform}]: {e}")
        await proc_msg.edit_text(
            f"❌ *Download failed!*\n\n`{e}`",
            parse_mode="Markdown",
        )
        return
    finally:
        spinner_task.cancel()

    # ── Step 3: Processing message delete করো ────────────────────────────────
    try:
        await proc_msg.delete()
    except Exception:
        pass

    # ── Step 4: Video পাঠাও ──────────────────────────────────────────────────
    title     = result.get("title", "N/A")
    caption   = (
        f"✅ *Download Complete!*\n\n"
        f"🎬 *Title*\n"
        f"`{title}`\n\n"
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
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
