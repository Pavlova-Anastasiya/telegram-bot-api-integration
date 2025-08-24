"""main.py — точка входа для Telegram-бота.

Здесь создаётся приложение python-telegram-bot,
регистрируются все хендлеры и запускается polling.

Запуск:
    python main.py
"""

from telegram.ext import Application
from config import BOT_TOKEN
from handlers.user_handlers import register_user_handlers


def main():
    """Создать и запустить Telegram-бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация всех хендлеров (командных и диалоговых)
    register_user_handlers(application)

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()

