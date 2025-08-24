"""config.py — модуль конфигурации для Telegram-бота.

Загружает переменные окружения из `.env` файла
и предоставляет доступ к ним как к константам.

Файл `.env` должен содержать, например:

    BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

Используется в main.py для запуска бота.
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Токен Telegram-бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
