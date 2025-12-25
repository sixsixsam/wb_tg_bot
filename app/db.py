# app/db.py
import aiosqlite
import os
import sqlite3
from pathlib import Path
from . import config

# БД всегда в корне проекта для доступа из workflow
BASE_DIR = Path(__file__).parent.parent  # Поднимаемся из app/ в корень
DB_PATH = BASE_DIR / "reposter.db"

db_conn = None  # persistent connection


async def init_db():
    global db_conn
    
    print(f"[DB] Database path: {DB_PATH}")
    print(f"[DB] Database exists: {DB_PATH.exists()}")
    
    # Если БД не существует - создаем её
    if not DB_PATH.exists():
        print("[DB] Creating new database...")
        # Создаем БД с помощью sync sqlite3 (проще)
        sync_conn = sqlite3.connect(str(DB_PATH))
        cursor = sync_conn.cursor()
        
        # Создаем таблицы
        cursor.execute("""
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_channel TEXT,
                source_message_id INTEGER,
                error_text TEXT,
                traceback TEXT,
                created_at TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        
        sync_conn.commit()
        sync_conn.close()
        print(f"[DB] New database created: {DB_PATH}")
    
    # Подключаемся с помощью aiosqlite
    db_conn = await aiosqlite.connect(str(DB_PATH))
    
    # Включаем поддержку ON CONFLICT
    await db_conn.execute("PRAGMA foreign_keys = ON")
    
    # Создаем таблицы если их еще нет (на всякий случай)
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
    
    # Проверяем сколько записей уже есть
    async with db_conn.execute("SELECT COUNT(*) FROM messages") as cur:
        count = await cur.fetchone()
        print(f"[DB] Total messages in database: {count[0]}")


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
    # Используем INSERT OR REPLACE для простоты
    await db_conn.execute("""
        INSERT OR REPLACE INTO messages (
            source_channel, source_message_id,
            target_message_id, message_type,
            processed_at, summary
        )
        VALUES (?, ?, ?, ?, ?, ?)
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


async def close_db():
    """Закрыть соединение с БД"""
    if db_conn:
        await db_conn.close()
        print("[DB] Database connection closed")
