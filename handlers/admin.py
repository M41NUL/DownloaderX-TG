"""
╔══════════════════════════════════════════╗
║       DOWNLOADER X — ADMIN PANEL         ║
║  /admin command + inline admin buttons   ║
║  Author    : Md. Mainul Islam            ║
║  Copyright : (c) 2026 MAINUL - X        ║
╚══════════════════════════════════════════╝
"""

import logging
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import OWNER_ID, BOT_NAME, COPYRIGHT

logger = logging.getLogger("DownloaderX.admin")

# ── In-memory storage ─────────────────────────────────────────────────────────
_stats = {
    "total_downloads": 0,
    "youtube":         0,
    "facebook":        0,
    "instagram":       0,
    "tiktok":          0,
    "today":           0,
    "today_date":      str(date.today()),
}

_users: dict       = {}
_banned: set       = set()
_logs: list        = []
_maintenance: bool = False


# ── Public helpers ────────────────────────────────────────────────────────────
def increment_stat(platform: str) -> None:
    today = str(date.today())
    if _stats["today_date"] != today:
        _stats["today"] = 0
        _stats["today_date"] = today
    _stats["total_downloads"] += 1
    _stats["today"] += 1
    if platform in _stats:
        _stats[platform] += 1


def register_user(user) -> None:
    if user.id not in _users:
        _users[user.id] = {
            "name":     user.full_name,
            "username": f"@{user.username}" if user.username else "N/A",
            "joined":   datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        _add_log(f"New user: {user.full_name} (ID: {user.id})")


def add_download_log(platform: str, title: str, user_id: int) -> None:
    _add_log(f"[{platform.upper()}] {title[:40]} — User {user_id}")


def is_banned(user_id: int) -> bool:
    return user_id in _banned


def is_maintenance() -> bool:
    return _maintenance


def _add_log(text: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    _logs.append(f"[{ts}] {text}")
    if len(_logs) > 20:
        _logs.pop(0)


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


# ── Keyboards ─────────────────────────────────────────────────────────────────
def _admin_keyboard() -> InlineKeyboardMarkup:
    maint_label = "🔴 Maintenance: ON" if _maintenance else "🟢 Maintenance: OFF"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats",        callback_data="admin_stats"),
            InlineKeyboardButton("🔄 Reset Stats",  callback_data="admin_reset_stats"),
        ],
        [
            InlineKeyboardButton("👥 Users",        callback_data="admin_users"),
            InlineKeyboardButton("🚫 Banned",       callback_data="admin_banned"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast",    callback_data="admin_broadcast"),
            InlineKeyboardButton("📋 Logs",         callback_data="admin_logs"),
        ],
        [
            InlineKeyboardButton(maint_label,       callback_data="admin_maintenance"),
        ],
        [
            InlineKeyboardButton("📋 Commands",     callback_data="admin_commands"),
            InlineKeyboardButton("ℹ️ Bot Info",     callback_data="admin_info"),
        ],
        [InlineKeyboardButton("🏠 Back to Home",    callback_data="dl_home")],
    ])


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Back to Admin", callback_data="admin_back")]
    ])


# ── /admin command ────────────────────────────────────────────────────────────
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not _is_owner(user.id):
        await update.message.reply_text(
            "🚫 *Access Denied.*\n\nThis panel is for the bot owner only.",
            parse_mode="Markdown",
        )
        return

    maint_status = "🔴 ON" if _maintenance else "🟢 OFF"
    text = (
        "🛠️ *Admin Panel — Downloader X*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Welcome back, Boss!\n\n"
        f"👥 Total Users    : `{len(_users)}`\n"
        f"📥 Total Downloads: `{_stats['total_downloads']}`\n"
        f"📅 Today          : `{_stats['today']}`\n"
        f"🔧 Maintenance    : {maint_status}\n\n"
        "Choose an option below:\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_{COPYRIGHT}_"
    )
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=_admin_keyboard()
    )


# ── New user notification ─────────────────────────────────────────────────────
async def notify_new_user(context: ContextTypes.DEFAULT_TYPE, user) -> None:
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                f"🆕 *New User Joined!*\n\n"
                f"👤 Name     : {user.full_name}\n"
                f"🆔 ID       : `{user.id}`\n"
                f"📛 Username : @{user.username or 'N/A'}\n"
                f"⏰ Time     : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"👥 Total Users: `{len(_users)}`"
            ),
            parse_mode="Markdown",
        )
    except Exception:
        pass


# ── Callback handler ──────────────────────────────────────────────────────────
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global _maintenance
    query = update.callback_query
    user  = query.from_user
    await query.answer()

    if not _is_owner(user.id):
        await query.answer("🚫 Access Denied.", show_alert=True)
        return

    data = query.data

    def _panel_text():
        maint_status = "🔴 ON" if _maintenance else "🟢 OFF"
        return (
            "🛠️ *Admin Panel — Downloader X*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👋 Welcome back, Boss!\n\n"
            f"👥 Total Users    : `{len(_users)}`\n"
            f"📥 Total Downloads: `{_stats['total_downloads']}`\n"
            f"📅 Today          : `{_stats['today']}`\n"
            f"🔧 Maintenance    : {maint_status}\n\n"
            "Choose an option below:\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"_{COPYRIGHT}_"
        )

    if data == "admin_back":
        await query.message.edit_text(
            _panel_text(), parse_mode="Markdown", reply_markup=_admin_keyboard()
        )

    elif data == "admin_stats":
        text = (
            "📊 *Download Statistics*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 Total Downloads : `{_stats['total_downloads']}`\n"
            f"📅 Today           : `{_stats['today']}`\n\n"
            f"▶️ YouTube   : `{_stats['youtube']}`\n"
            f"📘 Facebook  : `{_stats['facebook']}`\n"
            f"📸 Instagram : `{_stats['instagram']}`\n"
            f"🎵 TikTok    : `{_stats['tiktok']}`\n\n"
            f"👥 Total Users : `{len(_users)}`\n"
            f"🚫 Banned      : `{len(_banned)}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"_{COPYRIGHT}_"
        )
        await query.message.edit_text(
            text, parse_mode="Markdown", reply_markup=_back_keyboard()
        )

    elif data == "admin_reset_stats":
        for key in _stats:
            if key != "today_date":
                _stats[key] = 0
        _stats["today_date"] = str(date.today())
        _add_log("Stats reset by admin")
        await query.message.edit_text(
            "✅ *All stats have been reset!*\n\n" + f"_{COPYRIGHT}_",
            parse_mode="Markdown",
            reply_markup=_back_keyboard(),
        )

    elif data == "admin_users":
        if not _users:
            text = "👥 *No users yet.*"
        else:
            lines = [f"👥 *All Users* — Total: `{len(_users)}`\n\n━━━━━━━━━━━━━━━━━━━━━━"]
            for uid, info in list(_users.items())[-15:]:
                banned_tag = " 🚫" if uid in _banned else ""
                lines.append(
                    f"👤 {info['name']}{banned_tag}\n"
                    f"   🆔 `{uid}` | {info['username']}\n"
                    f"   ⏰ {info['joined']}"
                )
            text = "\n\n".join(lines)
        ban_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🚫 Ban User",   callback_data="admin_ban_prompt"),
                InlineKeyboardButton("✅ Unban User", callback_data="admin_unban_prompt"),
            ],
            [InlineKeyboardButton("◀️ Back to Admin", callback_data="admin_back")],
        ])
        await query.message.edit_text(
            text, parse_mode="Markdown", reply_markup=ban_keyboard
        )

    elif data == "admin_ban_prompt":
        context.user_data["admin_action"] = "ban"
        await query.message.edit_text(
            "🚫 *Ban User*\n\nPlease send the User ID to ban:",
            parse_mode="Markdown",
            reply_markup=_back_keyboard(),
        )

    elif data == "admin_unban_prompt":
        context.user_data["admin_action"] = "unban"
        await query.message.edit_text(
            "✅ *Unban User*\n\nPlease send the User ID to unban:",
            parse_mode="Markdown",
            reply_markup=_back_keyboard(),
        )

    elif data == "admin_banned":
        if not _banned:
            text = "✅ *No banned users.*"
        else:
            lines = [f"🚫 *Banned Users* — Total: `{len(_banned)}`\n\n━━━━━━━━━━━━━━━━━━━━━━"]
            for uid in _banned:
                info = _users.get(uid)
                name = info["name"] if info else "Unknown"
                lines.append(f"👤 {name}\n   🆔 `{uid}`")
            text = "\n\n".join(lines)
        await query.message.edit_text(
            text, parse_mode="Markdown", reply_markup=_back_keyboard()
        )

    elif data == "admin_broadcast":
        context.user_data["admin_action"] = "broadcast"
        await query.message.edit_text(
            "📢 *Broadcast Message*\n\n"
            f"Total users: `{len(_users)}`\n\n"
            "Please send the message to broadcast:",
            parse_mode="Markdown",
            reply_markup=_back_keyboard(),
        )

    elif data == "admin_logs":
        if not _logs:
            text = "📋 *No logs yet.*"
        else:
            log_text = "\n".join(reversed(_logs[-15:]))
            text = f"📋 *Recent Logs*\n\n━━━━━━━━━━━━━━━━━━━━━━\n`{log_text}`"
        await query.message.edit_text(
            text, parse_mode="Markdown", reply_markup=_back_keyboard()
        )

    elif data == "admin_maintenance":
        _maintenance = not _maintenance
        status = "🔴 ON" if _maintenance else "🟢 OFF"
        _add_log(f"Maintenance mode: {status}")
        await query.answer(f"Maintenance mode: {status}", show_alert=True)
        await query.message.edit_text(
            _panel_text(), parse_mode="Markdown", reply_markup=_admin_keyboard()
        )

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
            text, parse_mode="Markdown", reply_markup=_back_keyboard()
        )

    elif data == "admin_info":
        text = (
            f"ℹ️ *Bot Information*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Bot Name  :* {BOT_NAME}\n"
            f"👨‍💻 *Developer :* Md. Mainul Islam\n"
            f"🏷️ *Brand     :* MAINUL - X\n"
            f"📜 *License   :* MIT License\n"
            f"🔧 *Framework :* python-telegram-bot v21\n"
            f"⚙️ *Downloader:* yt-dlp\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"_{COPYRIGHT}_"
        )
        await query.message.edit_text(
            text, parse_mode="Markdown", reply_markup=_back_keyboard()
        )


# ── Admin message handler (ban/unban/broadcast) ───────────────────────────────
async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if message was handled as admin action."""
    user   = update.effective_user
    action = context.user_data.get("admin_action")

    if not _is_owner(user.id) or not action:
        return False

    text = update.message.text.strip()

    if action == "ban":
        context.user_data.pop("admin_action", None)
        try:
            target_id = int(text)
            _banned.add(target_id)
            info = _users.get(target_id)
            name = info["name"] if info else "Unknown"
            _add_log(f"User banned: {name} ({target_id})")
            await update.message.reply_text(
                f"🚫 *User Banned!*\n\n👤 {name}\n🆔 `{target_id}`",
                parse_mode="Markdown", reply_markup=_back_keyboard(),
            )
        except ValueError:
            await update.message.reply_text("❌ Invalid User ID.", reply_markup=_back_keyboard())
        return True

    elif action == "unban":
        context.user_data.pop("admin_action", None)
        try:
            target_id = int(text)
            if target_id in _banned:
                _banned.discard(target_id)
                _add_log(f"User unbanned: {target_id}")
                await update.message.reply_text(
                    f"✅ *User Unbanned!*\n\n🆔 `{target_id}`",
                    parse_mode="Markdown", reply_markup=_back_keyboard(),
                )
            else:
                await update.message.reply_text(
                    f"⚠️ User `{target_id}` is not banned.",
                    parse_mode="Markdown", reply_markup=_back_keyboard(),
                )
        except ValueError:
            await update.message.reply_text("❌ Invalid User ID.", reply_markup=_back_keyboard())
        return True

    elif action == "broadcast":
        context.user_data.pop("admin_action", None)
        success = failed = 0
        broadcast_text = f"📢 *Message from {BOT_NAME}*\n\n{text}"
        status_msg = await update.message.reply_text(
            f"📢 Broadcasting to `{len(_users)}` users...", parse_mode="Markdown"
        )
        for uid in list(_users.keys()):
            try:
                await context.bot.send_message(
                    chat_id=uid, text=broadcast_text, parse_mode="Markdown"
                )
                success += 1
            except Exception:
                failed += 1
        _add_log(f"Broadcast: {success} success, {failed} failed")
        await status_msg.edit_text(
            f"✅ *Broadcast Complete!*\n\n✔️ Success: `{success}`\n❌ Failed: `{failed}`",
            parse_mode="Markdown", reply_markup=_back_keyboard(),
        )
        return True

    return False
