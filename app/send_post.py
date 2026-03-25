# app/send_post.py

import asyncio
import os
import sys
from pathlib import Path

# Добавляем путь для импорта config
sys.path.append(str(Path(__file__).parent))

# Импортируем после добавления пути
import config
from telethon import TelegramClient, Button

async def send_tradein_post():
    """
    Отправляет пост с кнопками Trade-In в целевой канал через БОТА
    """
    print("🚀 Запуск отправки Trade-In поста через бота...")
    
    # Проверяем токен бота
    if not config.BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не задан!")
        print("   Установите BOT_TOKEN в GitHub Secrets")
        return False
    
    if not config.TARGET_CHANNEL:
        print("❌ Ошибка: TARGET_CHANNEL не задан!")
        return False
    
    print(f"📊 Конфигурация:")
    print(f"   BOT_TOKEN: {'*' * len(config.BOT_TOKEN) if config.BOT_TOKEN else 'Нет'}")
    print(f"   TARGET_CHANNEL: {config.TARGET_CHANNEL}")
    
    # Инициализируем клиент БОТА
    client = TelegramClient(
        session='bot_session',  # любое имя для сессии бота
        api_id=config.API_ID,
        api_hash=config.API_HASH
    )
    
    try:
        # Запускаем бота с токеном
        await client.start(bot_token=config.BOT_TOKEN)
        print("✅ Бот авторизован")
        
        # Текст поста
        post_text = """
🎯 Официальный аккаунт ✅ 

Только новая и оригинальная техника из первоисточников!
👇👇👇
"""
        
        # Кнопки
        buttons =  [
            # Первые три — по одной строке
            [InlineKeyboardButton("Гарантийный сервис", url="https://t.me/linfortepiano")],
            [InlineKeyboardButton("Оптовый заказ", url="https://t.me/linfortepiano")],
            # Пары
            [
                InlineKeyboardButton("Гаджеты", url="https://t.me/perviykremlevskiy/319"),
                InlineKeyboardButton("Яндекс/JBL", url="https://t.me/perviykremlevskiy/320")
            ],
            [
                InlineKeyboardButton("Ps5/Xbox", url="https://t.me/perviykremlevskiy/321"),
                InlineKeyboardButton("Honor/huawei", url="https://t.me/perviykremlevskiy/322")
            ],
            [
                InlineKeyboardButton("Pixel/ONE PLUS", url="https://t.me/perviykremlevskiy/323"),
                InlineKeyboardButton("SAMSUNG", url="https://t.me/perviykremlevskiy/324")
            ],
            [
                InlineKeyboardButton("Xiaomi/Poco", url="https://t.me/perviykremlevskiy/326"),
                InlineKeyboardButton("Dyson", url="https://t.me/perviykremlevskiy/328")
            ],
            [
                InlineKeyboardButton("DJI", url="https://t.me/perviykremlevskiy/332"),
                InlineKeyboardButton("Apple Watch", url="https://t.me/perviykremlevskiy/333")
            ],
            [
                InlineKeyboardButton("Смарт-часы", url="https://t.me/perviykremlevskiy/334"),
                InlineKeyboardButton("AirPods", url="https://t.me/perviykremlevskiy/339")
            ],
            [
                InlineKeyboardButton("Наушники", url="https://t.me/perviykremlevskiy/340"),
                InlineKeyboardButton("iPad Air", url="https://t.me/perviykremlevskiy/342")
            ],
            [
                InlineKeyboardButton("iPad Pro", url="https://t.me/perviykremlevskiy/344"),
                InlineKeyboardButton("iPad/iPad mini", url="https://t.me/perviykremlevskiy/345")
            ],
            [
                InlineKeyboardButton("iMac", url="https://t.me/perviykremlevskiy/346"),
                InlineKeyboardButton("MacBook Air", url="https://t.me/perviykremlevskiy/348")
            ],
            [
                InlineKeyboardButton("MacBook Pro", url="https://t.me/perviykremlevskiy/350"),
                InlineKeyboardButton("SE/11/12", url="https://t.me/perviykremlevskiy/352")
            ],
            [
                InlineKeyboardButton("iPhone 13", url="https://t.me/perviykremlevskiy/364"),
                InlineKeyboardButton("iPhone 14/14 Pro", url="https://t.me/perviykremlevskiy/365")
            ],
            [
                InlineKeyboardButton("iPhone 15/15 Pro", url="https://t.me/perviykremlevskiy/355"),
                InlineKeyboardButton("iPhone 16e/16", url="https://t.me/perviykremlevskiy/356")
            ],
            [
                InlineKeyboardButton("iPhone 16e/16", url="https://t.me/perviykremlevskiy/359"),
                InlineKeyboardButton("iPhone 16 Pro", url="https://t.me/perviykremlevskiy/360")
            ],
            [
                InlineKeyboardButton("iPhone 17 Pro", url="https://t.me/perviykremlevskiy/367")
            ],
            # Последняя кнопка
            [InlineKeyboardButton("Заказать", url="https://t.me/linfortepiano")]
        ]
        
        print(f"📤 Отправка поста в {config.TARGET_CHANNEL}...")
        
        # Отправка через бота
        await client.send_message(
            entity=config.TARGET_CHANNEL,
            message=post_text,
            buttons=buttons,
            link_preview=False,
            parse_mode='md'
        )
        
        print("✅ Пост успешно отправлен через бота!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при отправке: {type(e).__name__}: {e}")
        
        # Проверяем права бота
        if "CHAT_WRITE_FORBIDDEN" in str(e) or "no write access" in str(e):
            print("\n⚠️  У бота нет прав на публикацию в канале!")
            print("   Сделайте бота администратором канала с правом:")
            print("   - 'Post Messages' (Отправка сообщений)")
            print("   - 'Edit Messages' (Редактирование сообщений)")
        elif "Could not find the input entity" in str(e):
            print("\n⚠️  Не найден канал! Проверьте:")
            print("   1. TARGET_CHANNEL в формате @username или -1001234567890")
            print("   2. Бот добавлен в канал")
            print("   3. Бот - администратор канала")
        
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if client.is_connected():
            await client.disconnect()
            print("📴 Соединение закрыто")

if __name__ == "__main__":
    success = asyncio.run(send_tradein_post())
    sys.exit(0 if success else 1)
