import asyncio
import html
import logging
import math
import os

import aiosqlite
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# ---------------- НАСТРОЙКИ ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
PLAYEROK_URL = os.getenv(
    "PLAYEROK_URL", "https://playerok.com/profile/yunogasaiip/products"
)
DB_PATH = os.getenv("DB_PATH", "shop.db")
REVIEWS_PER_PAGE = 5

# Список товаров. Позже заменим реальными.
PRODUCTS = [
    {"id": "demo1", "title": "Товар 1 (пример)", "price": "000 ₽", "description": "Описание будет позже."},
    {"id": "demo2", "title": "Товар 2 (пример)", "price": "000 ₽", "description": "Описание будет позже."},
]


def get_product(product_id):
    return next((p for p in PRODUCTS if p["id"] == product_id), None)


# ---------------- БАЗА ДАННЫХ ----------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    product_id TEXT NOT NULL,
    product_title TEXT NOT NULL,
    name TEXT NOT NULL,
    contact TEXT NOT NULL,
    task TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    rating INTEGER,
    comment TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def create_order(user_id, username, product_id, product_title, name, contact, task):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO orders (user_id, username, product_id, product_title, name, contact, task) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, product_id, product_title, name, contact, task),
        )
        await db.commit()
        return cur.lastrowid


async def get_order(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return await cur.fetchone()


async def mark_paid(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "UPDATE orders SET status = 'paid' WHERE id = ? AND status = 'new'", (order_id,)
        )
        await db.commit()
        return cur.rowcount > 0


async def set_rating(order_id, user_id, rating):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "UPDATE orders SET rating = ?, status = 'completed', completed_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND user_id = ? AND status = 'paid'",
            (rating, order_id, user_id),
        )
        await db.commit()
        return cur.rowcount > 0


async def set_comment(order_id, user_id, comment):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET comment = ? WHERE id = ? AND user_id = ? AND status = 'completed'",
            (comment, order_id, user_id),
        )
        await db.commit()


async def count_reviews():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
        return (await cur.fetchone())[0]


async def list_reviews(offset, limit):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM orders WHERE status = 'completed' "
            "ORDER BY completed_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return await cur.fetchall()


async def average_rating():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT AVG(rating) FROM orders WHERE status = 'completed' AND rating IS NOT NULL"
        )
        return (await cur.fetchone())[0] or 0


# ---------------- КЛАВИАТУРЫ ----------------
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="🔒 Безопасная сделка", callback_data="safe")],
        [InlineKeyboardButton(text="⭐ Завершённые сделки и отзывы", callback_data="revs:0")],
    ])


def catalog_kb():
    rows = [
        [InlineKeyboardButton(text=f"{p['title']} — {p['price']}", callback_data=f"prod:{p['id']}")]
        for p in PRODUCTS
    ]
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_kb(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Оформить заявку", callback_data=f"order:{product_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog")],
    ])


def cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")],
    ])


def safe_deal_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Перейти на Playerok", url=PLAYEROK_URL)],
        [InlineKeyboardButton(text="⬅️ Выйти в меню", callback_data="menu")],
    ])


def admin_order_kb(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Клиент оплатил товар", callback_data=f"paid:{order_id}")],
    ])


def rating_kb(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"rate:{order_id}:{i}") for i in range(0, 6)],
    ])


def skip_comment_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_comment")],
    ])


def reviews_kb(page, total_pages):
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"revs:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"revs:{page + 1}"))
    rows = [nav] if nav else []
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------- СОСТОЯНИЯ ----------------
class OrderForm(StatesGroup):
    name = State()
    contact = State()
    task = State()


class ReviewForm(StatesGroup):
    comment = State()


router = Router()
WELCOME = "👋 Добро пожаловать в Exe shop!\n\nВыберите раздел:"


# ---------------- МЕНЮ ----------------
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME, reply_markup=main_menu())


@router.callback_query(F.data == "menu")
async def to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(WELCOME, reply_markup=main_menu())
    await call.answer()


@router.callback_query(F.data == "safe")
async def safe_deal(call: CallbackQuery):
    await call.message.edit_text(
        "🔒 Безопасная сделка\n\n"
        "Вот профиль и товары на Playerok для безопасной сделки.\n"
        "Вы можете перейти на сайт или выйти в меню.",
        reply_markup=safe_deal_kb(),
    )
    await call.answer()


# ---------------- КАТАЛОГ И ЗАЯВКА ----------------
@router.callback_query(F.data == "catalog")
async def show_catalog(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🛒 Каталог. Выберите услугу:", reply_markup=catalog_kb())
    await call.answer()


@router.callback_query(F.data.startswith("prod:"))
async def show_product(call: CallbackQuery):
    product = get_product(call.data.split(":", 1)[1])
    if not product:
        await call.answer("Товар не найден", show_alert=True)
        return
    await call.message.edit_text(
        f"<b>{html.escape(product['title'])}</b>\n"
        f"Цена: {html.escape(product['price'])}\n\n"
        f"{html.escape(product['description'])}",
        reply_markup=product_kb(product["id"]),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("order:"))
async def start_order(call: CallbackQuery, state: FSMContext):
    product = get_product(call.data.split(":", 1)[1])
    if not product:
        await call.answer("Товар не найден", show_alert=True)
        return
    await state.clear()
    await state.update_data(product_id=product["id"])
    await state.set_state(OrderForm.name)
    await call.message.edit_text("Как вас зовут? Напишите имя:", reply_markup=cancel_kb())
    await call.answer()


@router.message(OrderForm.name, F.text)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(OrderForm.contact)
    await message.answer(
        "Оставьте контакт для связи (Telegram @username, телефон и т.п.):",
        reply_markup=cancel_kb(),
    )


@router.message(OrderForm.contact, F.text)
async def get_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text.strip())
    await state.set_state(OrderForm.task)
    await message.answer("Опишите вашу задачу:", reply_markup=cancel_kb())


@router.message(OrderForm.task, F.text)
async def get_task(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    product = get_product(data["product_id"])
    if not product:
        await message.answer("Товар больше недоступен.", reply_markup=main_menu())
        return

    user = message.from_user
    task = message.text.strip()
    order_id = await create_order(
        user.id, user.username, product["id"], product["title"],
        data["name"], data["contact"], task,
    )

    uname = f"@{user.username}" if user.username else "нет username"
    await bot.send_message(
        ADMIN_ID,
        f"📩 <b>Новая заявка #{order_id}</b>\n\n"
        f"Товар: {html.escape(product['title'])} — {html.escape(product['price'])}\n"
        f"Имя: {html.escape(data['name'])}\n"
        f"Контакт: {html.escape(data['contact'])}\n"
        f"Telegram: {html.escape(uname)} (id {user.id})\n\n"
        f"Задача:\n{html.escape(task)}",
        reply_markup=admin_order_kb(order_id),
        parse_mode="HTML",
    )

    await message.answer(
        "✅ Ваша заявка отправлена, ожидайте ответа.\n\n"
        "Продавец может быть занят. Оплата товара — после того, "
        "как продавец напишет вам.",
        reply_markup=main_menu(),
    )


# ---------------- ПРОДАВЕЦ: КЛИЕНТ ОПЛАТИЛ ----------------
@router.callback_query(F.data.startswith("paid:"))
async def client_paid(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Только для продавца", show_alert=True)
        return

    order_id = int(call.data.split(":", 1)[1])
    order = await get_order(order_id)
    if not order:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    if not await mark_paid(order_id):
        await call.answer("Уже отмечено как оплаченное", show_alert=True)
        return

    await call.message.edit_text(
        call.message.html_text + "\n\n💰 <b>Оплачено. Запрос отзыва отправлен клиенту.</b>",
        parse_mode="HTML",
        reply_markup=None,
    )
    await bot.send_message(
        order["user_id"],
        "Оставьте отзыв: как прошла сделка?\n"
        "Оцените площадку продаж и продавца от 0 до 5:",
        reply_markup=rating_kb(order_id),
    )
    await call.answer("Готово")


# ---------------- ОТЗЫВЫ ----------------
@router.callback_query(F.data.startswith("rate:"))
async def rate(call: CallbackQuery, state: FSMContext):
    _, order_id, rating = call.data.split(":")
    order_id, rating = int(order_id), int(rating)

    if not await set_rating(order_id, call.from_user.id, rating):
        await call.answer("Оценка уже сохранена", show_alert=True)
        return

    await state.set_state(ReviewForm.comment)
    await state.update_data(order_id=order_id)
    await call.message.edit_text(
        f"Спасибо! Ваша оценка: {rating}/5.\n\n"
        "Напишите сообщение к отзыву или нажмите «Пропустить».",
        reply_markup=skip_comment_kb(),
    )
    await call.answer()


async def notify_review(order_id, bot: Bot):
    order = await get_order(order_id)
    comment = order["comment"] or "—"
    await bot.send_message(
        ADMIN_ID,
        f"⭐ Новый отзыв по заявке #{order_id}: {order['rating']}/5\n{html.escape(comment)}",
        parse_mode="HTML",
    )


@router.message(ReviewForm.comment, F.text)
async def get_comment(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    await set_comment(data["order_id"], message.from_user.id, message.text.strip())
    await message.answer(
        "Спасибо за отзыв! Он появится в разделе «Завершённые сделки и отзывы».",
        reply_markup=main_menu(),
    )
    await notify_review(data["order_id"], bot)


@router.callback_query(F.data == "skip_comment", ReviewForm.comment)
async def skip_comment(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    await call.message.edit_text("Спасибо за оценку!", reply_markup=main_menu())
    await call.answer()
    await notify_review(data["order_id"], bot)


def mask(name):
    return name[0] + "***" if name else "Аноним"


@router.callback_query(F.data.startswith("revs:"))
async def show_reviews(call: CallbackQuery):
    page = int(call.data.split(":", 1)[1])
    total = await count_reviews()
    if total == 0:
        await call.message.edit_text(
            "Пока нет завершённых сделок.", reply_markup=reviews_kb(0, 1)
        )
        await call.answer()
        return

    total_pages = math.ceil(total / REVIEWS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    rows = await list_reviews(page * REVIEWS_PER_PAGE, REVIEWS_PER_PAGE)
    avg = await average_rating()

    lines = [f"⭐ Завершённые сделки: {total} | Средняя оценка: {avg:.1f}/5\n"]
    for r in rows:
        lines.append(
            f"<b>{html.escape(mask(r['name']))}</b> — {html.escape(r['product_title'])}\n"
            f"Оценка: {r['rating']}/5\n"
            f"{html.escape(r['comment']) if r['comment'] else ''}\n"
        )
    lines.append(f"Стр. {page + 1}/{total_pages}")

    await call.message.edit_text(
        "\n".join(lines), reply_markup=reviews_kb(page, total_pages), parse_mode="HTML"
    )
    await call.answer()


# ---------------- ЗАПУСК ----------------
async def main():
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise SystemExit("Не задан BOT_TOKEN")
    if not ADMIN_ID:
        raise SystemExit("Не задан ADMIN_ID")

    await init_db()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
