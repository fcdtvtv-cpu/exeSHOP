from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from keyboards import categories, products_kb, product_actions_kb, PRODUCTS
from .order import OrderForm

router = Router()

@router.message(F.text == "🛒 Каталог товаров")
async def open_catalog(message: Message):
    await message.answer("Выберите категорию:", reply_markup=categories)

@router.callback_query(F.data.startswith("cat:"))
async def show_products(call: CallbackQuery):
    cat = call.data.split(":")[1]
    await call.message.edit_text("Выберите товар:", reply_markup=products_kb(cat))

@router.callback_query(F.data == "back:cats")
async def back_cats(call: CallbackQuery):
    await call.message.edit_text("Выберите категорию:", reply_markup=categories)

@router.callback_query(F.data.startswith("prod:"))
async def show_product(call: CallbackQuery):
    cb = call.data.split(":", 1)[1]
    cat = cb.split(":")[0]
    name = next((n for n, c in PRODUCTS[cat] if c == cb), "Товар")
    await call.message.edit_text(
        f"📦 <b>{name}</b>\n\nВыберите действие:",
        reply_markup=product_actions_kb(cb),
        parse_mode="HTML",
    )
