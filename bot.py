import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from database import init_db
from handlers import start, catalog, order, safe_deal, reviews, help

async def main():
    await init_db()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(order.router)       # order раньше catalog (FSM)
    dp.include_router(catalog.router)
    dp.include_router(safe_deal.router)
    dp.include_router(reviews.router)
    dp.include_router(help.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
