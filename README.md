# Telegram Price Reposter — продакшн-ready (инструкция)

## Требования
- Python 3.10+
- Доступ к API Telegram (API_ID, API_HASH) и BOT_TOKEN (если используете бота)
- Права: бот должен читать SOURCE_CHANNELS и писать в TARGET_CHANNEL

## Установка
1. Клонируйте или создайте структуру проекта из файлов.
2. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
