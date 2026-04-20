from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from database.db import add_user
from keyboards.inline import main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(message.from_user.id)
    text = (
        "<b>SUBERS Klon — Zayavka trafigini boshqaruvchi yordamchingiz.</b>\n\n"
        "Yangi bot yaratish uchun quyidagi ro'yxatni oching."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard())
