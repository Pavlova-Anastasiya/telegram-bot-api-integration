"""history.py — модуль для хранения и работы с историей запросов пользователей.

История хранится в JSON-файле `telegram_bot/history.json`.
Используется для реализации команды /history в боте.
"""

from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime

# Путь к файлу истории (расположен в корне проекта рядом с utils/)
HISTORY_FILE = Path(__file__).resolve().parents[1] / "history.json"


def _read_all() -> list[dict]:
    """Прочитать всю историю из файла.

    Returns:
        list[dict]: список записей истории (или пустой список, если файл отсутствует/повреждён).
    """
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _write_all(items: list[dict]) -> None:
    """Перезаписать историю в файл.

    Args:
        items: список записей истории для сохранения.
    """
    HISTORY_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def add(user_id: int, username: str | None, command: str, text: str) -> None:
    """Добавить новую запись в историю.

    Args:
        user_id: ID пользователя Telegram.
        username: @username пользователя (или None).
        command: команда, вызвавшая запись (например "find", "top").
        text: аргументы/текст запроса.
    """
    items = _read_all()
    items.append({
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",  # UTC-время ISO
        "user_id": user_id,
        "username": username,
        "command": command,
        "text": text,
    })
    # ограничим размер истории последними 5000 записями
    items = items[-5000:]
    _write_all(items)


def last_for_user(user_id: int, limit: int = 10) -> list[dict]:
    """Получить последние записи истории для конкретного пользователя.

    Args:
        user_id: ID пользователя Telegram.
        limit: максимальное количество записей (по умолчанию 10).

    Returns:
        list[dict]: список последних записей.
    """
    items = [x for x in _read_all() if x.get("user_id") == user_id]
    return items[-limit:]
