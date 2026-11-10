from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID, PLAYEROK_URL, KWORK_URL
from keyboards import safe_deal_kb, link_kb, rating_kb
from database import get_order, mark_paid, save_review

router = Router()

class ReviewForm(StatesGroup):
    waiting_rating = State()
    waiting_text = State()

@router.message(F.text == "🔒 Безопасная сделка")
async def open_safe(message: Message):
    await message.answer("Выберите площадку для безопасной сделки:", reply_markup=safe_deal_kb)

@router.callback_query(F.data == "safe:menu")
async def safe_menu(call: CallbackQuery):
    await call.message.edit_text("Выберите площадку:", reply_markup=safe_deal_kb)

@router.callback_query(F.data == "safe:playerok")
async def safe_playerok(call: CallbackQuery):
    await call.message.edit_text(
        "🔒 Безопасная сделка через Playerok\n\n"
        f"Профиль: {PLAYEROK_URL}",
        reply_markup=link_kb(PLAYEROK_URL),
        disable_web_page_preview=True,
    )

@router.callback_query(F.data == "safe:kwork")
async def safe_kwork(call: CallbackQuery):
    await call.message.edit_text(
        "🔒 Безопасная сделка через Kwork\n\n"
        f"Профиль: {KWORK_URL}",
        reply_markup=link_kb(KWORK_URL),
        disable_web_page_preview=True,
    )

@router.callback_query(F.data == "safe:gg")
async def safe_gg(call: CallbackQuery):
    await call.message.edit_text("🔒 GG Sell — скоро добавим ссылку.")

# --- админ жмёт "клиент оплатил" ---
@router.callback_query(F.data.startswith("paid:"))
async def paid(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Нет доступа", show_alert=True)
    order_id = int(call.data.split(":")[1])
    order = await get_order(order_id)
    if not order:
        return await call.answer("Заявка не найдена")
    await mark_paid(order_id)
    await call.message.edit_text(call.message.text + "\n\n✅ Отмечено как оплачено. Клиенту отправлен запрос отзыва.")

    user_id = order[1]
    try:
        await call.bot.send_message(
            user_id,
            "🎉 Спасибо за покупку!\nОцените сделку и продавца от 0 до 5 ⭐:",
            reply_markup=rating_kb,
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("rate:"))
async def rate(call: CallbackQuery, state: FSMContext):
    rating = int(call.data.split(":")[1])
    await state.update_data(rating=rating, user_id=call.from_user.id)
    await state.set_state(ReviewForm.waiting_text)
    await call.message.edit_text(
        f"Оценка: {rating} ⭐\n\nНапишите комментарий к отзыву (или «-»):"
    )

@router.message(ReviewForm.waiting_text)
async def review_text(message: Message, state: FSMContext):
    data = await state.get_data()
    rating = data["rating"]
    text = message.text or "-"

    # ищем последнюю оплаченную заявку пользователя
    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, name, product FROM orders WHERE user_id=? AND status='paid' ORDER BY id DESC LIMIT 1",
            (message.from_user.id,),
        )
        row = await cur.fetchone()
    if row:
        order_id, name, product = row
        await save_review(order_id, message.from_user.id, name, product, rating, text)

    await message.answer("🙏 Спасибо за отзыв! Он сохранён.")
    await state.clear()
