# app/main.py
import asyncio
import threading
import traceback
import re
import os
import sys
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

# ЗАКОММЕНТИРУЙТЕ ДЛЯ CRON-ЗАДАЧ - НЕ НУЖЕН СЕРВЕР
# threading.Thread(target=start_fastapi, daemon=True).start()

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
    """ИСПРАВЛЕНА: Убрана бесконечность, добавлены таймауты"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Таймаут на выполнение функции
            return await asyncio.wait_for(func(*args, **kwargs), timeout=30.0)
        except FloodWait as fw:
            logger.warning(f"FloodWait {fw.value}s, attempt {attempt+1}/{max_retries}")
            await asyncio.sleep(min(fw.value, 300))  # Максимум 5 минут ожидания
        except asyncio.TimeoutError:
            logger.error(f"Timeout on attempt {attempt+1}/{max_retries}")
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except RPCError as e:
            if "MESSAGE_NOT_MODIFIED" in str(e):
                logger.info(f"Message already up to date")
                return "already_updated"  # Специальный маркер успеха
            elif "FLOOD_WAIT" in str(e):
                # Парсим время ожидания из ошибки
                import re
                match = re.search(r"FLOOD_WAIT_(\d+)", str(e))
                wait_time = int(match.group(1)) if match else 60
                logger.warning(f"Flood wait {wait_time}s")
                await asyncio.sleep(min(wait_time, 300))
                continue
            else:
                logger.error(f"RPCError on attempt {attempt+1}: {e}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt+1}: {e}")
            if attempt == max_retries - 1:
                return None
    
    logger.error(f"Failed after {max_retries} attempts")
    return None

# ================= CORE =================
async def process_message(msg: Message):
    raw = (msg.text or "") + (msg.caption or "")
    logger.info(f"PROCESS {msg.id}")

    if not has_date_start(raw):
        logger.info(f"SKIP {msg.id} (no date)")
        return

    text = clean_text(raw)

    new_text, price_changes = replace_prices_in_text(
        text=text,
        pro_delta=config.PRICE_PRO_DELTA,
        default_delta=config.PRICE_DEFAULT_DELTA,
        min_zero=config.MIN_PRICE_TO_ZERO,
        min_ignore=config.MIN_PRICE_TO_IGNORE
    )

    if not new_text.strip():
        logger.info(f"SKIP {msg.id} (empty text after cleaning)")
        return

    # Получаем старый текст из базы данных
    old_target_id, old_text = await db.get_message_target_with_text(str(msg.chat.id), msg.id)
    
    # Логируем изменения
    if old_target_id:
        logger.info(f"Found existing message in DB: target_id={old_target_id}")
        
        if old_text == new_text:
            logger.info(f"SKIP {msg.id} (text not changed)")
            return
        else:
            # Анализируем различия
            logger.info(f"Text changed for message {msg.id}")
            
            # Логируем изменения цен, если есть
            if price_changes:
                logger.info(f"Price changes detected: {price_changes}")
            
            # Сравниваем длину текста
            if len(old_text) != len(new_text):
                logger.info(f"Text length changed: {len(old_text)} -> {len(new_text)} chars")
            
            # Сравниваем первые 50 символов для наглядности
            old_preview = old_text[:50].replace('\n', ' ')
            new_preview = new_text[:50].replace('\n', ' ')
            if old_preview != new_preview:
                logger.info(f"Text preview changed: '{old_preview}' -> '{new_preview}'")
    else:
        logger.info(f"New message {msg.id}, no previous record in DB")

    kb = build_keyboard()
    media_file = None

    try:
        if msg.photo:
            media_file = await download_media(msg)
            if old_target_id:
                # Редактируем существующее сообщение
                logger.info(f"Editing photo message {msg.id} -> {old_target_id}")
                sent = await safe(
                    bot_client.edit_message_caption,
                    chat_id=config.TARGET_CHANNEL,
                    message_id=old_target_id,
                    caption=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                if sent and sent != "already_updated":
                    logger.info(f"✅ Photo message {msg.id} edited successfully")
                elif sent == "already_updated":
                    logger.info(f"✅ Photo message {msg.id} already up to date")
            else:
                # Отправляем новое сообщение
                logger.info(f"Sending new photo message {msg.id}")
                sent = await safe(
                    bot_client.send_photo,
                    chat_id=config.TARGET_CHANNEL,
                    photo=media_file,
                    caption=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                if sent:
                    logger.info(f"✅ Photo message {msg.id} sent successfully, target_id={sent.id}")
                
        elif msg.video:
            media_file = await download_media(msg)
            if old_target_id:
                # Редактируем существующее сообщение
                logger.info(f"Editing video message {msg.id} -> {old_target_id}")
                sent = await safe(
                    bot_client.edit_message_caption,
                    chat_id=config.TARGET_CHANNEL,
                    message_id=old_target_id,
                    caption=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                if sent and sent != "already_updated":
                    logger.info(f"✅ Video message {msg.id} edited successfully")
                elif sent == "already_updated":
                    logger.info(f"✅ Video message {msg.id} already up to date")
            else:
                # Отправляем новое сообщение
                logger.info(f"Sending new video message {msg.id}")
                sent = await safe(
                    bot_client.send_video,
                    chat_id=config.TARGET_CHANNEL,
                    video=media_file,
                    caption=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                if sent:
                    logger.info(f"✅ Video message {msg.id} sent successfully, target_id={sent.id}")
        else:
            if old_target_id:
                # Редактируем существующее текстовое сообщение
                logger.info(f"Editing text message {msg.id} -> {old_target_id}")
                sent = await safe(
                    bot_client.edit_message_text,
                    chat_id=config.TARGET_CHANNEL,
                    message_id=old_target_id,
                    text=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                if sent and sent != "already_updated":
                    logger.info(f"✅ Text message {msg.id} edited successfully")
                elif sent == "already_updated":
                    logger.info(f"✅ Text message {msg.id} already up to date")
            else:
                # Отправляем новое текстовое сообщение
                logger.info(f"Sending new text message {msg.id}")
                sent = await safe(
                    bot_client.send_message,
                    chat_id=config.TARGET_CHANNEL,
                    text=new_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb
                )
                if sent:
                    logger.info(f"✅ Text message {msg.id} sent successfully, target_id={sent.id}")

        # Обновляем базу данных
        if sent and sent != "already_updated":
            await db.update_message_target(
                str(msg.chat.id),
                msg.id,
                sent.id,
                datetime.utcnow().isoformat(),
                new_text[:800]
            )
            logger.info(f"✅ Database updated for message {msg.id}")
        elif sent == "already_updated" and old_target_id:
            # Обновляем только timestamp для уже актуальных сообщений
            await db.update_message_target(
                str(msg.chat.id),
                msg.id,
                old_target_id,
                datetime.utcnow().isoformat(),
                new_text[:800]
            )
            logger.info(f"✅ Database timestamp updated for message {msg.id}")

    except Exception as e:
        logger.error(f"❌ Error processing message {msg.id}: {str(e)}")
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

    # ОГРАНИЧЕНИЕ ВРЕМЕНИ НА ВЕСЬ BACKFILL
    try:
        for src in config.SOURCE_CHANNELS:
            logger.info(f"BACKFILL {src}")
            message_count = 0
            
            # Таймаут на получение истории для каждого канала
            try:
                async for m in user_client.get_chat_history(src, limit=config.BACKFILL_LIMIT):
                    if message_count >= config.BACKFILL_LIMIT:
                        break
                    
                    # Таймаут на обработку каждого сообщения
                    try:
                        await asyncio.wait_for(
                            process_message(m), 
                            timeout=60.0  # 60 секунд на сообщение
                        )
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout processing message {m.id}, skipping")
                    
                    await asyncio.sleep(float(config.REQUEST_DELAY))
                    message_count += 1
                    
                logger.info(f"Processed {message_count} messages from {src}")
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout getting history from {src}, moving to next channel")
                continue
            except Exception as e:
                logger.error(f"Error processing channel {src}: {e}")
                continue
                
    except asyncio.CancelledError:
        logger.warning("Backfill cancelled")
    except Exception as e:
        logger.error(f"Critical error in backfill: {e}")

    logger.info("DONE - All messages processed")
    
    # === ИСПРАВЛЕННЫЙ БЛОК ОСТАНОВКИ ===
    print("🔄 Starting graceful shutdown...")
    
    # 1. Останавливаем клиенты (с таймаутом)
    try:
        if bot_client.is_connected:
            await asyncio.wait_for(bot_client.stop(), timeout=5.0)
            print("✅ Bot client stopped")
    except (asyncio.TimeoutError, Exception) as e:
        print(f"⚠️ Bot client stop error (ignored): {e}")
    
    try:
        if user_client.is_connected:
            await asyncio.wait_for(user_client.stop(), timeout=5.0)
            print("✅ User client stopped")
    except (asyncio.TimeoutError, Exception) as e:
        print(f"⚠️ User client stop error (ignored): {e}")
    
    # 2. Ждем завершения оставшихся задач
    await asyncio.sleep(1.0)
    
    # 3. Явный выход для cron-задачи
    print("✅ Bot work completed successfully")
    return

def run_bot():
    """Запуск бота с гарантированным завершением для cron"""
    try:
        # ГЛАВНЫЙ ТАЙМАУТ: 10 минут на весь бота
        asyncio.run(asyncio.wait_for(main(), timeout=600.0))
        print("✅ Bot completed within timeout")
    except asyncio.TimeoutError:
        print("❌ Bot timeout after 10 minutes - forcing exit")
    except KeyboardInterrupt:
        print("Bot interrupted by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🏁 Bot process finished")
        # Гарантированное завершение процесса
        sys.exit(0)

if __name__ == "__main__":
    run_bot()
