from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from keyboards import main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в магазин!\n\n"
        "Выберите раздел в меню ниже 👇",
        reply_markup=main_menu,
    )
