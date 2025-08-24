"""translator.py — модуль для перевода строк с помощью deep_translator.

Содержит два варианта перевода:
- t_ui: используется для UI-строк интерфейса (оставляет русский текст без перевода).
- t_to: используется для любых данных из API (всегда переводит в выбранный язык).
"""

from functools import lru_cache
from deep_translator import GoogleTranslator


@lru_cache(maxsize=4096)
def _translate_auto_to(text: str, target: str) -> str:
    """Вспомогательная функция: перевод текста в указанный язык.

    Использует кэширование для снижения числа запросов к API.

    Args:
        text: исходная строка.
        target: язык назначения (например, "ru", "en").

    Returns:
        str: переведённая строка.
    """
    return GoogleTranslator(source="auto", target=target).translate(text)


def t_ui(text: str, lang: str) -> str:
    """Перевод строк интерфейса.

    Особенность:
      - если язык = "ru" → возвращается исходный текст без перевода;
      - если язык другой (например, "en") → переводится.

    Args:
        text: строка интерфейса.
        lang: язык назначения ("ru", "en").

    Returns:
        str: переведённая строка или оригинал (для русского).
    """
    if not text:
        return text
    if lang == "ru":
        return text
    try:
        return _translate_auto_to(text, lang)
    except Exception:
        return text


def t_to(text: str, lang: str) -> str:
    """Перевод произвольных данных (например, названий и описаний товаров).

    В отличие от t_ui:
      - всегда выполняет перевод (в т.ч. в русский).

    Args:
        text: строка для перевода.
        lang: язык назначения ("ru", "en").

    Returns:
        str: переведённая строка.
    """
    if not text:
        return text
    try:
        return _translate_auto_to(text, lang)
    except Exception:
        return text


