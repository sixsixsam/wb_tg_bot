# app/db.py
# Асинхронная работа с SQLite через aiosqlite.
# Таблицы: messages, errors, settings

import aiosqlite
import asyncio
import os
import json
from . import config


DB_PATH = "reposter.db"

# Инициализация БД — вызывается при старте
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_channel TEXT,
            source_message_id INTEGER,
            target_message_id INTEGER,
            processed_at TEXT,
            summary TEXT
        );
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_channel TEXT,
            source_message_id INTEGER,
            error_text TEXT,
            traceback TEXT,
            created_at TEXT
        );
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)
        # Записать дефолтные настройки, если нет
        cur = await db.execute("SELECT value FROM settings WHERE key = ?", ("price_pro_delta",))
        row = await cur.fetchone()
        if not row:
            await db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", ("price_pro_delta", str(config.PRICE_PRO_DELTA)))
            await db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", ("price_default_delta", str(config.PRICE_DEFAULT_DELTA)))
        await db.commit()

# Сохранить сообщение
async def save_message(source_channel, source_message_id, target_message_id, processed_at, summary):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages(source_channel, source_message_id, target_message_id, processed_at, summary) VALUES (?, ?, ?, ?, ?)",
            (source_channel, source_message_id, target_message_id, processed_at, summary)
        )
        await db.commit()
        # Обрезать до RECENT_MESSAGES_LIMIT
        await db.execute(f"""
            DELETE FROM messages WHERE id NOT IN (
                SELECT id FROM messages ORDER BY id DESC LIMIT {config.RECENT_MESSAGES_LIMIT}
            );
        """)
        await db.commit()

# Сохранить ошибку
async def save_error(source_channel, source_message_id, error_text, traceback_text, created_at):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO errors(source_channel, source_message_id, error_text, traceback, created_at) VALUES (?, ?, ?, ?, ?)",
            (source_channel, source_message_id, error_text, traceback_text, created_at)
        )
        await db.commit()

# Получить последние N ошибок / сообщений
async def get_recent_errors(limit=100):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, source_channel, source_message_id, error_text, traceback, created_at FROM errors ORDER BY id DESC LIMIT ?", (limit,))
        rows = await cur.fetchall()
    return rows

async def get_recent_messages(limit=100):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, source_channel, source_message_id, target_message_id, processed_at, summary FROM messages ORDER BY id DESC LIMIT ?", (limit,))
        rows = await cur.fetchall()
    return rows

# Функции настроек
async def get_setting(key, default=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cur.fetchone()
        if row:
            return row[0]
    return default

async def set_setting(key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", (key, str(value)))
        await db.commit()
