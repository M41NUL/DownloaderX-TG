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
import time
import threading
import http.server
import socketserver
import os
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
from handlers.admin       import handle_admin, admin_callback, admin_message_handler
from handlers.auto_detect import auto_detect_handler
from handlers.downloads   import download_callback

from handlers.platforms.youtube   import yt_command
from handlers.platforms.facebook  import fb_command
from handlers.platforms.instagram import ig_command
from handlers.platforms.tiktok    import tt_command
start_time = time.time()
def run_server():
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            
            uptime_seconds = int(time.time() - start_time)
            days, rem = divmod(uptime_seconds, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, seconds = divmod(rem, 60)
            
            uptime_string = f"{days}d {hours}h {minutes}m {seconds}s"

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            html = f"""
            <html>
            <head>
                <title>Downloader X Bot Status</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding-top: 100px; background-color: #0e1621; color: white;">
                <div style="border: 2px solid #0088cc; display: inline-block; padding: 30px; border-radius: 15px; background: #17212b; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                    <h1 style="color: #40a7e3; margin-bottom: 10px;">🚀 Downloader X Bot</h1>
                    <p style="font-size: 1.1em; color: #abbecf;">The bot is currently <b>Online</b></p>
                    
                    <div style="background: #242f3d; padding: 10px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #40a7e3;">
                        <span style="color: #8295a5;">Uptime:</span> <span style="color: #fff; font-family: monospace;">{uptime_string}</span>
                    </div>

                    <div style="margin: 20px 0; font-weight: bold; color: #fff;">
                        Developed by: <span style="color: #40a7e3;">MAINUL - X</span>
                    </div>
                    <hr style="border: 0; border-top: 1px solid #2b3948;">
                    <p style="font-size: 0.9em; color: #8295a5;">(c) 2026 MAINUL - X | All Rights Reserved</p>
                    <a href="https://t.me/mdmainulislaminfo" style="display: inline-block; margin-top: 15px; padding: 10px 20px; background-color: #0088cc; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Contact Developer</a>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

    PORT = int(os.environ.get("PORT", 8080))
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

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
    async def smart_message_handler(update, context):
        handled = await admin_message_handler(update, context)
        if not handled:
            await auto_detect_handler(update, context)

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, smart_message_handler),
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
