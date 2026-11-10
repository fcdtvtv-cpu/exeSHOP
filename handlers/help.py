from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import SUPPORT_URL

router = Router()

@router.message(F.text == "🛠 Техподдержка")
async def support(message: Message):
    await message.answer(f"🛠 Поддержка: {SUPPORT_URL}")

@router.message(Command("help"))
@router.message(F.text == "❓ Справка")
async def help_cmd(message: Message):
    await message.answer(
        "❓ <b>Справка по боту</b>\n\n"
        "🛒 <b>Каталог товаров</b> — выбрать товар по категории.\n"
        "📦 <b>Заказать услугу</b> — оставить заявку (товар, имя, контакт, задача).\n"
        "🔒 <b>Безопасная сделка</b> — покупка через Playerok / Kwork / GG Sell.\n"
        "⭐ <b>Отзывы и сделки</b> — посмотреть завершённые сделки и отзывы.\n"
        "🛠 <b>Техподдержка</b> — связаться с продавцом.\n\n"
        "💳 <b>Оплата:</b> после того как продавец напишет вам лично.\n"
        "📩 <b>Заявки</b> приходят продавцу в личные сообщения.",
        parse_mode="HTML",
    )
