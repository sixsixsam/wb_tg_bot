# send_post.py

import asyncio
from telethon import TelegramClient, Button
import config  # твой конфиг

async def send_tradein_post():
    """
    Отправляет пост с кнопками Trade-In в целевой канал
    """
    # Используем USER-сессию из твоего конфига (или BOT, если нужны права админа)
    client = TelegramClient(
        session=config.USER_SESSION_NAME,
        api_id=config.API_ID,
        api_hash=config.API_HASH
    )
    
    await client.start()
    
    # Текст поста (отредактируй по желанию)
    post_text = """
🎯 Официальный аккаунт ✅ 

Только новая и оригинальная техника из первоисточников!
Выбери категорию ниже 👇
"""
    
    # Кнопки в точном порядке как требуется
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
    
    try:
        # Отправляем в целевой канал из конфига
        target_channel = config.TARGET_CHANNEL
        if not target_channel:
            print("❌ TARGET_CHANNEL не указан в конфиге!")
            return
        
        print(f"📤 Отправка поста в канал: {target_channel}")
        
        await client.send_message(
            entity=target_channel,
            message=post_text,
            buttons=buttons,
            link_preview=False,
            parse_mode='md'  # Markdown форматирование
        )
        
        print("✅ Пост с инлайн-кнопками успешно отправлен!")
        
    except Exception as e:
        print(f"❌ Ошибка при отправке: {e}")
    
    finally:
        await client.disconnect()


if __name__ == "__main__":
    # Проверка обязательных параметров
    if not config.API_ID or not config.API_HASH:
        print("❌ Укажите API_ID и API_HASH в переменных окружения или .env файле!")
        exit(1)
    
    if not config.TARGET_CHANNEL:
        print("❌ Укажите TARGET_CHANNEL в переменных окружения!")
        exit(1)
    
    # Запускаем
    asyncio.run(send_tradein_post())
