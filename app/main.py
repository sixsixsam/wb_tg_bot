# app/main.py
# Полностью исправленный main.py для Pyrogram + совместимость с REPLIT

import asyncio
import os
import re
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto, InputMediaVideo, InputMediaDocument, Message
)
from pyrogram.errors import FloodWait
import traceback

from . import config
from .logger import logger
from . import db
from .utils_price import replace_prices_in_text, detect_pro_in_text
from .utils_media import download_media, cleanup_files

# ====== FIX: event-loop для Replit, Linux, Python 3.12–3.14 ======
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# ====== Replit: загружаем переменные из Secrets ======
if "API_ID" in os.environ:
    config.API_ID = int(os.environ["API_ID"])
if "API_HASH" in os.environ:
    config.API_HASH = os.environ["API_HASH"]
if "BOT_TOKEN" in os.environ:
    config.BOT_TOKEN = os.environ["BOT_TOKEN"]
if "TARGET_CHANNEL" in os.environ:
    config.TARGET_CHANNEL = os.environ["TARGET_CHANNEL"]
if "SOURCE_CHANNELS" in os.environ:
    # Пример: "-10012345,-10099999"
    config.SOURCE_CHANNELS = [
        int(x.strip()) for x in os.environ["SOURCE_CHANNELS"].split(",") if x.strip()
    ]

# ====== Альбомы ======
album_buffer = {}

DATE_START_RE = re.compile(r'^\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b')


def is_informational(text):
    if not text:
        return False
    t = text.lower()
    for kw in config.INFO_KEYWORDS:
        if kw.lower() in t:
            return True
    return False


def message_starts_with_date(text):
    if not config.DATE_START_REQUIRED:
        return True
    if not text:
        return False
    return bool(DATE_START_RE.match(text.strip()))


def process_keyboard(kb, has_pro, pro_delta, default_delta):
    if not kb:
        return None

    new_rows = []
    for row in kb.inline_keyboard:
        new_row = []
        for btn in row:
            new_text, _ = replace_prices_in_text(
                btn.text or "",
                has_pro,
                pro_delta,
                default_delta,
                min_to_zero=config.MIN_PRICE_TO_ZERO
            )
            new_btn = InlineKeyboardButton(
                new_text,
                url=btn.url,
                callback_data=btn.callback_data,
                switch_inline_query=btn.switch_inline_query,
                switch_inline_query_current_chat=btn.switch_inline_query_current_chat
            )
            new_row.append(new_btn)
        new_rows.append(new_row)

    return InlineKeyboardMarkup(new_rows)


async def handle_single_message(client: Client, msg: Message):
    try:
        if msg.service:
            return

        combined = (msg.text or "") + "\n" + (msg.caption or "")

        if not message_starts_with_date(msg.text or msg.caption or ""):
            logger.info("Пропуск сообщения: нет даты")
            return

        if is_informational(combined):
            logger.info("Пропуск информационного сообщения")
            return

        has_pro = detect_pro_in_text(combined)

        pro_delta = float(await db.get_setting("price_pro_delta", config.PRICE_PRO_DELTA))
        default_delta = float(await db.get_setting("price_default_delta", config.PRICE_DEFAULT_DELTA))

        new_kb = process_keyboard(msg.reply_markup, has_pro, pro_delta, default_delta)

        new_text = None
        new_caption = None

        if msg.text:
            new_text, _ = replace_prices_in_text(
                msg.text, has_pro, pro_delta, default_delta,
                min_to_zero=config.MIN_PRICE_TO_ZERO
            )

        if msg.caption:
            new_caption, _ = replace_prices_in_text(
                msg.caption, has_pro, pro_delta, default_delta,
                min_to_zero=config.MIN_PRICE_TO_ZERO
            )

        target = config.TARGET_CHANNEL
        sent_msg = None

        if msg.photo:
            p = await download_media(msg)
            if p:
                sent_msg = await client.send_photo(
                    chat_id=target,
                    photo=str(p),
                    caption=new_caption or "",
                    reply_markup=new_kb,
                    parse_mode="html"
                )
                cleanup_files([p])

        elif msg.video:
            p = await download_media(msg)
            if p:
                sent_msg = await client.send_video(
                    chat_id=target,
                    video=str(p),
                    caption=new_caption or "",
                    reply_markup=new_kb
                )
                cleanup_files([p])

        elif msg.document:
            p = await download_media(msg)
            if p:
                sent_msg = await client.send_document(
                    chat_id=target,
                    document=str(p),
                    caption=new_caption or "",
                    reply_markup=new_kb
                )
                cleanup_files([p])

        elif msg.text:
            sent_msg = await client.send_message(
                chat_id=target,
                text=new_text or "",
                reply_markup=new_kb
            )

        if sent_msg:
            await db.save_message(
                str(msg.chat.id),
                msg.message_id,
                sent_msg.message_id,
                datetime.utcnow().isoformat(),
                (new_text or new_caption or "")[:800]
            )

    except FloodWait as fw:
        await asyncio.sleep(fw.x + 1)

    except Exception as e:
        tb = traceback.format_exc()
        logger.exception(f"Ошибка обработки: {e}")
        await db.save_error(
            str(msg.chat.id),
            msg.message_id,
            str(e),
            tb,
            datetime.utcnow().isoformat()
        )


async def process_album_group(client: Client, media_group_id: str):
    group = album_buffer.pop(media_group_id, [])

    if not group:
        return

    first = group[0]
    combined = (first.text or "") + "\n" + (first.caption or "")

    if not message_starts_with_date(first.text or first.caption or ""):
        logger.info("Пропуск альбома — без даты")
        return

    if is_informational(combined):
        logger.info("Пропуск альбома — информационное")
        return

    has_pro = detect_pro_in_text(combined)

    pro_delta = float(await db.get_setting("price_pro_delta", config.PRICE_PRO_DELTA))
    default_delta = float(await db.get_setting("price_default_delta", config.PRICE_DEFAULT_DELTA))

    medias = []
    temp_files = []

    try:
        for m in group:
            p = await download_media(m)
            if not p:
                continue

            temp_files.append(p)

            cap = ""
            if m.caption:
                cap, _ = replace_prices_in_text(
                    m.caption, has_pro, pro_delta, default_delta,
                    min_to_zero=config.MIN_PRICE_TO_ZERO
                )

            if m.photo:
                medias.append(InputMediaPhoto(media=str(p), caption=cap))
            elif m.video:
                medias.append(InputMediaVideo(media=str(p), caption=cap))
            else:
                medias.append(InputMediaDocument(media=str(p), caption=cap))

            await asyncio.sleep(config.REQUEST_DELAY)

        if medias:
            sent = await client.send_media_group(config.TARGET_CHANNEL, medias)
            await db.save_message(
                str(first.chat.id),
                first.message_id,
                sent[0].message_id,
                datetime.utcnow().isoformat(),
                (first.caption or "")[:800]
            )

    except Exception as e:
        tb = traceback.format_exc()
        logger.exception(f"Ошибка альбома: {e}")
        await db.save_error(
            str(first.chat.id),
            first.message_id,
            str(e),
            tb,
            datetime.utcnow().isoformat()
        )
    finally:
        cleanup_files(temp_files)


async def wait_and_process_album(client: Client, media_group_id: str):
    await asyncio.sleep(config.ALBUM_BUFFER_DELAY)
    await process_album_group(client, media_group_id)


def run_bot():
    app = Client(
        name=config.SESSION_NAME,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN if config.USE_BOT_ACCOUNT else None,
        workdir="."
    )

    @app.on_message(filters.chat(config.SOURCE_CHANNELS))
    async def new_message_handler(client, message):
        try:
            if message.service:
                return

            if message.media_group_id:
                album_buffer.setdefault(message.media_group_id, []).append(message)
                if len(album_buffer[message.media_group_id]) == 1:
                    asyncio.create_task(wait_and_process_album(client, message.media_group_id))
                return

            await handle_single_message(client, message)

        except Exception as e:
            tb = traceback.format_exc()
            logger.exception(f"Unhandled error: {e}")
            await db.save_error(
                str(message.chat.id),
                message.message_id,
                str(e),
                tb,
                datetime.utcnow().isoformat()
            )

    async def _start():
        await db.init_db()
        logger.info("Pyrogram client стартует... На Replit всё работает.")

    app.run(_start())


if __name__ == "__main__":
    run_bot()
