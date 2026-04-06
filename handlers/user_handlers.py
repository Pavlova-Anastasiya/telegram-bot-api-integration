"""Хендлеры Telegram-бота: выбор языка, каталог/товары, оформление,
а также командные хендлеры /help, /history, /find, /top.

Зависимости:
- utils.translator: t_ui (перевод UI-строк), t_to (перевод данных из API)
- utils.history: простая файловая история запросов (history.json)
- keyboards.inline: клавиатуры выбора категорий и моделей
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    Application,
)
import requests

from utils.translator import t_ui, t_to
from keyboards.inline import (
    get_product_categories_keyboard,
    get_models_keyboard,
    get_category_label,
)
# 🆕 история запросов
from utils import history as hist

CHOOSE_LANGUAGE, SELECTING, CONFIRMING, ASK_ADDRESS, ASK_CARD = range(5)

# ======================= ДОБАВЛЕНО: утилиты для команд =======================
def _lang(context: CallbackContext) -> str:
    """Вернуть выбранный пользователем язык из user_data.

    Args:
        context: контекст PTB.

    Returns:
        str: "ru" по умолчанию или ранее выбранный язык пользователя.
    """
    return context.user_data.get("lang", "ru")

def _args_after_command(update: Update) -> str:
    """Возвращает аргументы строки после команды (для /find, /top).

    Args:
        update: апдейт с текстом сообщения.

    Returns:
        str: текст после первой "команды" (после пробела), либо пустая строка.
    """
    text = update.message.text if update.message else ""
    if not text:
        return ""
    parts = text.split(maxsplit=1)
    if len(parts) == 1:
        return ""
    return parts[1].strip()

# ======================= ДОБАВЛЕНО: команды =======================
async def help_cmd(update: Update, context: CallbackContext):
    """Вывести справку по доступным командам бота.

    Команды:
      /start — запуск и выбор языка
      /help — текущая справка
      /history — последние 10 запросов пользователя
      /find <слова> — поиск по DummyJSON
      /top <category> [limit] — топ товаров по рейтингу

    Args:
        update: апдейт команды /help.
        context: контекст PTB.
    """
    lang = _lang(context)
    text = (
        "🤖 Доступные команды:\n"
        "/start — выбрать язык и начать\n"
        "/help — справка по командам\n"
        "/history — последние 10 ваших запросов\n"
        "/find <слова> — поиск товаров по ключевым словам\n"
        "/top <category> [limit] — топ товаров по рейтингу в категории\n\n"
        "Категории: smartphones, laptops, fragrances, skincare, groceries, home-decoration"
    )
    await update.message.reply_text(t_ui(text, lang))

async def history_cmd(update: Update, context: CallbackContext):
    """Показать историю последних 10 запросов текущего пользователя.

    История хранится в history.json (utils.history).

    Args:
        update: апдейт команды /history.
        context: контекст PTB.
    """
    lang = _lang(context)
    user = update.effective_user
    rows = hist.last_for_user(user.id, limit=10)
    if not rows:
        await update.message.reply_text(t_ui("История пуста.", lang))
        return
    lines = []
    for r in rows:
        u = f"@{r['username']}" if r.get("username") else str(r["user_id"])
        lines.append(f"• {r['ts']} — {u} — {r['command']} {r['text']}")
    await update.message.reply_text("\n".join(lines))

async def find_cmd(update: Update, context: CallbackContext):
    """Искать товары по ключевым словам через DummyJSON /products/search?q=.

    Формат:
        /find <слова>

    Побочный эффект:
        Запись в историю запросов (utils.history.add).

    Args:
        update: апдейт команды /find.
        context: контекст PTB.
    """
    lang = _lang(context)
    query = _args_after_command(update)
    if not query:
        await update.message.reply_text(t_ui("Использование: /find <слова для поиска>", lang))
        return

    # лог в историю
    user = update.effective_user
    hist.add(user.id, user.username, "find", query)

    try:
        resp = requests.get(
            "https://dummyjson.com/products/search",
            params={"q": query}, timeout=15
        )
        data = resp.json()
        products = data.get("products", [])[:10]
        if not products:
            await update.message.reply_text(t_ui("Ничего не найдено.", lang))
            return

        keyboard = [
            [InlineKeyboardButton(text=t_to(p["title"], lang), callback_data=f"product:{p['id']}")]
            for p in products
        ]
        await update.message.reply_text(
            t_ui("Нашлось:", lang),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        await update.message.reply_text(t_ui("Ошибка при поиске. Попробуйте позже.", lang))

async def top_cmd(update: Update, context: CallbackContext):
    """Показать топ-товары по рейтингу внутри категории.

    Формат:
        /top <category> [limit]
        Пример: /top smartphones 5

    Побочный эффект:
        Запись в историю запросов (utils.history.add).

    Args:
        update: апдейт команды /top.
        context: контекст PTB.
    """
    lang = _lang(context)
    args = _args_after_command(update)
    if not args:
        await update.message.reply_text(
            t_ui("Использование: /top <category> [limit]\nНапр.: /top smartphones 5", lang)
        )
        return

    parts = args.split()
    category = parts[0]
    try:
        limit = int(parts[1]) if len(parts) > 1 else 5
    except ValueError:
        limit = 5

    # лог в историю
    user = update.effective_user
    hist.add(user.id, user.username, "top", f"{category} {limit}")

    try:
        resp = requests.get(f"https://dummyjson.com/products/category/{category}", timeout=15)
        products = resp.json().get("products", [])
        if not products:
            await update.message.reply_text(t_ui("Категория не найдена или пуста.", lang))
            return

        products.sort(key=lambda p: p.get("rating", 0), reverse=True)
        products = products[:max(1, min(limit, 10))]

        text_lines = [t_ui("Топ по рейтингу:", lang)]
        for i, p in enumerate(products, 1):
            text_lines.append(f"{i}. {t_to(p['title'], lang)} — ⭐ {p.get('rating', '—')}")
        await update.message.reply_text("\n".join(text_lines))

        keyboard = [
            [InlineKeyboardButton(text=t_to(p["title"], lang), callback_data=f"product:{p['id']}")]
            for p in products
        ]
        await update.message.reply_text(
            t_ui("Открыть карточку товара:", lang),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        await update.message.reply_text(t_ui("Ошибка при получении категории.", lang))

# ======================= ТВОЙ РАБОТАЮЩИЙ КОД (без изменений) =======================
async def start(update: Update, context: CallbackContext):
    """Старт диалога: очистить user_data и предложить выбрать язык.

    Args:
        update: апдейт команды /start.
        context: контекст PTB.

    Returns:
        int: состояние CHOOSE_LANGUAGE для ConversationHandler.
    """
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="lang:ru")],
        [InlineKeyboardButton("English", callback_data="lang:en")],
    ]
    await update.message.reply_text(
        "🌐 Выберите язык / Choose your language:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_LANGUAGE

async def set_language(update: Update, context: CallbackContext):
    """Установить выбранный язык и показать клавиатуру категорий.

    Источник языка — callback_data "lang:<code>".

    Args:
        update: callback от кнопки выбора языка.
        context: контекст PTB.

    Returns:
        int: состояние SELECTING (выбор категории/модели).
    """
    query = update.callback_query
    await query.answer()

    lang = query.data.split("lang:")[1]
    context.user_data["lang"] = lang

    await query.message.reply_text(
        text=t_ui("Привет! Выберите категорию товара:", lang),
        reply_markup=get_product_categories_keyboard(lang),
    )
    return SELECTING

async def handle_callback_query(update: Update, context: CallbackContext):
    """Обработать нажатия inline-кнопок категорий и товаров.

    Обрабатываются callback_data:
      - "category:<slug>" — показать список моделей
      - "product:<id>"   — показать карточку товара

    Args:
        update: callback от inline-кнопки.
        context: контекст PTB.

    Returns:
        int | None: состояние SELECTING/CONFIRMING или None при ошибке.
    """
    query = update.callback_query
    data = query.data
    lang = context.user_data.get("lang", "ru")
    await query.answer()

    if data.startswith("category:"):
        category = data.split("category:")[1]
        await query.message.reply_text(
            text=t_ui(f"Вы выбрали категорию: {get_category_label(category, lang)}", lang),
            reply_markup=get_models_keyboard(category, lang),
        )
        return SELECTING

    elif data.startswith("product:"):
        product_id = data.split("product:")[1]
        try:
            product_data = requests.get(
                f"https://dummyjson.com/products/{product_id}", timeout=15
            ).json()

            # данные из API переводим в выбранный язык
            title_loc = t_to(product_data["title"], lang)
            desc_loc = t_to(product_data["description"], lang)
            price = product_data["price"]
            rating = product_data["rating"]

            text = (
                f"📱 *{title_loc}*\n\n"
                f"💵 {t_ui('Цена', lang)}: ${price}\n"
                f"⭐️ {t_ui('Рейтинг', lang)}: {rating}\n"
                f"📝 {t_ui('Описание', lang)}: {desc_loc}"
            )

            context.user_data.setdefault("cart", []).append(product_data)
            await query.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN)

            keyboard = [
                [InlineKeyboardButton(t_ui("✅ Оформить заказ", lang), callback_data="confirm_order")],
                [InlineKeyboardButton(t_ui("➕ Добавить ещё", lang), callback_data="add_more")],
            ]
            await query.message.reply_text(
                t_ui("Вы хотите оформить заказ или выбрать ещё товар?", lang),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return CONFIRMING

        except Exception:
            await query.edit_message_text(
                t_ui("Произошла ошибка при получении информации о товаре.", lang)
            )
            return SELECTING

async def confirm_order(update: Update, context: CallbackContext):
    """Попросить у пользователя адрес доставки.

    Переход в состояние ASK_ADDRESS.

    Args:
        update: callback от кнопки "Оформить заказ".
        context: контекст PTB.

    Returns:
        int: состояние ASK_ADDRESS.
    """
    query = update.callback_query
    lang = context.user_data.get("lang", "ru")
    await query.answer()

    await query.message.reply_text(
        t_ui(
            "Пожалуйста, введите адрес доставки в формате:\n\nФИО, телефон, ИИН, страна, город, индекс, улица, дом и квартира",
            lang,
        )
    )
    return ASK_ADDRESS

async def ask_more(update: Update, context: CallbackContext):
    """Вернуться к выбору категорий (кнопка «Добавить ещё»).

    Args:
        update: callback от кнопки "Добавить ещё".
        context: контекст PTB.

    Returns:
        int: состояние SELECTING.
    """
    query = update.callback_query
    lang = context.user_data.get("lang", "ru")
    await query.answer()

    await query.message.reply_text(
        t_ui("Выберите категорию товара:", lang),
        reply_markup=get_product_categories_keyboard(lang),
    )
    return SELECTING

async def save_address(update: Update, context: CallbackContext):
    """Сохранить адрес доставки и показать расчёт оплаты.

    Сохраняет адрес в user_data["address"] и рассчитывает:
      - 50% предоплаты,
      - 7% доставка,
      - итоговую сумму.

    Переход в состояние ASK_CARD.

    Args:
        update: апдейт с текстовым сообщением (адрес).
        context: контекст PTB.

    Returns:
        int: состояние ASK_CARD.
    """
    lang = context.user_data.get("lang", "ru")
    address = update.message.text
    context.user_data["address"] = address

    cart = context.user_data.get("cart", [])
    total_price = sum(item["price"] for item in cart)
    prepayment = total_price * 0.5
    delivery = total_price * 0.07
    final_amount = prepayment + delivery

    context.user_data["payment"] = {
        "prepayment": prepayment,
        "delivery": delivery,
        "total": final_amount,
    }

    await update.message.reply_text(
        f"💳 {t_ui('Сумма к оплате', lang)}:\n"
        f"50% {t_ui('предоплата', lang)}: ${prepayment:.2f}\n"
        f"{t_ui('Доставка', lang)} (7%): ${delivery:.2f}\n"
        f"{t_ui('Итого', lang)}: ${final_amount:.2f}\n\n"
        f"{t_ui('Введите номер карты для оплаты:', lang)}"
    )
    return ASK_CARD

async def save_card(update: Update, context: CallbackContext):
    """Сохранить номер карты и подтвердить заказ.

    Очищает user_data по завершении.

    Args:
        update: апдейт с текстом (номер карты).
        context: контекст PTB.

    Returns:
        int: ConversationHandler.END
    """
    lang = context.user_data.get("lang", "ru")
    card_number = update.message.text
    payment = context.user_data.get("payment", {})
    cart = context.user_data.get("cart", [])
    address = context.user_data.get("address", "")

    text = t_ui("✅ Заказ подтверждён!\n\n📦 Состав заказа:\n", lang)
    for i, item in enumerate(cart, 1):
        text += f"{i}. {t_to(item['title'], lang)} — ${item['price']}\n"

    text += (
        f"\n🚚 {t_ui('Адрес доставки', lang)}:\n{address}"
        f"\n💳 {t_ui('Оплата', lang)}:\n{t_ui('Предоплата', lang)}: ${payment['prepayment']:.2f}, "
        f"{t_ui('доставка', lang)}: ${payment['delivery']:.2f}\n"
        f"{t_ui('Номер карты', lang)}: {card_number}"
        f"\n\n{t_ui('Спасибо за заказ!', lang)}"
    )

    await update.message.reply_text(text)
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    """Отменить текущую операцию и очистить user_data.

    Args:
        update: апдейт команды /cancel.
        context: контекст PTB.

    Returns:
        int: ConversationHandler.END
    """
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(t_ui("Операция отменена.", lang))
    context.user_data.clear()
    return ConversationHandler.END

def register_user_handlers(application: Application):
    """Зарегистрировать командные и разговорные хендлеры в приложении.

    Сначала регистрируются командные хендлеры (/help, /history, /find, /top),
    затем — разговорный ConversationHandler со стадиями выбора языка,
    категорий/товаров и оформления заказа.

    Args:
        application: экземпляр telegram.ext.Application
    """
    # 🆕 сначала регистрируем командные хендлеры
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("history", history_cmd))
    application.add_handler(CommandHandler("find", find_cmd))
    application.add_handler(CommandHandler("top", top_cmd))

    # затем — твой разговорный handler как был
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_LANGUAGE: [CallbackQueryHandler(set_language, pattern="^lang:")],
            SELECTING: [
                CallbackQueryHandler(handle_callback_query, pattern="^(category:|product:)"),
            ],
            CONFIRMING: [
                CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                CallbackQueryHandler(ask_more, pattern="^add_more$"),
            ],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_address)],
            ASK_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_card)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(conv_handler)


