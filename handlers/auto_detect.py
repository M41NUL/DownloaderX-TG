"""
╔══════════════════════════════════════════╗
║     DOWNLOADER X — AUTO-DETECT HANDLER   ║
║  Detects platform from raw URL messages  ║
║  Author    : Md. Mainul Islam            ║
║  Copyright : (c) 2026 MAINUL - X        ║
╚══════════════════════════════════════════╝

AUTO-DETECT LOGIC:
  ┌─ User sends raw link (no prior command / button)
  │    → detect platform → download → delete detect msg after 2s
  │
  ├─ User clicked a platform button OR used a command
  │    → bot is "waiting for link" → auto-detect is DISABLED for that user
  │    → bot uses the platform already chosen
  │    → after download, waiting state is cleared
  │
  └─ If auto-detect would have fired AND button/command was also pending
       → auto-detect disables itself to avoid duplicate sends
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import PLATFORMS, AUTO_DETECT_DELETE_DELAY
from handlers.downloads import process_download

logger = logging.getLogger("DownloaderX.auto_detect")

# ── user_data keys ────────────────────────────────────────────────────────────
WAITING_KEY   = "waiting_platform"   # set when button/command mode is active
AUTO_DET_KEY  = "auto_detect_active" # True while auto-detect is processing


def _detect_platform(url: str) -> str | None:
    """Return platform name if URL matches, else None."""
    url_lower = url.lower()
    for platform, domains in PLATFORMS.items():
        if any(d in url_lower for d in domains):
            return platform
    return None


def _extract_url(text: str) -> str | None:
    """Pull first token that looks like a URL from the message text."""
    for token in text.split():
        if token.startswith(("http://", "https://")):
            return token
    return None


# ─────────────────────────────────────────────────────────────────────────────
async def auto_detect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles every plain-text message that isn't a command.

    Cases:
      A) Button / command mode active  → forward link to process_download()
         with the already-chosen platform, then clear waiting state.
      B) No waiting state + URL found  → auto-detect path.
      C) No waiting state + no URL     → silently ignore.
    """
    text = (update.message.text or "").strip()
    uid  = update.effective_user.id

    waiting_platform: str | None = context.user_data.get(WAITING_KEY)

    # ── CASE A: button / command mode ─────────────────────────────────────────
    if waiting_platform:
        url = _extract_url(text)
        if not url:
            await update.message.reply_text(
                "⚠️ That doesn't look like a valid link.\n"
                "Please send a proper video URL."
            )
            return

        # Delete waiting message
        msg_id  = context.user_data.pop("waiting_msg_id", None)
        chat_id = context.user_data.pop("waiting_chat_id", None)
        if msg_id and chat_id:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass

        # Clear waiting state BEFORE download so auto-detect won't be suppressed
        # for the next message.
        context.user_data.pop(WAITING_KEY, None)

        await process_download(update, context, platform=waiting_platform, url=url)
        return

    # ── CASE B: auto-detect ───────────────────────────────────────────────────
    url = _extract_url(text)
    if not url:
        return  # plain text, not a URL — ignore silently

    platform = _detect_platform(url)
    if not platform:
        await update.message.reply_text(
            "❌ *Unsupported link.*\n\n"
            "Supported platforms: YouTube, Facebook, Instagram, TikTok.\n"
            "Use /help for more info.",
            parse_mode="Markdown",
        )
        return

    # Guard: if auto-detect is already running for this user, skip
    if context.user_data.get(AUTO_DET_KEY):
        logger.info(f"Auto-detect already active for user {uid}, skipping duplicate.")
        return

    context.user_data[AUTO_DET_KEY] = True

    # ── Send & auto-delete the "detected" notice ──────────────────────────────
    platform_display = {
        "youtube":   "▶️ YouTube",
        "facebook":  "📘 Facebook",
        "instagram": "📸 Instagram",
        "tiktok":    "🎵 TikTok",
    }.get(platform, platform.title())

    notice = await update.message.reply_text(
        f"🔍 *Auto-Detect Successful!*\n"
        f"📡 Platform : *{platform_display}*\n"
        f"⏳ Starting download...",
        parse_mode="Markdown",
    )

    # Schedule notice deletion after AUTO_DETECT_DELETE_DELAY seconds
    async def _delete_notice():
        await asyncio.sleep(AUTO_DETECT_DELETE_DELAY)
        try:
            await notice.delete()
        except Exception:
            pass

    asyncio.create_task(_delete_notice())

    # ── Run the actual download ───────────────────────────────────────────────
    try:
        await process_download(update, context, platform=platform, url=url)
    finally:
        context.user_data[AUTO_DET_KEY] = False
