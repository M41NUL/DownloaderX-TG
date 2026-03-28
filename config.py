"""
╔══════════════════════════════════════════╗
║         DOWNLOADER X — CONFIG            ║
║  Author    : Md. Mainul Islam            ║
║  Owner     : MAINUL - X                 ║
║  GitHub    : github.com/M41NUL          ║
║  License   : MIT License                ║
║  Copyright : (c) 2026 MAINUL - X        ║
╚══════════════════════════════════════════╝
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Bot Credentials ───────────────────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID    = int(os.getenv("OWNER_ID", "YOUR_OWNER_TELEGRAM_ID"))

# ── Author Info ───────────────────────────────────────────────────────────────
AUTHOR      = "Md. Mainul Islam"
OWNER_NAME  = "MAINUL - X"
GITHUB      = "M41NUL"
GITHUB_URL  = "https://github.com/M41NUL"
WHATSAPP    = "+8801308850528"
TELEGRAM    = "@mdmainulislaminfo"
EMAIL       = "githubmainul@gmail.com | devmainulislam@gmail.com"
LICENSE     = "MIT License"
COPYRIGHT   = f"Copyright (c) {datetime.now().year} MAINUL - X"
BOT_NAME    = "Downloader X"

# ── Supported Platforms ───────────────────────────────────────────────────────
PLATFORMS = {
    "youtube":   ["youtube.com", "youtu.be"],
    "facebook":  ["facebook.com", "fb.watch", "fb.com"],
    "instagram": ["instagram.com"],
    "tiktok":    ["tiktok.com", "vm.tiktok.com"],
}

# ── Timing (seconds) ──────────────────────────────────────────────────────────
AUTO_DETECT_DELETE_DELAY = 2      # delete "auto detect success" msg
VIDEO_DELETE_DELAY        = 1     # delete "processing" msg after video sent
PROCESSING_EDIT_DELAY     = 1     # time between progress bar edits
