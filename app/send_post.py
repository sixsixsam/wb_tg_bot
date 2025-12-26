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
    Отправляет пост с кнопками Trade-In в целевой канал
    """
    print("🚀 Запуск отправки Trade-In поста...")
    
    # Используем значения из config (которые загружаются из env)
    print(f"📊 Конфигурация:")
    print(f"   API_ID: {config.API_ID}")
    print(f"   TARGET_CHANNEL: {config.TARGET_CHANNEL}")
    print(f"   SESSION: {config.USER_SESSION_NAME}")
    
    if not config.API_ID or not config.API_HASH:
        print("❌ Ошибка: API_ID или API_HASH не заданы!")
        print("   Установите секреты в GitHub Secrets:")
        print("   - API_ID")
        print("   - API_HASH")
        print("   - TARGET_CHANNEL")
        return False
    
    if not config.TARGET_CHANNEL:
        print("❌ Ошибка: TARGET_CHANNEL не задан!")
        return False
    
    # Инициализируем клиент
    client = TelegramClient(
        session=config.USER_SESSION_NAME,
        api_id=config.API_ID,
        api_hash=config.API_HASH
    )
    
    try:
        await client.start()
        print("✅ Авторизация успешна")
        
        # Текст поста
        post_text = """
🎯 **Официальный аккаунт ✅**

Только новая и оригинальная техника из первоисточников!
Выбери категорию ниже 👇
"""
        
        # Кнопки
        buttons = [
            [Button.url('Гарантийный сервис', 'https://t.me/linfortepiano')],
            [Button.url('Оптовый заказ', 'https://t.me/linfortepiano')],
            [
                Button.url('Гаджеты', 'https://t.me/perviykremlevskiy/319'),
                Button.url('Яндекс/JBL', 'https://t.me/perviykremlevskiy/320')
            ],
            [
                Button.url('PS 5/Xbox', 'https://t.me/perviykremlevskiy/321'),
                Button.url('HUAWEI/HONOR', 'https://t.me/perviykremlevskiy/322')
            ],
            [
                Button.url('Pixel/ONE PLUS', 'https://t.me/perviykremlevskiy/323'),
                Button.url('SAMSUNG', 'https://t.me/perviykremlevskiy/324')
            ],
            [
                Button.url('Xiaomi/Poco', 'https://t.me/perviykremlevskiy/326'),
                Button.url('Dyson', 'https://t.me/perviykremlevskiy/328')
            ],
            [
                Button.url('DJI', 'https://t.me/perviykremlevskiy/332'),
                Button.url('Apple Watch', 'https://t.me/perviykremlevskiy/333')
            ],
            [
                Button.url('Смарт-часы', 'https://t.me/perviykremlevskiy/336'),
                Button.url('AirPods', 'https://t.me/perviykremlevskiy/339')
            ],
            [
                Button.url('Наушники', 'https://t.me/perviykremlevskiy/340'),
                Button.url('iPad Air', 'https://t.me/perviykremlevskiy/342')
            ],
            [
                Button.url('iPad Pro', 'https://t.me/perviykremlevskiy/344'),
                Button.url('iPad/iPad mini', 'https://t.me/perviykremlevskiy/345')
            ],
            [
                Button.url('iMac', 'https://t.me/perviykremlevskiy/346'),
                Button.url('MacBook Air', 'https://t.me/perviykremlevskiy/348')
            ],
            [
                Button.url('MacBook Pro', 'https://t.me/perviykremlevskiy/350'),
                Button.url('SE/11/12', 'https://t.me/perviykremlevskiy/352')
            ],
            [
                Button.url('iPhone 13', 'https://t.me/perviykremlevskiy/353'),
                Button.url('iPhone 14/14 Pro', 'https://t.me/perviykremlevskiy/354')
            ],
            [
                Button.url('iPhone 15/15 Pro', 'https://t.me/perviykremlevskiy/355'),
                Button.url('iPhone 16e/16', 'https://t.me/perviykremlevskiy/356')
            ],
            [
                Button.url('iPhone 16 Pro', 'https://t.me/perviykremlevskiy/357'),
                Button.url('iPhone 17/Air', 'https://t.me/perviykremlevskiy/358')
            ],
            [Button.url('iPhone 17 Pro/Pro ...', 'https://t.me/perviykremlevskiy/360')],
            [Button.url('Заказать', 'https://t.me/linfortepiano')]
        ]
        
        print(f"📤 Отправка поста в {config.TARGET_CHANNEL}...")
        
        await client.send_message(
            entity=config.TARGET_CHANNEL,
            message=post_text,
            buttons=buttons,
            link_preview=False,
            parse_mode='md'
        )
        
        print("✅ Пост успешно отправлен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при отправке: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if client.is_connected():
            await client.disconnect()
            print("📴 Соединение закрыто")

if __name__ == "__main__":
    # Для отладки в локальном режиме
    if not os.getenv('GITHUB_ACTIONS'):
        print("⚠️  Локальный запуск. Убедитесь, что переменные окружения установлены.")
        print("   Или создайте .env файл в папке app/")
    
    success = asyncio.run(send_tradein_post())
    sys.exit(0 if success else 1)
