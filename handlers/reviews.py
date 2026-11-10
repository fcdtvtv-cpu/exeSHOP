from aiogram import Router, F
from aiogram.types import Message
from database import get_reviews, avg_rating

router = Router()

@router.message(F.text == "⭐ Отзывы и сделки")
async def show_reviews(message: Message):
    avg, cnt = await avg_rating()
    reviews = await get_reviews()

    text = f"⭐ <b>Средний рейтинг:</b> {avg:.1f} ({cnt} отзывов)\n\n"
    if not reviews:
        text += "Пока отзывов нет — станьте первым!"
    else:
        for name, product, rating, txt, dt in reviews:
            text += f"📦 {product}\n👤 {name or 'Клиент'} — {'⭐'*rating} ({rating}/5)\n💬 {txt}\n\n"

    await message.answer(text[:4000], parse_mode="HTML")
