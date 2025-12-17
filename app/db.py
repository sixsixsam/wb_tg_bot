# app/db.py
import aiosqlite
import os
from . import config

DB_PATH = os.getenv("DB_PATH", "reposter.db")

db_conn = None  # persistent connection


async def init_db():
    global db_conn
    db_conn = await aiosqlite.connect(DB_PATH)

    # Удаляем старую таблицу для чистой схемы (если нужно, убрать на проде!)
    # await db_conn.execute("DROP TABLE IF EXISTS messages;")

    # Создаем таблицы
    await db_conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            source_channel TEXT NOT NULL,
            source_message_id INTEGER NOT NULL,
            target_message_id INTEGER,
            message_type TEXT DEFAULT 'text',
            processed_at TEXT,
            summary TEXT,
            PRIMARY KEY (source_channel, source_message_id)
        );
    """)
    await db_conn.execute("""
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_channel TEXT,
            source_message_id INTEGER,
            error_text TEXT,
            traceback TEXT,
            created_at TEXT
        );
    """)
    await db_conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    await db_conn.commit()


async def get_message_target(source_channel, source_message_id):
    async with db_conn.execute(
        "SELECT target_message_id FROM messages WHERE source_channel=? AND source_message_id=?",
        (source_channel, source_message_id)
    ) as cur:
        row = await cur.fetchone()
        return row[0] if row else None


async def get_message_target_with_text(source_channel, source_message_id):
    """Получаем target_id и текст сообщения из базы"""
    async with db_conn.execute(
        "SELECT target_message_id, summary FROM messages WHERE source_channel=? AND source_message_id=?",
        (source_channel, source_message_id)
    ) as cur:
        row = await cur.fetchone()
        if row:
            return row[0], row[1]  # target_id, text
        return None, None  # Если записи нет


async def update_message_target(
    source_channel,
    source_message_id,
    target_message_id,
    processed_at,
    summary,
    message_type="text"
):
    # ON CONFLICT сработает только если есть PRIMARY KEY (у нас source_channel+source_message_id)
    await db_conn.execute("""
        INSERT INTO messages (
            source_channel, source_message_id,
            target_message_id, message_type,
            processed_at, summary
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_channel, source_message_id) DO UPDATE SET
            target_message_id=excluded.target_message_id,
            processed_at=excluded.processed_at,
            summary=excluded.summary,
            message_type=excluded.message_type
    """, (
        source_channel,
        source_message_id,
        target_message_id,
        message_type,
        processed_at,
        summary
    ))
    await db_conn.commit()


async def save_error(source_channel, source_message_id, error_text, traceback_text, created_at):
    await db_conn.execute("""
        INSERT INTO errors(
            source_channel, source_message_id,
            error_text, traceback, created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        source_channel,
        source_message_id,
        error_text,
        traceback_text,
        created_at
    ))
    await db_conn.commit()
