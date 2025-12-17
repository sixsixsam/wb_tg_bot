# app/main.py
import asyncio
import threading
import traceback
import re
import os
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, RPCError

from fastapi import FastAPI
import uvicorn

from . import config, db
from .logger import logger
from .utils_price import replace_prices_in_text
from .utils_media import download_media, cleanup_files

# ================= FASTAPI =================
api = FastAPI()

@api.get("/ping")
async def ping():
    return {"status": "ok"}

def start_fastapi():
    uvicorn.run(api, host="0.0.0.0", port=config.ADMIN_BIND_PORT)

threading.Thread(target=start_fastapi, daemon=True).start()

# ================= CLIENTS =================
# РАЗДЕЛ ИСПРАВЛЕН: Явные пути к файлам сессий
# Получаем абсолютный путь к папке, где лежит main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"[DEBUG] Base directory: {BASE_DIR}")
print(f"[DEBUG] Files in base dir: {os.listdir(BASE_DIR)}")

# Для user_client - файл сессии будет в app/user.session
USER_SESSION_PATH = os.path.join(BASE_DIR, config.USER_SESSION_NAME)
print(f"[DEBUG] User session path: {USER_SESSION_PATH}.session")
print(f"[DEBUG] User session exists: {os.path.exists(USER_SESSION_PATH + '.session')}")

user_client = Client(
    name=USER_SESSION_PATH,  # Явный путь к файлу сессии (без расширения .session)
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    workdir=BASE_DIR  # Рабочая директория = папка app/
)

# Для bot_client - если используем токен, то файл сессии не нужен
BOT_SESSION_PATH = os.path.join(BASE_DIR, config.BOT_SESSION_NAME) if hasattr(config, 'BOT_SESSION_NAME') else None

bot_client = Client(
    name=BOT_SESSION_PATH if BOT_SESSION_PATH else config.BOT_SESSION_NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN if hasattr(config, 'BOT_TOKEN') else None,
    workdir=BASE_DIR
)

# ================= REGEX =================
DATE_RE = re.compile(r"^\s*\d{1,2}[./-]\d{1,2}[./-]\d{4}")

# ================= HELPERS =================
def has_date_start(text: str) -> bool:
    return bool(text and DATE_RE.match(text.strip()))

def clean_text(text: str) -> str:
    if not text:
        return ""

    junk_patterns = [
        r"Аксессуар(?:ы)?/ Фото/ Описание ⬇️",
        r"@BSAAccessories"
    ]

    for pattern in junk_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def build_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Заказать", url="https://t.me/linfortepiano")]]
    )

async def safe(func, *args, **kwargs):
    while True:
        try:
            return await func(*args, **kwargs)
        except FloodWait as fw:
            logger.warning(f"FloodWait {fw.value}s")
            await asyncio.sleep(fw.value)
        except RPCError as e:
            logger.error(f"RPCError: {e}")
            return None

# ================= CORE =================
async def process_message(msg: Message):
    raw = (msg.text or "") + (msg.caption or "")
    logger.info(f"PROCESS {msg.id}")

    if not has_date_start(raw):
        logger.info(f"SKIP {msg.id} (no date)")
        return

    text = clean_text(raw)

    new_text, _ = replace_prices_in_text(
        text=text,
        pro_delta=config.PRICE_PRO_DELTA,
        default_delta=config.PRICE_DEFAULT_DELTA,
        min_zero=config.MIN_PRICE_TO_ZERO,
        min_ignore=config.MIN_PRICE_TO_IGNORE
    )

    if not new_text.strip():
        return

    old_target_id = await db.get_message_target(str(msg.chat.id), msg.id)
    kb = build_keyboard()
    media_file = None

    try:
        if msg.photo:
            media_file = await download_media(msg)
            if old_target_id:
                # Редактируем существующее сообщение
                sent = await safe(
                    bot_client.edit_message_caption,
                    chat_id=config.TARGET_CHANNEL,
                    message_id=old_target_id,
                    caption=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            else:
                # Отправляем новое сообщение
                sent = await safe(
                    bot_client.send_photo,
                    chat_id=config.TARGET_CHANNEL,
                    photo=media_file,
                    caption=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                
        elif msg.video:
            media_file = await download_media(msg)
            if old_target_id:
                # Редактируем существующее сообщение
                sent = await safe(
                    bot_client.edit_message_caption,
                    chat_id=config.TARGET_CHANNEL,
                    message_id=old_target_id,
                    caption=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            else:
                # Отправляем новое сообщение
                sent = await safe(
                    bot_client.send_video,
                    chat_id=config.TARGET_CHANNEL,
                    video=media_file,
                    caption=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
        else:
            if old_target_id:
                # Редактируем существующее текстовое сообщение
                sent = await safe(
                    bot_client.edit_message_text,
                    chat_id=config.TARGET_CHANNEL,
                    message_id=old_target_id,
                    text=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            else:
                # Отправляем новое текстовое сообщение
                sent = await safe(
                    bot_client.send_message,
                    chat_id=config.TARGET_CHANNEL,
                    text=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )

        if sent:
            await db.update_message_target(
                str(msg.chat.id),
                msg.id,
                sent.id,
                datetime.utcnow().isoformat(),
                new_text[:800]
            )

    except Exception:
        logger.error(traceback.format_exc())
    finally:
        if media_file:
            cleanup_files([media_file])

# ================= HANDLERS =================
@user_client.on_message(filters.chat(config.SOURCE_CHANNELS))
async def on_new(_, msg: Message):
    await process_message(msg)

@user_client.on_edited_message(filters.chat(config.SOURCE_CHANNELS))
async def on_edit(_, msg: Message):
    await process_message(msg)

# ================= START =================
async def main():
    print("[DEBUG] Starting main()...")
    
    # Дополнительная проверка перед стартом
    user_session_file = USER_SESSION_PATH + '.session'
    print(f"[DEBUG] Final check - User session file: {user_session_file}")
    print(f"[DEBUG] File exists: {os.path.exists(user_session_file)}")
    
    if os.path.exists(user_session_file):
        print(f"[DEBUG] File size: {os.path.getsize(user_session_file)} bytes")
        with open(user_session_file, 'rb') as f:
            header = f.read(6)
            print(f"[DEBUG] File header: {header.hex()} (should be '53514c697465' for SQLite)")
    else:
        print(f"[DEBUG] ERROR: Session file not found at expected location!")
        print(f"[DEBUG] Current directory: {os.getcwd()}")
        print(f"[DEBUG] Files in current dir: {os.listdir('.')}")
        print(f"[DEBUG] Files in app dir: {os.listdir(BASE_DIR) if BASE_DIR != '.' else 'same as current'}")
    
    await db.init_db()
    
    print("[DEBUG] Starting user_client...")
    await user_client.start()
    print("[DEBUG] User client started successfully!")
    
    print("[DEBUG] Starting bot_client...")
    await bot_client.start()
    print("[DEBUG] Bot client started successfully!")

    for src in config.SOURCE_CHANNELS:
        logger.info(f"BACKFILL {src}")
        async for m in user_client.get_chat_history(src, limit=config.BACKFILL_LIMIT):
            await process_message(m)
            await asyncio.sleep(config.REQUEST_DELAY)

    logger.info("DONE")
    
    # Корректная остановка
    try:
        await user_client.stop()
        await bot_client.stop()
    except RuntimeError as e:
        logger.warning(f"Ignoring stop error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
