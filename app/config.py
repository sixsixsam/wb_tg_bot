# config.py

import os

# ---------- Telegram ----------
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")

# USER — читает
USER_SESSION_NAME = "price_reposter_user"

# BOT — публикует
BOT_SESSION_NAME = "price_reposter_bot"
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ---------- Каналы ----------
SOURCE_CHANNELS = os.getenv("SOURCE_CHANNELS", "").split(",") if os.getenv("SOURCE_CHANNELS") else []
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "")

# ---------- Цены ----------
PRICE_PRO_DELTA = 2000.0
PRICE_DEFAULT_DELTA = 1000.0
MIN_PRICE_TO_ZERO = True
MIN_PRICE_TO_IGNORE = float(os.getenv("MIN_PRICE_TO_IGNORE", 10000.0))

# ---------- Тайминги ----------
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", 0.45))
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
DOWNLOAD_RETRIES = int(os.getenv("DOWNLOAD_RETRIES", 3))
ALBUM_BUFFER_DELAY = float(os.getenv("ALBUM_BUFFER_DELAY", 1.0))

# ---------- Backfill ----------
BACKFILL_LIMIT = int(os.getenv("BACKFILL_LIMIT", 50))

# ---------- Логи ----------
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5

# ---------- Админ ----------
ADMIN_BIND_HOST = os.getenv("ADMIN_BIND_HOST", "127.0.0.1")
ADMIN_BIND_PORT = int(os.getenv("ADMIN_BIND_PORT", 8000))
ADMIN_BASIC_USERNAME = os.getenv("ADMIN_BASIC_USERNAME", "admin")
ADMIN_BASIC_PASSWORD = os.getenv("ADMIN_BASIC_PASSWORD", "changeme")

# ---------- Фильтры ----------
DATE_START_REQUIRED = True

INFO_KEYWORDS = [
    "официальный аккаунт", "отдел продаж", "оптовая торговля",
    "гарантийный сервис", "ежедневно", "г. москва",
    "контак", "📟", "+7", "телефон"
]

RECENT_MESSAGES_LIMIT = int(os.getenv("RECENT_MESSAGES_LIMIT", 500))
