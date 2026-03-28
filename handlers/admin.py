"""
╔══════════════════════════════════════════╗
║       DOWNLOADER X — ADMIN PANEL         ║
║  /admin command + inline admin buttons   ║
║  Author    : Md. Mainul Islam            ║
║  Copyright : (c) 2026 MAINUL - X        ║
╚══════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import OWNER_ID, BOT_NAME, COPYRIGHT

logger = logging.getLogger("DownloaderX.admin")

# Simple in-memory stats (resets on bot restart — replace with DB for persistence)
_stats = {
    "total_downloads": 0,
    "youtube": 0,
    "facebook": 0,
    "instagram": 0,
    "tiktok": 0,
}


def increment_stat(platform: str) -> None:
    """Called by platform downloaders after a successful download."""
    _stats["total_downloads"] += 1
    if platform in _stats:
        _stats[platform] += 1


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def _admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats",       callback_data="admin_stats"),
            InlineKeyboardButton("🔄 Reset Stats", callback_data="admin_reset_stats"),
        ],
        [
            InlineKeyboardButton("📋 Commands",    callback_data="admin_commands"),
            InlineKeyboardButton("ℹ️ Bot Info",    callback_data="admin_info"),
        ],
        [InlineKeyboardButton("🏠 Back to Home",   callback_data="dl_home")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# /admin command
# ─────────────────────────────────────────────────────────────────────────────
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    if not _is_owner(user.id):
        await update.message.reply_text(
            "🚫 *Access Denied.*\n\nThis panel is for the bot owner only.",
            parse_mode="Markdown",
        )
        return

    text = (
        "🛠️ *Admin Panel — Downloader X*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Welcome back, Boss! 👋\n"
        "Choose an option below:\n\n"
        f"_{COPYRIGHT}_"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=_admin_keyboard(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Inline button callbacks  (admin_*)
# ─────────────────────────────────────────────────────────────────────────────
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user  = query.from_user
    await query.answer()

    if not _is_owner(user.id):
        await query.answer("🚫 Access Denied.", show_alert=True)
        return

    data = query.data

    # ── Stats ─────────────────────────────────────────────────────────────────
    if data == "admin_stats":
        text = (
            "📊 *Download Statistics*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 Total Downloads : `{_stats['total_downloads']}`\n\n"
            f"▶️ YouTube   : `{_stats['youtube']}`\n"
            f"📘 Facebook  : `{_stats['facebook']}`\n"
            f"📸 Instagram : `{_stats['instagram']}`\n"
            f"🎵 TikTok    : `{_stats['tiktok']}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"_{COPYRIGHT}_"
        )
        await query.message.edit_text(
            text, parse_mode="Markdown", reply_markup=_admin_keyboard()
        )

    # ── Reset Stats ───────────────────────────────────────────────────────────
    elif data == "admin_reset_stats":
        for key in _stats:
            _stats[key] = 0
        await query.message.edit_text(
            "✅ *Stats have been reset!*\n\n"
            f"_{COPYRIGHT}_",
            parse_mode="Markdown",
            reply_markup=_admin_keyboard(),
        )

    # ── Commands list ─────────────────────────────────────────────────────────
    elif data == "admin_commands":
        text = (
            "📋 *All Bot Commands*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👤 *User Commands:*\n"
            "  /start — Welcome message\n"
            "  /help  — Help guide\n"
            "  /dev   — Developer info\n"
            "  /yt    — YouTube download\n"
            "  /fb    — Facebook download\n"
            "  /ig    — Instagram download\n"
            "  /tt    — TikTok download\n\n"
            "🛠️ *Admin Commands:*\n"
            "  /admin — Open admin panel\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"_{COPYRIGHT}_"
        )
        await query.message.edit_text(
            text, parse_mode="Markdown", reply_markup=_admin_keyboard()
        )

    # ── Bot Info ──────────────────────────────────────────────────────────────
    elif data == "admin_info":
        text = (
            f"ℹ️ *Bot Information*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Bot Name  :* {BOT_NAME}\n"
            f"👨‍💻 *Developer :* Md. Mainul Islam\n"
            f"🏷️ *Brand     :* MAINUL - X\n"
            f"📜 *License   :* MIT License\n"
            f"🔧 *Framework :* python-telegram-bot v20+\n"
            f"⚙️ *Downloader:* yt-dlp\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"_{COPYRIGHT}_"
        )
        await query.message.edit_text(
            text, parse_mode="Markdown", reply_markup=_admin_keyboard()
        )
