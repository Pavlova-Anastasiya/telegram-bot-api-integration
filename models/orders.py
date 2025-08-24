"""orders.py — простая модель товара для примера работы с заказами.

Содержит класс Product, описывающий товар с основными характеристиками.
"""

class Product:
    """Модель товара.

    Атрибуты:
        id (int | str): идентификатор товара.
        name (str): название товара.
        price (float | int): цена товара (в тенге).
        colors (list[str]): доступные цвета.
        memory (list[str] | str): варианты памяти или характеристик.
    """

    def __init__(self, id, name, price, colors, memory):
        """Создать объект товара.

        Args:
            id: идентификатор товара.
            name: название товара.
            price: цена товара.
            colors: список доступных цветов.
            memory: список вариантов памяти (или строка).
        """
        self.id = id
        self.name = name
        self.price = price
        self.colors = colors
        self.memory = memory

    def __repr__(self):
        """Вернуть строковое представление товара.

        Returns:
            str: строка в формате "<название> (<цена>₸)".
        """
        return f"{self.name} ({self.price}₸)"
