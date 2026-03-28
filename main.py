"""
╔══════════════════════════════════════════╗
║         DOWNLOADER X — MAIN              ║
║  Author    : Md. Mainul Islam            ║
║  Owner     : MAINUL - X                 ║
║  GitHub    : github.com/M41NUL          ║
║  License   : MIT License                ║
║  Copyright : (c) 2026 MAINUL - X        ║
╚══════════════════════════════════════════╝
"""

import logging
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config import BOT_TOKEN

# ── Handlers ──────────────────────────────────────────────────────────────────
from handlers.logic       import handle_start, handle_help, handle_dev
from handlers.admin       import handle_admin, admin_callback
from handlers.auto_detect import auto_detect_handler
from handlers.downloads   import download_callback

from handlers.platforms.youtube   import yt_command
from handlers.platforms.facebook  import fb_command
from handlers.platforms.instagram import ig_command
from handlers.platforms.tiktok    import tt_command

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("DownloaderX.main")


async def main() -> None:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # ── Commands ──────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",  handle_start))
    app.add_handler(CommandHandler("help",   handle_help))
    app.add_handler(CommandHandler("dev",    handle_dev))
    app.add_handler(CommandHandler("admin",  handle_admin))
    app.add_handler(CommandHandler("yt",     yt_command))
    app.add_handler(CommandHandler("fb",     fb_command))
    app.add_handler(CommandHandler("ig",     ig_command))
    app.add_handler(CommandHandler("tt",     tt_command))

    # ── Inline Button Callbacks ───────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(download_callback, pattern="^dl_"))
    app.add_handler(CallbackQueryHandler(admin_callback,    pattern="^admin_"))

    # ── Auto-Detect: plain text messages (URLs) ───────────────────────────────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, auto_detect_handler),
        group=1,
    )

    logger.info("✅ Downloader X is running...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )

    # Run forever
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
