"""inline.py — генерация inline-клавиатур для Telegram-бота.

Содержит:
- LABELS: словарь локализованных названий категорий.
- get_category_label: возвращает локализованное название категории.
- get_product_categories_keyboard: клавиатура с категориями.
- get_models_keyboard: клавиатура с моделями товаров из API.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from api import get_products_by_category
from utils.translator import t_ui, t_to

# Словарь «slug категории» → { "ru": "название", "en": "translation" }
LABELS = {
    "smartphones": {"ru": "Смартфоны", "en": "Smartphones"},
    "laptops": {"ru": "Ноутбуки", "en": "Laptops"},
    "fragrances": {"ru": "Парфюмерия", "en": "Fragrances"},
    "skincare": {"ru": "Уход за кожей", "en": "Skincare"},
    "groceries": {"ru": "Продукты", "en": "Groceries"},
    "home-decoration": {"ru": "Декор", "en": "Home Decoration"},
}

def get_category_label(slug: str, lang: str = "ru") -> str:
    """Вернуть локализованное название категории по её slug.

    Args:
        slug: строка-идентификатор категории (например "smartphones").
        lang: язык пользователя ("ru" или "en").

    Returns:
        str: локализованное название категории или сам slug, если перевода нет.
    """
    return LABELS.get(slug, {}).get(lang, slug)

def get_product_categories_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Сформировать клавиатуру с кнопками всех категорий.

    Args:
        lang: язык пользователя ("ru" или "en").

    Returns:
        InlineKeyboardMarkup: клавиатура с кнопками «категория».
    """
    keyboard = [
        [InlineKeyboardButton(text=LABELS[cat][lang], callback_data=f"category:{cat}")]
        for cat in LABELS
    ]
    return InlineKeyboardMarkup(keyboard)

def get_models_keyboard(category: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Сформировать клавиатуру с моделями товаров в категории.

    Загружает список товаров из API по категории,
    переводит названия в выбранный язык и формирует кнопки.

    Args:
        category: slug категории (например "smartphones").
        lang: язык пользователя ("ru" или "en").

    Returns:
        InlineKeyboardMarkup: клавиатура с кнопками «товар».
    """
    products = get_products_by_category(category)
    keyboard = [
        [InlineKeyboardButton(text=t_to(p["title"], lang), callback_data=f"product:{p['id']}")]
        for p in products
    ]
    return InlineKeyboardMarkup(keyboard)


