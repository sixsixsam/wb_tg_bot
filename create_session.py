#!/usr/bin/env python3
"""Создание новой сессии для Pyrogram"""

import asyncio
from pyrogram import Client

# Данные из вашего config.py
API_ID = 2040  # ВАШ API_ID (число)
API_HASH = "ваш_api_hash"  # ВАШ API_HASH
SESSION_NAME = "price_reposter_user"

async def main():
    print("🚀 Создание новой сессии...")
    print(f"API_ID: {API_ID}")
    print(f"SESSION_NAME: {SESSION_NAME}")
    
    async with Client(
        name=SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir="."
    ) as client:
        print("✅ Сессия создана!")
        print(f"📁 Файл сессии: {SESSION_NAME}.session")
        
        # Проверяем, что сессия работает
        me = await client.get_me()
        print(f"👤 Аккаунт: {me.first_name} (@{me.username})")
        print(f"🆔 ID: {me.id}")

if __name__ == "__main__":
    asyncio.run(main())
