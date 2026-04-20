from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.db import count_bots, count_users, get_all_users
from config import ADMIN_IDS
from keyboards.inline import get_broadcast_keyboard
from aiogram.enums import ParseMode

router = Router()

class BroadcastStates(StatesGroup):
    waiting_for_message = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    users = await count_users()
    bots = await count_bots()
    text = (
        "<b><tg-emoji emoji-id=\"5870982283724328568\">⚙</tg-emoji> Admin Panel:</b>\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"🤖 Yaratilgan botlar: {bots}\n\n"
        "Xabar tarqatish uchun: /broadcast"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("broadcast"))
async def broadcast_command(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        '<b><tg-emoji emoji-id="6039422865189638057">📣</tg-emoji> Tarqatmoqchi bo\'lgan xabaringizni yuboring.</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_broadcast_keyboard()
    )
    await state.set_state(BroadcastStates.waiting_for_message)


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    await state.clear()
    users = await get_all_users()
    success = 0
    await message.answer("<b><tg-emoji emoji-id=\"5345906554510012647\">🔄</tg-emoji> Xabar tarqatish boshlandi...</b>", parse_mode="HTML")
    
    for user_id in users:
        try:
            await message.send_copy(chat_id=user_id)
            success += 1
        except Exception:
            pass
            
    await message.answer(f"<b><tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> Xabar {success} ta foydalanuvchiga muvaffaqiyatli yetkazildi!</b>", parse_mode="HTML")
