# app/logger.py
# Централизованное логирование: консоль + ротация файлов

import logging
from logging.handlers import RotatingFileHandler
import os
from . import config


LOG_DIR = config.LOG_DIR
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name="price_reposter"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Консольный хэндлер
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    # Файловый ротационный хэндлер
    fh = RotatingFileHandler(
        os.path.join(LOG_DIR, f"{name}.log"),
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    return logger

logger = setup_logger()
