import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import init_db, get_all_active_bots
from handlers import user, admin, bot_maker
from child_bot_manager import bot_manager

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    await bot_manager.start_manager()
    active_bots = await get_all_active_bots()
    for bot_data in active_bots:
        token = bot_data['token']
        await bot_manager.start_bot(token)

    if not BOT_TOKEN:
        print("BOT_TOKEN topilmadi. .env faylini tekshiring.")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(bot_maker.router)

    try:
        print("Asosiy bot ishga tushdi!")
        await dp.start_polling(bot)
    finally:
        print("Bot to'xtatilmoqda, resurslar tozalanmoqda...")
        await bot_manager.stop_all()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
