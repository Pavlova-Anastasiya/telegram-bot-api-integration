"""history.py — модуль для хранения и работы с историей запросов пользователей.

ВМЕСТО JSON теперь используется база данных SQLite + ORM Peewee.
Файл базы: `telegram_bot/history.db`.

Публичный API сохранён:
- add(user_id, username, command, text)
- last_for_user(user_id, limit=10)
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime
from peewee import SqliteDatabase, Model, IntegerField, CharField, TextField, DateTimeField

# Путь к файлу БД (в корне проекта рядом с utils/)
DB_PATH = Path(__file__).resolve().parents[1] / "history.db"

# Инициализация БД
db = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class SearchHistory(BaseModel):
    """Таблица истории запросов."""
    user_id = IntegerField()                 # Telegram user id
    username = CharField(null=True)          # @username (может быть None)
    command = CharField()                    # команда: find/top/etc
    text = TextField()                       # аргументы/поисковая строка
    created_at = DateTimeField(default=datetime.utcnow)  # время в UTC


# Создаём таблицу, если её ещё нет
db.connect(reuse_if_open=True)
db.create_tables([SearchHistory])


def add(user_id: int, username: str | None, command: str, text: str) -> None:
    """Добавить новую запись в историю (SQLite + Peewee)."""
    SearchHistory.create(
        user_id=user_id,
        username=username,
        command=command,
        text=text,
    )


def last_for_user(user_id: int, limit: int = 10) -> list[dict]:
    """Получить последние записи истории для конкретного пользователя.

    Возвращает список словарей в том же формате, что был при JSON-хранилище.
    """
    query = (SearchHistory
             .select()
             .where(SearchHistory.user_id == user_id)
             .order_by(SearchHistory.created_at.desc())
             .limit(limit))

    # Приведём к прежнему виду, чтобы существующий код не менять
    return [
        {
            "ts": row.created_at.isoformat(timespec="seconds") + "Z",
            "user_id": row.user_id,
            "username": row.username,
            "command": row.command,
            "text": row.text,
        }
        for row in query
    ]

