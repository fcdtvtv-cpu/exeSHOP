from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID
from keyboards import PRODUCTS
from database import create_order

router = Router()

class OrderForm(StatesGroup):
    waiting_data = State()

@router.callback_query(F.data.startswith("order:"))
async def start_order(call: CallbackQuery, state: FSMContext):
    cb = call.data.split(":", 1)[1]
    cat = cb.split(":")[0]
    name = next((n for n, c in PRODUCTS[cat] if c == cb), "Товар")

    await state.update_data(product=name)
    await state.set_state(OrderForm.waiting_data)

    await call.message.answer(
        f"Вы выбрали: <b>{name}</b>\n\n"
        "Отправьте одним сообщением:\n"
        "1️⃣ Товар/услуга (уточните)\n"
        "2️⃣ Ваше имя\n"
        "3️⃣ Контакт для связи (Telegram / Discord / др.)\n"
        "4️⃣ Задачу или пожелания",
        parse_mode="HTML",
    )

@router.message(OrderForm.waiting_data)
async def receive_order(message: Message, state: FSMContext):
    data = await state.get_data()
    product = data.get("product", "—")
    text = message.text or ""

    order_id = await create_order(
        message.from_user.id,
        message.from_user.username or "—",
        product,
        "—", "—",
        text,
    )

    # пересылаем админу
    await message.bot.send_message(
        ADMIN_ID,
        f"📥 <b>Новая заявка #{order_id}</b>\n\n"
        f"👤 @{message.from_user.username or '—'} (ID: {message.from_user.id})\n"
        f"📦 Товар: {product}\n\n"
        f"<b>Данные клиента:</b>\n{text}\n\n"
        f"👉 Когда клиент оплатит — нажмите кнопку ниже:",
        parse_mode="HTML",
    )
    await message.bot.send_message(
        ADMIN_ID, f"✅ Клиент оплатил заявку #{order_id}",
        reply_markup=__import__("aiogram").types.InlineKeyboardMarkup(
            inline_keyboard=[[__import__("aiogram").types.InlineKeyboardButton(
                text="✅ Клиент оплатил",
                callback_data=f"paid:{order_id}")]]
        ),
    )

    await message.answer(
        "✅ Ваша заявка отправлена, ожидайте ответа.\n"
        "Продавец может быть занят. Оплата — только после того, как продавец напишет вам.",
    )
    await state.clear()
