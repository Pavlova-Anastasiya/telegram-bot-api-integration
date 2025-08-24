"""api.py — модуль для работы с внешним API DummyJSON.

Содержит функции для получения списка товаров и выборки по категориям.
Используется в keyboards.inline и handlers.user_handlers.
"""

import requests

# Базовый URL DummyJSON API
BASE_URL = "https://dummyjson.com/products"


def fetch_products() -> dict:
    """Получить все товары из API.

    Делает запрос к https://dummyjson.com/products.
    В случае успеха возвращает JSON с ключом "products".
    При ошибке — пустой список товаров.

    Returns:
        dict: словарь с ключом "products" (список товаров).
    """
    response = requests.get(BASE_URL, timeout=15)
    if response.status_code == 200:
        return response.json()
    return {"products": []}


def get_products_by_category(category: str) -> list[dict]:
    """Получить список товаров по категории.

    Args:
        category: строковый slug категории (например, "smartphones").

    Returns:
        list[dict]: список товаров из этой категории.
    """
    url = f"{BASE_URL}/category/{category}"
    response = requests.get(url, timeout=15)
    if response.status_code == 200:
        return response.json().get("products", [])
    return []
