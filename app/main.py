# app/main.py
import asyncio
import threading
import traceback
import re
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
user_client = Client(
    config.USER_SESSION_NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    workdir="."
)

bot_client = Client(
    config.BOT_SESSION_NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    workdir="."
)

# ================= REGEX / CONST =================
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

    new_text, changed = replace_prices_in_text(
        text=text,
        pro_delta=config.PRICE_PRO_DELTA,
        default_delta=config.PRICE_DEFAULT_DELTA,
        min_zero=config.MIN_PRICE_TO_ZERO,
        min_ignore=config.MIN_PRICE_TO_IGNORE
    )

    new_text = new_text.strip()
    if not new_text:
        logger.warning(f"EMPTY AFTER CLEAN {msg.id}")
        return

    old_target_id = await db.get_message_target(str(msg.chat.id), msg.id)
    kb = build_keyboard()

    media_file = None
    try:
        if msg.photo:
            media_file = await download_media(msg)
            if old_target_id:
                sent = await safe(
                    bot_client.edit_message_caption,
                    config.TARGET_CHANNEL,
                    old_target_id,
                    new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            else:
                sent = await safe(
                    bot_client.send_photo,
                    config.TARGET_CHANNEL,
                    media_file,
                    caption=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )

        elif msg.video:
            media_file = await download_media(msg)
            if old_target_id:
                sent = await safe(
                    bot_client.edit_message_caption,
                    config.TARGET_CHANNEL,
                    old_target_id,
                    new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            else:
                sent = await safe(
                    bot_client.send_video,
                    config.TARGET_CHANNEL,
                    media_file,
                    caption=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )

        else:
            if old_target_id:
                sent = await safe(
                    bot_client.edit_message_text,
                    config.TARGET_CHANNEL,
                    old_target_id,
                    new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
            else:
                sent = await safe(
                    bot_client.send_message,
                    config.TARGET_CHANNEL,
                    new_text,
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
            logger.info(f"SENT {msg.id} → {sent.id}")

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
    await db.init_db()
    await user_client.start()
    await bot_client.start()

    for src in config.SOURCE_CHANNELS:
        logger.info(f"BACKFILL {src}")
        msgs = []
        async for m in user_client.get_chat_history(src, limit=config.BACKFILL_LIMIT):
            msgs.append(m)

        msgs.reverse()
        for m in msgs:
            await process_message(m)
            await asyncio.sleep(config.REQUEST_DELAY)

    logger.info("DONE")

    await user_client.stop()
    await bot_client.stop()

if __name__ == "__main__":
    asyncio.run(main())
