from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Каталог товаров")],
        [KeyboardButton(text="📦 Заказать услугу")],
        [KeyboardButton(text="🔒 Безопасная сделка")],
        [KeyboardButton(text="⭐ Отзывы и сделки")],
        [KeyboardButton(text="🛠 Техподдержка")],
        [KeyboardButton(text="❓ Справка")],
    ],
    resize_keyboard=True,
)

# --- категории ---
categories = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎮 Игры", callback_data="cat:games")],
    [InlineKeyboardButton(text="💻 IT-разработка", callback_data="cat:it")],
    [InlineKeyboardButton(text="🤖 AI-услуги", callback_data="cat:ai")],
    [InlineKeyboardButton(text="🌐 Хостинг", callback_data="cat:hosting")],
    [InlineKeyboardButton(text="⚙️ Макросы / автоматизация", callback_data="cat:macros")],
])

# --- товары по категориям (заглушки, потом заменишь) ---
PRODUCTS = {
    "games": [
        ("Плей рок / GG Sell — товары", "games:1"),
        ("Макросы для игр", "games:2"),
    ],
    "it": [
        ("Парсинг данных", "it:1"),
        ("Сборщик заявок (бот)", "it:2"),
        ("Автоматизация Excel/Google Sheets", "it:3"),
    ],
    "ai": [
        ("AI-автоответчик (ChatGPT)", "ai:1"),
        ("Мониторинг цен и сайтов", "ai:2"),
    ],
    "hosting": [
        ("Хостинг — консультация", "hosting:1"),
    ],
    "macros": [
        ("Автопостинг контента", "macros:1"),
        ("Парсинг данных", "macros:2"),
        ("Автоматизация рутины", "macros:3"),
    ],
}

def products_kb(cat: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=name, callback_data=f"prod:{cb}")]
            for name, cb in PRODUCTS.get(cat, [])]
    rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back:cats")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def product_actions_kb(cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Оставить заявку", callback_data=f"order:{cb}")],
        [InlineKeyboardButton(text="🔒 Безопасная сделка", callback_data="safe:menu")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back:cats")],
    ])

# --- безопасная сделка ---
safe_deal_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔹 Playerok (Play Rock)", callback_data="safe:playerok")],
    [InlineKeyboardButton(text="🔹 Kwork", callback_data="safe:kwork")],
    [InlineKeyboardButton(text="🔹 GG Sell", callback_data="safe:gg")],
    [InlineKeyboardButton(text="↩️ Назад", callback_data="back:main")],
])

def link_kb(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Перейти на сайт", url=url)],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="safe:menu")],
    ])

# --- оценка ---
rating_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=str(i), callback_data=f"rate:{i}") for i in range(0, 6)]
])
