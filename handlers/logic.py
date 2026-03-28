"""
╔══════════════════════════════════════════╗
║       DOWNLOADER X — LOGIC HANDLER       ║
║  /start  /help  /dev  commands           ║
║  Author    : Md. Mainul Islam            ║
║  Copyright : (c) 2026 MAINUL - X        ║
╚══════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import (
    BOT_NAME, AUTHOR, OWNER_NAME, GITHUB_URL,
    TELEGRAM, WHATSAPP, EMAIL, COPYRIGHT,
)

logger = logging.getLogger("DownloaderX.logic")


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Sends a welcome message with 4 platform download buttons + a Telegram contact button.
    Users can:
      1. Click a platform button → bot asks for link
      2. Send a raw URL → auto-detect kicks in
      3. Use a platform command directly (/yt, /fb, etc.)
    """
    user = update.effective_user
    first = user.first_name or "there"

    text = (
        f"👋 *Welcome, {first}!*\n\n"
        f"🤖 I'm *{BOT_NAME}* — your all-in-one video downloader bot.\n\n"
        "📥 *How to download:*\n"
        "┣ Just send me a video link (auto-detect)\n"
        "┣ Tap a platform button below\n"
        "┗ Or use a command: `/yt` `/fb` `/ig` `/tt`\n\n"
        "🌐 *Supported Platforms:*\n"
        "▸ YouTube  ▸ Facebook  ▸ Instagram  ▸ TikTok\n\n"
        f"_{COPYRIGHT}_"
    )

    keyboard = [
        [
            InlineKeyboardButton("▶️ YouTube",   callback_data="dl_platform_youtube"),
            InlineKeyboardButton("📘 Facebook",  callback_data="dl_platform_facebook"),
        ],
        [
            InlineKeyboardButton("📸 Instagram", callback_data="dl_platform_instagram"),
            InlineKeyboardButton("🎵 TikTok",    callback_data="dl_platform_tiktok"),
        ],
        [
            InlineKeyboardButton("💬 Contact on Telegram", url=f"https://t.me/mdmainulislaminfo"),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    logger.info(f"/start → user {user.id} ({user.username})")


# ─────────────────────────────────────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────────────────────────────────────
async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 *Downloader X — Help Guide*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 *Commands:*\n"
        "  /start — Welcome & platform buttons\n"
        "  /yt    — Download YouTube video\n"
        "  /fb    — Download Facebook video\n"
        "  /ig    — Download Instagram video\n"
        "  /tt    — Download TikTok video\n"
        "  /help  — Show this help message\n"
        "  /dev   — Developer information\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *3 Ways to Download:*\n\n"
        "1️⃣ *Auto-Detect* — Just paste any supported link\n"
        "   Bot will detect platform & download automatically\n\n"
        "2️⃣ *Platform Buttons* — Tap a button from /start\n"
        "   Then send the link when asked\n\n"
        "3️⃣ *Commands* — Use /yt, /fb, /ig, /tt\n"
        "   Then send the link when asked\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ *Supported Sites:*\n"
        "  • YouTube (youtube.com, youtu.be)\n"
        "  • Facebook (facebook.com, fb.watch)\n"
        "  • Instagram (instagram.com)\n"
        "  • TikTok (tiktok.com, vm.tiktok.com)\n\n"
        f"_{COPYRIGHT}_"
    )

    keyboard = [[InlineKeyboardButton("🏠 Back to Home", callback_data="dl_home")]]
    await update.effective_message.reply_text(
    text,
    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(keyboard),
)



# ─────────────────────────────────────────────────────────────────────────────
# /dev
# ─────────────────────────────────────────────────────────────────────────────
async def handle_dev(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👨‍💻 *Developer Information*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧑 *Name     :* {AUTHOR}\n"
        f"🏷️ *Brand    :* {OWNER_NAME}\n"
        f"💻 *GitHub   :* [M41NUL]({GITHUB_URL})\n"
        f"✈️ *Telegram :* {TELEGRAM}\n"
        f"📱 *WhatsApp :* {WHATSAPP}\n"
        f"📧 *Email    :* `githubmainul@gmail.com`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Bot      :* {BOT_NAME}\n"
        f"📜 *License  :* MIT License\n"
        f"_{COPYRIGHT}_"
    )

    keyboard = [
        [
            InlineKeyboardButton("💻 GitHub",   url=GITHUB_URL),
            InlineKeyboardButton("✈️ Telegram", url="https://t.me/mdmainulislaminfo"),
        ],
        [InlineKeyboardButton("🏠 Back to Home", callback_data="dl_home")],
    ]

    await update.effective_message.reply_text(
    text,
    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(keyboard),
)
