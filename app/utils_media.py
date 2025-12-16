# app/utils_media.py
import asyncio
from pathlib import Path
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError
from . import config
from .logger import logger

DOWNLOAD_DIR = Path(config.DOWNLOAD_DIR)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def download_media(msg: Message, max_retries=None) -> Path | None:
    retries = max_retries or config.DOWNLOAD_RETRIES
    attempt = 0

    while attempt < retries:
        try:
            path = await msg.download(file_name=str(DOWNLOAD_DIR))
            if path:
                return Path(path)
            return None
        except FloodWait as fw:
            logger.warning(f"FloodWait download {fw.value}s")
            await asyncio.sleep(fw.value + 1)
        except RPCError as e:
            logger.warning(f"RPCError download {e}")
            attempt += 1
            await asyncio.sleep(1 + attempt)
        except Exception:
            logger.exception("DOWNLOAD ERROR")
            attempt += 1
            await asyncio.sleep(1 + attempt)

    logger.error("DOWNLOAD FAILED")
    return None

def cleanup_files(paths):
    for p in paths:
        try:
            if p and p.exists():
                p.unlink()
        except Exception:
            pass
