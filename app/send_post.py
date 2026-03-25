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
            [Button.url("Гарантийный сервис", "https://t.me/linfortepiano")],
            [Button.url("Оптовый заказ", "https://t.me/linfortepiano")],
            # Пары
            [
                Button.url("Гаджеты", "https://t.me/perviykremlevskiy/319"),
                Button.url("Яндекс/JBL", "https://t.me/perviykremlevskiy/320")
            ],
            [
                Button.url("Ps5/Xbox", "https://t.me/perviykremlevskiy/321"),
                Button.url("Honor/huawei", "https://t.me/perviykremlevskiy/322")
            ],
            [
                Button.url("Pixel/ONE PLUS", "https://t.me/perviykremlevskiy/323"),
                Button.url("SAMSUNG", "https://t.me/perviykremlevskiy/324")
            ],
            [
                Button.url("Xiaomi/Poco", "https://t.me/perviykremlevskiy/326"),
                Button.url("Dyson", "https://t.me/perviykremlevskiy/328")
            ],
            [
                Button.url("DJI", "https://t.me/perviykremlevskiy/332"),
                Button.url("Apple Watch", "https://t.me/perviykremlevskiy/333")
            ],
            [
                Button.url("Смарт-часы", "https://t.me/perviykremlevskiy/334"),
                Button.url("AirPods", "https://t.me/perviykremlevskiy/339")
            ],
            [
                Button.url("Наушники", "https://t.me/perviykremlevskiy/340"),
                Button.url("iPad Air", "https://t.me/perviykremlevskiy/342")
            ],
            [
                Button.url("iPad Pro", "https://t.me/perviykremlevskiy/344"),
                Button.url("iPad/iPad mini", "https://t.me/perviykremlevskiy/345")
            ],
            [
                Button.url("iMac", "https://t.me/perviykremlevskiy/346"),
                Button.url("MacBook Air", "https://t.me/perviykremlevskiy/348")
            ],
            [
                Button.url("MacBook Pro", "https://t.me/perviykremlevskiy/350"),
                Button.url("SE/11/12", "https://t.me/perviykremlevskiy/352")
            ],
            [
                Button.url("iPhone 13", "https://t.me/perviykremlevskiy/364"),
                Button.url("iPhone 14/14 Pro", "https://t.me/perviykremlevskiy/365")
            ],
            [
                Button.url("iPhone 15/15 Pro", "https://t.me/perviykremlevskiy/355"),
                Button.url("iPhone 16e/16", "https://t.me/perviykremlevskiy/356")
            ],
            [
                Button.url("iPhone 16e/16", "https://t.me/perviykremlevskiy/359"),
                Button.url("iPhone 16 Pro", "https://t.me/perviykremlevskiy/360")
            ],
            [
                Button.url("iPhone 17 Pro", "https://t.me/perviykremlevskiy/367")
            ],
            # Последняя кнопка
            [Button.url("Заказать", "https://t.me/linfortepiano")]
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
