# app/utils_media.py
# Функции для скачивания медиа с retry и обработки альбомов

import asyncio
import os
from pathlib import Path
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError
from . import config
from app.logger import logger

DOWNLOAD_DIR = Path(config.DOWNLOAD_DIR)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def download_media(msg: Message, max_retries:int=None) -> Path:
    # Скачиваем сообщение (photo/video/document/audio/voice)
    tries = 0
    max_retries = max_retries if max_retries is not None else config.DOWNLOAD_RETRIES
    while tries < max_retries:
        try:
            path = await msg.download(file_name=str(DOWNLOAD_DIR))
            if path:
                return Path(path)
            else:
                return None
        except FloodWait as fw:
            logger.warning(f"FloodWait при скачивании: {fw.x}s")
            await asyncio.sleep(fw.x + 1)
        except RPCError as e:
            logger.warning(f"RPCError при скачивании (попытка {tries+1}): {e}")
            tries += 1
            await asyncio.sleep(1 + tries)
        except Exception as e:
            logger.exception(f"Ошибка при скачивании: {e}")
            tries += 1
            await asyncio.sleep(1 + tries)
    return None

# Очистка временных файлов
def cleanup_files(paths):
    for p in paths:
        try:
            if p and p.exists():
                p.unlink()
        except Exception:
            pass
