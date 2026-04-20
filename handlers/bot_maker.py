from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.db import add_bot, get_bots_by_owner, get_bot, update_bot_field, get_bot_stats, update_bot_fields, import_bot_users, get_bot_user_ids
from keyboards.inline import (
    cancel_keyboard, bot_dashboard_keyboard, bot_messages_keyboard, request_processing_keyboard, 
    bot_list_keyboard, main_menu_keyboard, bot_base_keyboard
)
from child_bot_manager import bot_manager
import os
import json
import aiohttp
from aiogram.types import BufferedInputFile

os.makedirs("media", exist_ok=True)

router = Router()

class BotCreation(StatesGroup):
    waiting_for_token = State()

class ChannelSetup(StatesGroup):
    waiting_for_forward = State()
    bot_token = State()

class LinkGenerator(StatesGroup):
    waiting_for_name = State()
    bot_id = State()
    chat_id = State()
    creates_join_request = State()

class ReqPercentage(StatesGroup):
    waiting_for_percent = State()
    bot_id = State()
    action = State()

class CaptchaMessage(StatesGroup):
    waiting_for_captcha_msg = State()
    bot_id = State()

class WelcomeMessage(StatesGroup):
    waiting_for_welcome_msg = State()
    waiting_for_btn_name = State()
    bot_id = State()
    temp_data = State()

class GoodbyeMessage(StatesGroup):
    waiting_for_goodbye_msg = State()
    waiting_for_btn_name = State()
    bot_id = State()
    temp_data = State()

class LimitInput(StatesGroup):
    waiting_for_count = State()

class MailingSetup(StatesGroup):
    waiting_for_message = State()
    waiting_for_button = State()
    waiting_for_date = State()
class MassMailingSetup(StatesGroup):
    waiting_for_buttons = State()
    waiting_for_random_count = State()
    waiting_for_posts = State()
    bot_id = State()

class BaseManagement(StatesGroup):
    waiting_for_json = State()
    bot_id = State()

@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("<b><tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> Amal bekor qilindi.</b>", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def go_main_menu(callback: CallbackQuery):
    text = (
        "<b>SUBERS Klon — Zayavka trafigini boshqaruvchi yordamchingiz.</b>\n\n"
        "Quyidagi ro'yxatdan kerakli bo'limni tanlang:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "bot_list")
async def show_my_bots(callback: CallbackQuery):
    bots = await get_bots_by_owner(callback.from_user.id)
    
    # Simple fix for missing usernames (self-healing)
    updated = False
    for i, bot_record in enumerate(bots):
        if not bot_record.get('username'):
            try:
                temp_bot = Bot(token=bot_record['token'])
                me = await temp_bot.get_me()
                from database.db import update_bot_field
                await update_bot_field(bot_record['id'], 'username', me.username)
                bots[i] = dict(bot_record)
                bots[i]['username'] = me.username
                updated = True
                await temp_bot.session.close()
            except:
                pass
    
    await callback.message.edit_text(
        "<b>🤖 Botingizni tanlang yoko yangisini yarating:</b>", 
        parse_mode="HTML", 
        reply_markup=bot_list_keyboard(bots)
    )

@router.callback_query(F.data == "create_bot")
async def start_bot_creation(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<b><tg-emoji emoji-id=\"5940433880585605708\">🔨</tg-emoji> Yangi bot yaratmoqdamiz.</b>\n\n"
        "@BotFather dan olingan bot tokenini yuboring.",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(BotCreation.waiting_for_token)
    await callback.answer()

@router.message(BotCreation.waiting_for_token)
async def process_token(message: Message, state: FSMContext):
    token = message.text.strip()
    wait_msg = await message.answer("Tekshirilmoqda...", parse_mode="HTML")
    
    try:
        temp_bot = Bot(token=token)
        me = await temp_bot.get_me()
        await temp_bot.session.close()
    except Exception as e:
        await wait_msg.edit_text("<b><tg-emoji emoji-id=\"5870657884844462243\">❌</tg-emoji> Noto'g'ri token, iltimos qaytatdan yuboring.</b>", parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    try:
        await add_bot(message.from_user.id, token, me.username)
        await wait_msg.edit_text(f"<b><tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> @{me.username} muvaffaqiyatli ulandi!</b>", parse_mode="HTML")
        await bot_manager.start_bot(token)
    except Exception as e:
        await wait_msg.edit_text("<b><tg-emoji emoji-id=\"5870657884844462243\">❌</tg-emoji> Xatolik yuz berdi. Balki bu bot allaqachon qo'shilgandir.</b>", parse_mode="HTML")
        
    await state.clear()
    await message.answer("<b>Bosh menyu:</b>", parse_mode="HTML", reply_markup=main_menu_keyboard())

@router.callback_query(F.data.startswith("bot_menu_"))
async def bot_settings_menu(callback: CallbackQuery):
    bot_id = int(callback.data.split("_")[-1])
    bot = await get_bot(bot_id)
    if not bot: return await callback.answer("Bot topilmadi", show_alert=True)
    
    bot_name = bot.get("username", bot['token'][:10] + "...")
        
    stats = await get_bot_stats(bot['token'])
    sc = stats['users_accepted'] if stats else 0
    sc_c = stats['captcha_passed'] if stats else 0
    sc_w = stats['welcomes_sent'] if stats else 0

    text = (
        f"<tg-emoji emoji-id=\"6030400221232501136\">🤖</tg-emoji> <b>Bot paneli:</b> @{bot_name}\n\n"
        "<tg-emoji emoji-id=\"5870772616305839506\">👥</tg-emoji> <b>Foydalanuvchilar</b>\n"
        "├ Bugun ≈ 0\n"
        "├ Kecha ≈ 0\n"
        f"├ Jami ≈ {sc}\n"
        "└ Navbatda turganlar ≈ 0\n\n"
        "<tg-emoji emoji-id=\"6037249452824072506\">🔒</tg-emoji> <b>Kapcha yechimlari</b>\n"
        "├ Bugun ≈ 0 | 0%\n"
        "├ Kecha ≈ 0 | 0%\n"
        f"└ Jami ≈ {sc_c} | -%\n\n"
        "<tg-emoji emoji-id=\"6039422865189638057\">📩</tg-emoji> <b>Xabarlar</b>\n"
        "├ Bugun ≈ 0\n"
        "├ Kecha ≈ 0\n"
        f"└ Jami ≈ {sc_w}\n\n"
        "🟢 Yashayapti ≈ 0\n"
        "🔴 O'lik (Dead) ≈ 0\n"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=bot_dashboard_keyboard(bot_id))
    await callback.answer()

@router.callback_query(F.data.startswith("req_"))
async def request_processing_router(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    action_or_param = parts[1]
    bot_id = int(parts[2])
    bot = await get_bot(bot_id)
    if not bot: return
    
    if action_or_param == "auto":
        new_val = 0 if bot['auto_accept'] else 1
        await update_bot_field(bot_id, "auto_accept", new_val)
        from keyboards.inline import request_processing_keyboard
        await callback.message.edit_reply_markup(reply_markup=request_processing_keyboard(bot_id, new_val, bot['deferred_time']))
        await callback.answer("Avto-qabul o'zgartirildi!")
        
    elif action_or_param == "defer":
        await callback.answer("Kechikish vaqtini o'zgartirish hozircha faol emas.", show_alert=True)
        
    elif action_or_param in ["accept", "reject"]:
        from keyboards.inline import req_percentage_keyboard
        from database.db import get_pending_requests_count
        count = await get_pending_requests_count(bot['token'])
        action_name = "QABUL QILMOQCHISIZ" if action_or_param == "accept" else "RAD QILMOQCHISIZ"
        
        text = (
            f"<b>Jarayon:</b> {'Hizmatga qabul qilish' if action_or_param == 'accept' else 'Rad etish'}\n"
            f"Hozirda <b>{count} ta</b> zayavka navbatda turibdi. Ularning necha foizini <u>{action_name}</u>?"
        )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=req_percentage_keyboard(bot_id, action_or_param))

    elif action_or_param == "percent":
        # pattern: req_percent_{bot_id}_{action}_{percent}
        sub_action = parts[3]
        percent_str = parts[4]
        
        if percent_str == "custom":
            await callback.message.delete()
            await callback.message.answer(
                "Iltimos, foizni raqamlarda kiriting (Masalan: <b>85</b>):", 
                parse_mode="HTML", reply_markup=cancel_keyboard()
            )
            await state.update_data(bot_id=bot_id, action=sub_action)
            await state.set_state(ReqPercentage.waiting_for_percent)
        else:
            await process_bulk_requests(callback.message, bot, sub_action, int(percent_str))
            
    else:
        await callback.answer("Sozlamalar yangilandi!", show_alert=False)

@router.message(ReqPercentage.waiting_for_percent)
async def process_custom_percent(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Iltimos, faqat musbat butun raqam (misol uchun 20) kiriting:", parse_mode="HTML")
        
    percent = int(message.text)
    if percent <= 0 or percent > 100:
        return await message.answer("⚠️ Foiz 1 va 100 oralig'ida bo'lishi shart:", parse_mode="HTML")
        
    data = await state.get_data()
    bot = await get_bot(data['bot_id'])
    
    await process_bulk_requests(message, bot, data['action'], percent)
    await state.clear()

async def process_bulk_requests(message: Message, bot_config: dict, action: str, percent: int):
    import asyncio
    from database.db import get_pending_requests_count, get_pending_requests, remove_pending_request, add_bot_user, increment_stat
    from child_bot_manager import send_welcome_message, bot_manager
    from keyboards.inline import main_menu_keyboard
    
    count = await get_pending_requests_count(bot_config['token'])
    if count == 0:
        await message.answer("<b>Navbatda zayavkalar yo'q!</b>", parse_mode="HTML", reply_markup=main_menu_keyboard())
        return
        
    amount = int(count * (percent / 100))
    if amount == 0 and percent > 0: amount = 1
    
    requests = await get_pending_requests(bot_config['token'], amount)
    bot = bot_manager.get_bot(bot_config['token'])
    
    msg = await message.answer(f"<b>Guruhlash boshlandi! {amount} ta zayavka ushbu vazifa uchun tanlandi...</b>\n\nJarayon orqa fonda amalga oshmoqda.", parse_mode="HTML", reply_markup=main_menu_keyboard())
    
    if not bot: return
    
    # Orqa fondagi tsikl
    async def bg_worker():
        for r in requests:
            req_id, chat_id, user_id = r
            try:
                if action == 'accept':
                    await bot.approve_chat_join_request(chat_id, user_id)
                    await increment_stat(bot_config['token'], 'users_accepted')
                    await add_bot_user(bot_config['token'], user_id)
                    await send_welcome_message(bot, bot_config, user_id)
                else:
                    await bot.decline_chat_join_request(chat_id, user_id)
                    # Send goodbye with media if set
                    if bot_config.get('goodbye_message'):
                        try:
                            from child_bot_manager import send_goodbye_message
                            await send_goodbye_message(bot, bot_config, user_id)
                        except Exception: pass
                
                await remove_pending_request(bot_config['token'], chat_id, user_id)
                await asyncio.sleep(0.05) # Limitlar uchun xavfsiz va tez uzilish
            except Exception as e:
                pass
                
    asyncio.create_task(bg_worker())

@router.callback_query(F.data.startswith("b_"))
async def dashboard_routing(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    action = parts[1]
    bot_id = int(parts[2])
    
    bot = await get_bot(bot_id)
    if not bot: return

    if action == "processing":
        from keyboards.inline import request_processing_keyboard
        await callback.message.edit_text(
            "<b><tg-emoji emoji-id=\"5870633910337015697\">☑️</tg-emoji> Zayavkalarni qayta ishlash sozlamalari.</b>", 
            parse_mode="HTML", 
            reply_markup=request_processing_keyboard(bot_id, bot['auto_accept'], bot['deferred_time'])
        )
    elif action == "base":
        from database.db import get_bot_user_count
        from keyboards.inline import bot_base_keyboard
        user_count = await get_bot_user_count(bot['token'])
        await callback.message.edit_text(
            f"<tg-emoji emoji-id=\"5870772616305839506\">👤</tg-emoji> <b>Obunachilar bazasi</b>\n\n"
            f"Bot: @{bot['username']}\n"
            f"Jami obunachilar: {user_count}\n\n"
            f"Siz bu yerda bazani JSON formatda import qilishingiz yoki yuklab olishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=bot_base_keyboard(bot_id)
        )
    elif action == "msgs":
        await callback.message.edit_text(
            "<b><tg-emoji emoji-id=\"6037249452824072506\">🔒</tg-emoji> Kapcha</b> — botga yangi a'zo bo'lganda robot emasligini tekshirish.\n\n"
            "<b><tg-emoji emoji-id=\"5870764288364252592\">👋</tg-emoji> Salomlashuv</b> — botga kirganda yuboriladigan xabar.\n\n"
            "<b><tg-emoji emoji-id=\"5870764288364252592\">👋</tg-emoji> Xayrlashuv</b> — botdan chiqganda yuboriladigan xabar.\n\n"
            "Kerakli bo'limni tanlang 🔽", 
            parse_mode="HTML", reply_markup=bot_messages_keyboard(bot_id)
        )
    elif action == "platforms":
        from keyboards.inline import bot_platforms_keyboard
        from database.db import get_channels
        channels = await get_channels(bot['token'])
        await callback.message.edit_text(
            "<b><tg-emoji emoji-id=\"6039451237743595514\">🗂</tg-emoji> Platformalar</b>\nPlatforma - bu ulangan kanal va guruhlarning umumiy nomi.\nKerakli platformani tanlang yoki yangisini qo'shing:", 
            parse_mode="HTML", reply_markup=bot_platforms_keyboard(bot_id, channels)
        )
    elif action == "links":
        from keyboards.inline import bot_links_keyboard
        from database.db import get_channels
        channels = await get_channels(bot['token'])
        if not channels:
            return await callback.answer("🔗 Ssilka yaratish uchun oldin Platformalar bo'limidan Kanal qo'shing!", show_alert=True)
        await callback.message.edit_text(
            "<b><tg-emoji emoji-id=\"5769289093221454192\">🔗</tg-emoji> Ssilkalar</b>\nQaysi kanal uchun Ssilka tayyorlanishini tanlang:", 
            parse_mode="HTML", reply_markup=bot_links_keyboard(bot_id, channels)
        )
    elif action == "protection":
        from keyboards.inline import protection_keyboard
        await callback.message.edit_text(
            "<b><tg-emoji emoji-id=\"6037243349675544634\">🛡</tg-emoji> Himoya</b>\n\nFiltrlarni yoqsangiz, zayavka yuborgan foydalanuvchi tekshiriladi. Shart bajarilmasa — zayavka <b>avtomatik rad</b> etiladi.\n\n🟢 — Yoqilgan  ⚪️ — O'chirilgan",
            parse_mode="HTML", reply_markup=protection_keyboard(bot_id, bot)
        )
    elif action == "mailings":
        from keyboards.inline import mailing_main_keyboard
        await callback.message.edit_text(
            "<b><tg-emoji emoji-id=\"6039422865189638057\">📨</tg-emoji> Yubormalar (Rassilka)</b>\n\nBu yerdan tezkor va rejalashtirilgan ommaviy xabarlarni yuborishingiz mumkin. "
            "<i>(Premium emojilar qo'llab quvvatlanadi, matnga oddiy qilib qo'shavering)</i>",
            parse_mode="HTML", reply_markup=mailing_main_keyboard(bot_id)
        )
    else:
        # For delete or other undefined actions
        await callback.answer(f"Ushbu bo'lim ({action}) hali mavjud emas.", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("prot_limit_"))
async def prot_limit_menu(callback: CallbackQuery):
    from keyboards.inline import limit_keyboard
    bot_id = int(callback.data.split("_")[2])
    bot = await get_bot(bot_id)
    if not bot:
        return await callback.answer("Bot topilmadi!", show_alert=True)
    await callback.message.edit_text(
        "<b>⛔ Limit</b>\n\n<i>Belgilangan vaqt ichida ko'p zayavka kelsa, ortiqchalari avtomatik rad etiladi.\nLimit yoqilganda yangi ulanishlar <b>Check</b> orqali nazorat qilinadi.</i>",
        parse_mode="HTML", reply_markup=limit_keyboard(bot_id, bot)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("prot_"))
async def protection_toggle(callback: CallbackQuery):
    from keyboards.inline import protection_keyboard
    parts = callback.data.split("_")
    # prot_<filter>_<bot_id>
    filter_type = parts[1]   # hieroglyphs, rtl, nophoto
    bot_id = int(parts[2])
    
    field_map = {
        'hieroglyphs': 'filter_hieroglyphs',
        'rtl': 'filter_rtl',
        'nophoto': 'filter_no_photo',
    }
    field = field_map.get(filter_type)
    if not field:
        return await callback.answer()
    
    bot = await get_bot(bot_id)
    if not bot:
        return await callback.answer("Bot topilmadi!", show_alert=True)
    
    new_val = 0 if bot.get(field, 0) else 1
    await update_bot_field(bot_id, field, new_val)
    bot[field] = new_val  # update locally for keyboard re-render
    
    await callback.message.edit_text(
        "<b>🛡 Himoya</b>\n\nFiltrlarni yoqsangiz, zayavka yuborgan foydalanuvchi tekshiriladi. Shart bajarilmasa — zayavka <b>avtomatik rad</b> etiladi.\n\n🟢 — Yoqilgan  ⚪️ — O'chirilgan",
        parse_mode="HTML", reply_markup=protection_keyboard(bot_id, bot)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lim_"))
async def limit_toggle(callback: CallbackQuery, state: FSMContext):
    from keyboards.inline import limit_keyboard
    from database.db import update_bot_fields
    parts = callback.data.split("_")
    action = parts[1]   # check, pun, time, count
    bot_id = int(parts[2])
    
    bot = await get_bot(bot_id)
    if not bot:
        return await callback.answer("Bot topilmadi!", show_alert=True)
    
    if action == "check":
        new_val = 0 if bot.get('limit_check', 0) else 1
        await update_bot_field(bot_id, 'limit_check', new_val)
        bot['limit_check'] = new_val
    
    elif action == "pun":
        new_pun = "ban" if bot.get('limit_punishment', 'kick') == 'kick' else 'kick'
        await update_bot_field(bot_id, 'limit_punishment', new_pun)
        bot['limit_punishment'] = new_pun
    
    elif action == "time":
        time_cycle = [1, 5, 15, 30, 60, 180]
        cur = bot.get('limit_time', 1)
        idx = time_cycle.index(cur) if cur in time_cycle else 0
        new_time = time_cycle[(idx + 1) % len(time_cycle)]
        await update_bot_field(bot_id, 'limit_time', new_time)
        bot['limit_time'] = new_time
    
    elif action == "count":
        # Show FSM to enter custom count
        await callback.message.answer(
            "<b>⛔ Yangi limit sonini kiriting:</b>\n<i>Masalan: 50 (1 vaqt oralig'ida nechta zayavka qabul qilinsin)</i>",
            parse_mode="HTML"
        )
        await state.update_data(bot_id=bot_id, lim_action="count")
        await state.set_state(LimitInput.waiting_for_count)
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "<b>⛔ Limit</b>\n\n<i>Belgilangan vaqt ichida ko'p zayavka kelsa, ortiqchalari avtomatik rad etiladi.\nLimit yoqilganda yangi ulanishlar <b>Check</b> orqali nazorat qilinadi.</i>",
        parse_mode="HTML", reply_markup=limit_keyboard(bot_id, bot)
    )
    await callback.answer()


@router.message(LimitInput.waiting_for_count)
async def limit_count_input(message: Message, state: FSMContext):
    from keyboards.inline import limit_keyboard
    if not message.text or not message.text.strip().isdigit():
        return await message.answer("⚠️ Faqat son kiriting! Masalan: <code>50</code>", parse_mode="HTML")
    
    data = await state.get_data()
    bot_id = data.get("bot_id")
    count = int(message.text.strip())
    if count < 1:
        return await message.answer("⚠️ Limit kamida 1 bo'lishi kerak!", parse_mode="HTML")
    
    await update_bot_field(bot_id, 'join_limit', count)
    bot = await get_bot(bot_id)
    await state.clear()
    await message.answer(
        f"<b>✅ Limit {count} ta qilib belgilandi!</b>\n\n<b>⛔ Limit menyusi:</b>",
        parse_mode="HTML", reply_markup=limit_keyboard(bot_id, bot)
    )


@router.callback_query(F.data.startswith("msgset_"))
async def msgset_handler(callback: CallbackQuery, state: FSMContext):

    parts = callback.data.split("_")
    bot_id = int(parts[1])
    msg_type = parts[2]
    
    if msg_type == 'welcome':
        await callback.message.delete()
        await callback.message.answer(
            "<b><tg-emoji emoji-id=\"5886285355279193209\">🎉</tg-emoji> Xush kelibsiz xabarini yuboring.</b>\nRasm, video va/yoki izoh yuborishingiz mumkin.", 
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
        await state.update_data(bot_id=bot_id)
        await state.set_state(WelcomeMessage.waiting_for_welcome_msg)
    elif msg_type == 'captcha':
        await callback.message.delete()
        await callback.message.answer(
            "<b><tg-emoji emoji-id=\"6037249452824072506\">🔒</tg-emoji> Kapcha Xabarini yuboring.</b>\nRasm, video va/yoki tagiga izoh matn yozishingiz mumkin. "
            "Ostida paydo bo'ladigan tugma nomini keyinroq kiritasiz.", 
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
        await state.update_data(bot_id=bot_id)
        await state.set_state(CaptchaMessage.waiting_for_captcha_msg)
    elif msg_type == 'goodbye':
        await callback.message.delete()
        await callback.message.answer(
            "<b>👋 Xayrlashuv xabarini yuboring.</b>\nRasm, video va/yoki izoh yuborishingiz mumkin.\n\n"
            "<i>Agar xayrlashuv xabarini o'chirmoqchi bo'lsangiz, <code>off</code> deb yozing.</i>", 
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
        await state.update_data(bot_id=bot_id)
        await state.set_state(GoodbyeMessage.waiting_for_goodbye_msg)
    else:
        await callback.answer("Bu funksiya hozircha qo'shilmagan!", show_alert=True)
        return
    await callback.answer()

@router.callback_query(F.data.startswith("chanlist_"))
async def chanlist_handler(callback: CallbackQuery):
    bot_id = int(callback.data.split("_")[1])
    bot = await get_bot(bot_id)
    if not bot: return
    
    from database.db import get_channels
    channels = await get_channels(bot['token'])
    if not channels:
        await callback.answer("Hali birorta ham kanal ulanmagan!", show_alert=True)
        return
        
    from keyboards.inline import bot_channels_keyboard
    text = "<b>Ulangan Kanallar:</b>\n\n"
    for c in channels:
        text += f"- {c['chat_title']} (ID: <code>{c['chat_id']}</code>)\n"
    from keyboards.inline import main_menu_keyboard # fallback if needed
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=bot_channels_keyboard(bot_id))

@router.callback_query(F.data.startswith("plat_"))
async def plat_manage_handler(callback: CallbackQuery):
    parts = callback.data.split("_")
    bot_id = int(parts[1])
    chat_id = int(parts[2])
    bot = await get_bot(bot_id)
    if not bot: return
    
    from database.db import get_channels
    channels = await get_channels(bot['token'])
    target_channel = next((c for c in channels if c['chat_id'] == chat_id), None)
    if not target_channel: return
    
    from keyboards.inline import platform_manage_keyboard
    text = (
        f"<b>🗂 Platforma:</b> {target_channel['chat_title']}\n\n"
        "🟢 Holati: Ulangan\n"
        "Boshqarish uchun tugmalardan foydalaning🔽"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=platform_manage_keyboard(bot_id, chat_id))

@router.callback_query(F.data.startswith("platdel_"))
async def plat_delete_handler(callback: CallbackQuery):
    parts = callback.data.split("_")
    bot_id = int(parts[1])
    chat_id = int(parts[2])
    bot = await get_bot(bot_id)
    if not bot: return
    
    from database.db import delete_channel
    await delete_channel(bot['token'], chat_id)
    await callback.answer("Platforma muvaffaqiyatli o'chirib tashlandi!", show_alert=True)
    
    from database.db import get_channels
    from keyboards.inline import bot_platforms_keyboard
    channels = await get_channels(bot['token'])
    await callback.message.edit_text(
        "<b>🗂 Platformalar</b>\nPlatforma - bu ulangan kanal va guruhlarning umumiy nomi.\nKerakli platformani tanlang yoki yangisini qo'shing:", 
        parse_mode="HTML", reply_markup=bot_platforms_keyboard(bot_id, channels)
    )

@router.callback_query(F.data.startswith("platadd_"))
async def chanadd_handler(callback: CallbackQuery, state: FSMContext):
    bot_id = int(callback.data.split("_")[1])
    bot = await get_bot(bot_id)
    if not bot: return
    
    await callback.message.delete()
    await callback.message.answer(
        "<b><tg-emoji emoji-id=\"6030400221232501136\">➕</tg-emoji> Kanal Qo'shish:</b>\n"
        "Zayavka botingizni o'z kanalingizga qo'shib <i>Admin</i> bering. "
        "So'ngra, o'sha kanaldan ixtiyoriy bitta xabarni men tomonga <b>Forward (Uzatmoq)</b> qilib yuboring:", 
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await state.update_data(bot_token=bot['token'])
    await state.set_state(ChannelSetup.waiting_for_forward)

@router.message(ChannelSetup.waiting_for_forward)
async def process_channel_forward(message: Message, state: FSMContext):
    if not message.forward_origin:
        return await message.answer("Iltimos, aynan kanaldan xabarni FORWARD qilib yuboring!", reply_markup=cancel_keyboard())
        
    chat = None
    if getattr(message.forward_origin, 'chat', None):
        chat = message.forward_origin.chat
    else:
        return await message.answer("Sizning ushbu xabaringizda Kanal ID si topilmadi (Hidden). Iltimos o'zingiz Admin bo'lgan asosiy kanaldan xabar forvard qiling.", reply_markup=cancel_keyboard())
        
    data = await state.get_data()
    bot_token = data.get("bot_token")
    
    from database.db import add_channel
    success = await add_channel(bot_token, chat.id, chat.title)
    if success:
        from keyboards.inline import main_menu_keyboard
        await message.answer(f"<b><tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> {chat.title} platforma muvaffaqiyatli ulandi!</b>", parse_mode="HTML", reply_markup=main_menu_keyboard())
    else:
        from keyboards.inline import main_menu_keyboard
        await message.answer("<b>Bu kanal allaqachon botga ulangan!</b>", parse_mode="HTML", reply_markup=main_menu_keyboard())
    await state.clear()


### LINK GENERATOR FLOW ###
@router.callback_query(F.data.startswith("linknew_"))
async def linknew_handler(callback: CallbackQuery):
    parts = callback.data.split("_")
    bot_id = int(parts[1])
    chat_id = int(parts[2])
    bot = await get_bot(bot_id)
    if not bot: return
    
    from keyboards.inline import link_type_keyboard
    await callback.message.edit_text(
        "<b>🔗 Ssilka turini tanlang:</b>", parse_mode="HTML", reply_markup=link_type_keyboard(bot_id, chat_id)
    )

@router.callback_query(F.data.startswith("linktype_"))
async def linktype_handler(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    bot_id = int(parts[1])
    chat_id = int(parts[2])
    link_type = parts[3]
    
    creates_join_request = (link_type == "req")
    
    await callback.message.delete()
    await callback.message.answer(
        "<b>Ajoyib! Endi bu ssilkaga chiroyli nom bering (Masalan: Konkurs ssilka):</b>", 
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await state.update_data(bot_id=bot_id, chat_id=chat_id, creates_join_request=creates_join_request)
    await state.set_state(LinkGenerator.waiting_for_name)

@router.message(LinkGenerator.waiting_for_name)
async def process_link_name(message: Message, state: FSMContext):
    name = message.text.strip()
    data = await state.get_data()
    bot_id = data['bot_id']
    chat_id = data['chat_id']
    req = data['creates_join_request']
    
    bot_config = await get_bot(bot_id)
    child_bot = Bot(token=bot_config['token'])
    
    try:
        invite_link = await child_bot.create_chat_invite_link(
            chat_id=chat_id,
            name=name,
            creates_join_request=req
        )
        await child_bot.session.close()
        
        from keyboards.inline import main_menu_keyboard
        t_type = "Zayavkali" if req else "Oddiy"
        await message.answer(f"<b><tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> Ssilka Tayyor!</b>\n\nNomi: {name}\nTuri: {t_type}\n\nManzil: {invite_link.invite_link}", parse_mode="HTML", reply_markup=main_menu_keyboard())
        await state.clear()
    except Exception as e:
        await child_bot.session.close()
        err = str(e)
        from keyboards.inline import main_menu_keyboard
        if "not enough rights" in err.lower() or "administrator" in err.lower():
            await message.answer("<b>❌ Xatolik:</b> Bot bu kanalda Ssilka yaratish uchun yetarli huquq-adminlikka (Invite Users) ega emas!", parse_mode="HTML", reply_markup=main_menu_keyboard())
        else:
            await message.answer(f"<b>❌ Nomalum xatolik ssilka yaratishda:</b> {err}", parse_mode="HTML", reply_markup=main_menu_keyboard())
        await state.clear()

### CAPTCHA MESSAGE SETUP FLOW ###
@router.message(CaptchaMessage.waiting_for_captcha_msg)
async def captcha_msg_received(message: Message, state: FSMContext):
    data = await state.get_data()
    bot_id = data.get("bot_id")
    file_id = None
    file_type = None
    caption = message.html_text or ""
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
        file_path = f"media/{file_id}.jpg"
        await message.bot.download(message.photo[-1], destination=file_path)
        file_id = file_path
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
        file_path = f"media/{file_id}.mp4"
        await message.bot.download(message.video, destination=file_path)
        file_id = file_path
        
    await update_bot_fields(bot_id, {
        "captcha_text": caption,
        "captcha_file_id": file_id,
        "captcha_file_type": file_type
    })
    
    await message.answer("<b>Yaxshi! Endi kapcha ostida chiqadigan tugma matnini yuboring (Masalan: ✅ Men robot emasman):</b>", parse_mode="HTML")
    await state.set_state(CaptchaMessage.bot_id)

@router.message(CaptchaMessage.bot_id)
async def captcha_btn_received(message: Message, state: FSMContext):
    data = await state.get_data()
    bot_id = data.get("bot_id")
    btn_text = message.text.strip()
    
    from keyboards.inline import bot_messages_keyboard
    await update_bot_field(bot_id, "captcha_btn_text", btn_text)
    await message.answer("<b><tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> Kapcha xabari va tugma muvaffaqiyatli saqlandi!</b>\n\n📩 Xabarlar bo'limi:", parse_mode="HTML", reply_markup=bot_messages_keyboard(bot_id))
    await state.clear()

### WELCOME MESSAGE SETUP FLOW ###
@router.message(WelcomeMessage.waiting_for_welcome_msg)
async def welcome_msg_received(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id, file_type = None, None
    caption = message.html_text or ""
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
        file_path = f"media/{file_id}.jpg"
        await message.bot.download(message.photo[-1], destination=file_path)
        file_id = file_path
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
        file_path = f"media/{file_id}.mp4"
        await message.bot.download(message.video, destination=file_path)
        file_id = file_path
        
    await state.update_data(temp_data={
        "welcome_message": caption,
        "welcome_file_id": file_id,
        "welcome_file_type": file_type
    })
    
    await message.answer("<b>Juda yaxshi! Endi tugma uchun malumotlarni quyidagi shablonda yuboring:</b>\n\n<code>Tugma nomi - https://manzil.com ::blue</code>\n\n📌 <i>Ranglar: ::blue, ::red, ::green</i>\n📌 <i>Premium emojini matn boshiga oddiy qo'shib yuboravering, bot o'zi o'qiydi.</i>", parse_mode="HTML")
    await state.set_state(WelcomeMessage.waiting_for_btn_name)

@router.message(WelcomeMessage.waiting_for_btn_name)
async def welcome_btn_name(message: Message, state: FSMContext):
    import re
    text = message.text or message.caption or ""
    
    match = re.match(r"^(.*?)\s*-\s*(https?://.*?)(?:\s*::(blue|red|green))?$", text.strip(), re.IGNORECASE)
    if not match:
        return await message.answer("⚠️ Format noto'g'ri. Iltimos shablondagidek kiriting:\n\n<code>Tugma nomi - https://manzil.com ::blue</code>", parse_mode="HTML")
        
    btn_text = match.group(1).strip()
    url = match.group(2).strip()
    color_map = {'blue': 'primary', 'red': 'danger', 'green': 'success'}
    style = color_map.get(match.group(3).lower()) if match.group(3) else None
    
    emoji_id = None
    if message.entities:
        for ent in message.entities:
            if ent.type == 'custom_emoji':
                emoji_id = ent.custom_emoji_id
                # Get the fallback emoji character
                fallback_char = ent.extract_from(message.text or message.caption or "")
                # Remove it so we don't get double emojis (Premium + Fallback)
                btn_text = btn_text.replace(fallback_char, "", 1).strip()
                break

    data = await state.get_data()
    bot_id = data.get("bot_id")
    temp_data = data.get("temp_data", {})
    temp_data["welcome_btn_text"] = btn_text
    temp_data["welcome_btn_url"] = url
    temp_data["welcome_btn_style"] = style
    temp_data["welcome_btn_emoji_id"] = emoji_id
    
    from keyboards.inline import bot_messages_keyboard
    await update_bot_fields(bot_id, temp_data)
    await message.answer("<b><tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> Xush kelibsiz xabari va oynali tugma to'liq sozlandi!</b>\n\n📩 Xabarlar bo'limi:", parse_mode="HTML", reply_markup=bot_messages_keyboard(bot_id))
    await state.clear()

# ==================== GOODBYE MESSAGE ====================

@router.message(GoodbyeMessage.waiting_for_goodbye_msg)
async def goodbye_msg_received(message: Message, state: FSMContext):
    data = await state.get_data()
    bot_id = data.get("bot_id")
    
    # "off" — xayrlashuvni butunlay o'chirish
    if message.text and message.text.strip().lower() == 'off':
        await update_bot_fields(bot_id, {
            'goodbye_message': None, 'goodbye_file_id': None, 'goodbye_file_type': None,
            'goodbye_btn_text': None, 'goodbye_btn_url': None, 'goodbye_btn_style': None, 'goodbye_btn_emoji_id': None
        })
        from keyboards.inline import bot_messages_keyboard
        await message.answer("<b>✅ Xayrlashuv xabari o'chirildi!</b>\n\n📩 Xabarlar bo'limi:", parse_mode="HTML", reply_markup=bot_messages_keyboard(bot_id))
        await state.clear()
        return

    file_id, file_type = None, None
    caption = message.html_text or ""
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
        file_path = f"media/{file_id}.jpg"
        await message.bot.download(message.photo[-1], destination=file_path)
        file_id = file_path
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
        file_path = f"media/{file_id}.mp4"
        await message.bot.download(message.video, destination=file_path)
        file_id = file_path
        
    await state.update_data(temp_data={
        "goodbye_message": caption,
        "goodbye_file_id": file_id,
        "goodbye_file_type": file_type
    })
    
    await message.answer("<b>Juda yaxshi! Endi tugma uchun malumotlarni quyidagi shablonda yuboring:</b>\n\n<code>Tugma nomi - https://manzil.com ::blue</code>\n\n📌 <i>Ranglar: ::blue, ::red, ::green</i>\n📌 <i>Premium emojini matn boshiga oddiy qo'shib yuboravering.</i>\n\n<i>Agar tugma kerak bo'lmasa, <code>skip</code> deb yozing.</i>", parse_mode="HTML")
    await state.set_state(GoodbyeMessage.waiting_for_btn_name)

@router.message(GoodbyeMessage.waiting_for_btn_name)
async def goodbye_btn_name(message: Message, state: FSMContext):
    import re
    text = message.text or message.caption or ""
    
    data = await state.get_data()
    bot_id = data.get("bot_id")
    temp_data = data.get("temp_data", {})
    
    # "skip" — tugmasiz saqlash
    if text.strip().lower() == 'skip':
        temp_data["goodbye_btn_text"] = None
        temp_data["goodbye_btn_url"] = None
        temp_data["goodbye_btn_style"] = None
        temp_data["goodbye_btn_emoji_id"] = None
        await update_bot_fields(bot_id, temp_data)
        from keyboards.inline import bot_messages_keyboard
        await message.answer("<b><tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> Xayrlashuv xabari sozlandi! (Tugmasiz)</b>\n\n📩 Xabarlar bo'limi:", parse_mode="HTML", reply_markup=bot_messages_keyboard(bot_id))
        await state.clear()
        return
    
    match = re.match(r"^(.*?)\s*-\s*(https?://.*?)(?:\s*::(blue|red|green))?$", text.strip(), re.IGNORECASE)
    if not match:
        return await message.answer("⚠️ Format noto'g'ri. Iltimos shablondagidek kiriting:\n\n<code>Tugma nomi - https://manzil.com ::blue</code>\n\n<i>Yoki <code>skip</code> deb yozing.</i>", parse_mode="HTML")
        
    btn_text = match.group(1).strip()
    url = match.group(2).strip()
    color_map = {'blue': 'primary', 'red': 'danger', 'green': 'success'}
    style = color_map.get(match.group(3).lower()) if match.group(3) else None
    
    emoji_id = None
    if message.entities:
        for ent in message.entities:
            if ent.type == 'custom_emoji':
                emoji_id = ent.custom_emoji_id
                fallback_char = ent.extract_from(message.text or message.caption or "")
                btn_text = btn_text.replace(fallback_char, "", 1).strip()
                break

    temp_data["goodbye_btn_text"] = btn_text
    temp_data["goodbye_btn_url"] = url
    temp_data["goodbye_btn_style"] = style
    temp_data["goodbye_btn_emoji_id"] = emoji_id
    
    from keyboards.inline import bot_messages_keyboard
    await update_bot_fields(bot_id, temp_data)
    await message.answer("<b><tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> Xayrlashuv xabari va tugma to'liq sozlandi!</b>\n\n📩 Xabarlar bo'limi:", parse_mode="HTML", reply_markup=bot_messages_keyboard(bot_id))
    await state.clear()


# ==================== MAILING SYSTEM ====================

def get_mailing_info_text(bot: dict, m: dict) -> str:
    st_txt = {'draft': 'Draft', 'scheduled': 'Scheduled', 'running': 'Running', 'paused': 'Paused', 'completed': 'Tugallangan ✅'}.get(m['status'], m['status'].capitalize())
    
    import datetime
    tz_uz = datetime.timezone(datetime.timedelta(hours=5))
    if m['schedule_time'] > 0:
        start_dt = datetime.datetime.fromtimestamp(m['schedule_time'], tz_uz).strftime('%d.%m.%Y %H:%M')
    else:
        start_dt = datetime.datetime.fromtimestamp(m['created_at'], tz_uz).strftime('%d.%m.%Y %H:%M')

    total = m['total_cnt'] if m['total_cnt'] else 0
    sent = m['sent_cnt']
    blocked = m.get('blocked_cnt', 0)
    attempted = sent + blocked
    percent = int((attempted / total * 100)) if total > 0 else 0

    bar_len = 10
    filled = int(percent / 10)
    bar = "▇" * filled + "▬" * (bar_len - filled)

    speed_txt = {'low': 'Minimum (~1/sec)', 'medium': 'Normal (~5/sec)', 'high': 'Maximum (~15/sec)'}.get(m['speed'], 'Medium')

    info = f"🚀 <b>Mailing:</b> @{bot.get('username', bot['token'][:10])}\n\n"
    info += f"📊 <code>{bar}</code> {percent}%\n\n"
    info += f"⸬ <b>Status:</b> {st_txt}\n\n"
    info += f"↪ <b>Sent:</b> {attempted} of {total}\n\n"
    info += f"✅ <b>Received:</b> {sent}\n"
    info += f"❌ <b>Blocked:</b> {blocked}\n\n"
    info += f"🟢 <b>Speed:</b> {speed_txt}\n\n"
    info += f"🗓 <b>Start date:</b> {start_dt}"
    return info

def get_mass_info_text(bot: dict, s: dict) -> str:
    import json
    btns = []
    if s.get('buttons_json'):
        btns = json.loads(s['buttons_json'])
    
    speed_txt = {'low': 'Minimum (~1/sec)', 'medium': 'Normal (~5/sec)', 'high': 'Maximum (~15/sec)'}.get(s.get('speed', 'medium'), 'Medium')
    
    info = f"📦 <b>Ommaviy Rassilka (Mass Mailing):</b> @{bot.get('username', bot['token'][:10])}\n\n"
    info += f"Bitta postga qoshib beriladigan\n"
    info += f"random URL-tugmalar soni: <b>{s.get('random_btn_count', 1)} ta</b>\n"
    info += f"Saqlangan jami URL-tugmalar: <b>{len(btns)} ta</b>\n\n"
    info += f"🟢 <b>Tasdiqlangan Tezlik:</b> {speed_txt}\n\n"
    info += f"<i>Quyidagi sozlamalar navbatdagi rejalashtirib qoyiladigan barcha postlarga tadbiq etiladi!</i>"
    return info

@router.callback_query(F.data.startswith("mail_"))
async def mailing_routing(callback: CallbackQuery, state: FSMContext):
    from database.db import create_mailing, get_scheduled_mailings, get_mailing, update_mailing, delete_mailing, get_bot
    from keyboards.inline import mailing_main_keyboard, mailing_list_keyboard, mailing_editor_keyboard
    
    parts = callback.data.split("_")
    action = parts[1]
    bot_id = int(parts[2])
    bot = await get_bot(bot_id)
    if not bot: return await callback.answer("Bot topilmadi", show_alert=True)
    
    if action == "main":
        await callback.message.edit_text(
            "<b>📨 Yubormalar (Rassilka)</b>\n\nBu yerdan tezkor va rejalashtirilgan ommaviy xabarlarni yuborishingiz mumkin. "
            "<i>(Premium emojilar qo'llab quvvatlanadi, matnga oddiy qilib qo'shavering)</i>",
            parse_mode="HTML", reply_markup=mailing_main_keyboard(bot_id)
        )
    
    elif action == "create":
        # Create draft mailing, then go to editor
        m_id = await create_mailing(bot['token'])
        m = await get_mailing(m_id)
        info = get_mailing_info_text(bot, m)
        await callback.message.edit_text(
            info,
            parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m)
        )
    
    elif action == "list":
        mailings = await get_scheduled_mailings(bot['token'])
        text = "<b>🗓 Rejalashtirilgan va Faol rassilkalar:</b>\n" if mailings else "<b>🗓 Hozircha hech qanday rassilka yo'q.</b>"
        await callback.message.edit_text(
            text, parse_mode="HTML", reply_markup=mailing_list_keyboard(bot_id, mailings)
        )
        
    elif action == "edit":
        m_id = int(parts[3])
        m = await get_mailing(m_id)
        if not m: return await callback.answer("Rassilka topilmadi!", show_alert=True)
        info = get_mailing_info_text(bot, m)
        await callback.message.edit_text(info, parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
        
    elif action == "del":
        m_id = int(parts[3])
        await delete_mailing(m_id)
        await callback.answer("O'chirildi!", show_alert=True)
        mailings = await get_scheduled_mailings(bot['token'])
        await callback.message.edit_text(
            "<b>🗓 Rejalashtirilgan va Faol rassilkalar:</b>" if mailings else "<b>🗓 Hozircha hech qanday rassilka yo'q.</b>",
            parse_mode="HTML", reply_markup=mailing_list_keyboard(bot_id, mailings)
        )
        
    elif action == "setmsg":
        m_id = int(parts[3])
        await callback.message.delete()
        await callback.message.answer(
            "<b>📨 Rassilka matnini (media ham mumkin) yuboring.</b>", 
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
        await state.update_data(bot_id=bot_id, mailing_id=m_id)
        await state.set_state(MailingSetup.waiting_for_message)
        
    elif action == "setbtn":
        m_id = int(parts[3])
        await callback.message.delete()
        await callback.message.answer(
            "<b>🔗 Tugma o'rnatish uchun malumotlarni quyidagi shablonda yuboring:</b>\n\n<code>Tugma nomi - https://manzil.com ::blue</code>\n\n<i>Kerak bo'lmasa <code>skip</code> deb yozing.</i>", 
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
        await state.update_data(bot_id=bot_id, mailing_id=m_id)
        await state.set_state(MailingSetup.waiting_for_button)
        
    elif action == "togpreview":
        m_id = int(parts[3])
        m = await get_mailing(m_id)
        nval = 0 if m.get('disable_preview') else 1
        await update_mailing(m_id, {'disable_preview': nval})
        m['disable_preview'] = nval
        await callback.message.edit_text(get_mailing_info_text(bot, m), parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
        
    elif action == "tognotify":
        m_id = int(parts[3])
        m = await get_mailing(m_id)
        nval = 0 if m.get('disable_notify') else 1
        await update_mailing(m_id, {'disable_notify': nval})
        m['disable_notify'] = nval
        await callback.message.edit_text(get_mailing_info_text(bot, m), parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
        
    elif action == "togprotect":
        m_id = int(parts[3])
        m = await get_mailing(m_id)
        nval = 0 if m.get('protect_content') else 1
        await update_mailing(m_id, {'protect_content': nval})
        m['protect_content'] = nval
        await callback.message.edit_text(get_mailing_info_text(bot, m), parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
        
    elif action == "togpin":
        m_id = int(parts[3])
        m = await get_mailing(m_id)
        nval = 0 if m.get('pin_message') else 1
        await update_mailing(m_id, {'pin_message': nval})
        m['pin_message'] = nval
        await callback.message.edit_text(get_mailing_info_text(bot, m), parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
        

    elif action == "speed":
        m_id = int(parts[3])
        m = await get_mailing(m_id)
        cycle = ['low', 'medium', 'high']
        cur = m['speed']
        idx = cycle.index(cur) if cur in cycle else 0
        new_speed = cycle[(idx + 1) % len(cycle)]
        await update_mailing(m_id, {'speed': new_speed})
        m['speed'] = new_speed
        await callback.message.edit_text(get_mailing_info_text(bot, m), parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
        
    elif action == "pause":
        m_id = int(parts[3])
        await update_mailing(m_id, {'status': 'paused'})
        m = await get_mailing(m_id)
        await callback.message.edit_text(get_mailing_info_text(bot, m), parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
        
    elif action == "resume":
        m_id = int(parts[3])
        await update_mailing(m_id, {'status': 'running'})
        m = await get_mailing(m_id)
        await callback.message.edit_text(get_mailing_info_text(bot, m), parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
        
    elif action == "sched":
        m_id = int(parts[3])
        await callback.message.delete()
        await callback.message.answer(
            "<b>⏰ Rassilka boshlanish vaqtini yuboring.</b>\nFormat: <code>YYYY-MM-DD HH:MM</code> (Masalan: 2026-04-20 15:30)\n\n<i>Eslatma: Vaqt Toshkent vaqti bilan kiritilishi kerak!</i>", 
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
        await state.update_data(bot_id=bot_id, mailing_id=m_id)
        await state.set_state(MailingSetup.waiting_for_date)
        
    elif action == "start":
        m_id = int(parts[3])
        m = await get_mailing(m_id)
        if not m['message'] and not m['file_id']:
            return await callback.answer("Oldin xabar matnini kiriting!", show_alert=True)
            
        from database.db import populate_mailing_queue
        total = await populate_mailing_queue(m_id, bot['token'])
        if total == 0:
            return await callback.answer("Botda xabar yuborish uchun hech qanday foydalanuvchi yo'q!", show_alert=True)
            
        await update_mailing(m_id, {'status': 'running', 'total_cnt': total})
        m = await get_mailing(m_id)
        await callback.answer(f"Rassilka boshlandi! ({total} ta odamga)", show_alert=True)
        await callback.message.edit_text(get_mailing_info_text(bot, m), parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
        
    await callback.answer()

@router.callback_query(F.data.startswith("mass_"))
async def mass_routing(callback: CallbackQuery, state: FSMContext):
    from database.db import get_mass_settings, update_mass_settings, get_bot
    from keyboards.inline import mass_mailing_editor_keyboard, cancel_keyboard
    
    parts = callback.data.split("_")
    action = parts[1]
    bot_id = int(parts[2])
    bot = await get_bot(bot_id)
    if not bot: return await callback.answer("Bot topilmadi", show_alert=True)
    
    s = await get_mass_settings(bot['token'])
    token = bot['token']
    
    if action == "main":
        await callback.message.edit_text(get_mass_info_text(bot, s), parse_mode="HTML", reply_markup=mass_mailing_editor_keyboard(bot_id, s))
        
    elif action == "maindone":
        await state.clear()
        await callback.message.edit_text(get_mass_info_text(bot, s), parse_mode="HTML", reply_markup=mass_mailing_editor_keyboard(bot_id, s))
        
    elif action == "togpreview":
        nval = 0 if s.get('disable_preview') else 1
        await update_mass_settings(token, {'disable_preview': nval})
        s['disable_preview'] = nval
        await callback.message.edit_text(get_mass_info_text(bot, s), parse_mode="HTML", reply_markup=mass_mailing_editor_keyboard(bot_id, s))
        
    elif action == "tognotify":
        nval = 0 if s.get('disable_notify') else 1
        await update_mass_settings(token, {'disable_notify': nval})
        s['disable_notify'] = nval
        await callback.message.edit_text(get_mass_info_text(bot, s), parse_mode="HTML", reply_markup=mass_mailing_editor_keyboard(bot_id, s))
        
    elif action == "togprotect":
        nval = 0 if s.get('protect_content') else 1
        await update_mass_settings(token, {'protect_content': nval})
        s['protect_content'] = nval
        await callback.message.edit_text(get_mass_info_text(bot, s), parse_mode="HTML", reply_markup=mass_mailing_editor_keyboard(bot_id, s))
        
    elif action == "togpin":
        nval = 0 if s.get('pin_message') else 1
        await update_mass_settings(token, {'pin_message': nval})
        s['pin_message'] = nval
        await callback.message.edit_text(get_mass_info_text(bot, s), parse_mode="HTML", reply_markup=mass_mailing_editor_keyboard(bot_id, s))
        

    elif action == "speed":
        cur = s.get('speed', 'medium')
        cycle = ['low', 'medium', 'high']
        idx = cycle.index(cur) if cur in cycle else 0
        new_speed = cycle[(idx + 1) % len(cycle)]
        await update_mass_settings(token, {'speed': new_speed})
        s['speed'] = new_speed
        await callback.message.edit_text(get_mass_info_text(bot, s), parse_mode="HTML", reply_markup=mass_mailing_editor_keyboard(bot_id, s))
        
    elif action == "setbtn":
        await callback.message.delete()
        await callback.message.answer(
            "<b>🔗 Ommaviy tugmalar saqlash ombori:</b>\n"
            "Tugmalarni quyidagi shablonda kiritishingiz mumkin:\n"
            "<code>Tugma nomi - https://manzil.com ::blue</code>\n\n"
            "<i>(Nechta kiritsangiz ham bo'ladi. Ular ro'yxati saqlab olinib, postga random qo'shib beriladi).</i>\n\nTozalash uchun <code>skip</code> yozing.",
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
        await state.update_data(bot_id=bot_id)
        await state.set_state(MassMailingSetup.waiting_for_buttons)
        
    elif action == "sendposts":
        await callback.message.delete()
        await callback.message.answer(
            "<b>⬇️ Postlarni Yuboring.</b>\nEndi rejalashtirmoqchi bo'lgan postlaringizni botga "
            "(rasm, video matn qanchasi kerak bolsa) yuboring yoki forward qiling!\n\n"
            "<b>Qanday qilib vaqtini belgilash qonuniydi?</b>\n"
            "O'zingiz tashlab qo'ygan ixtiyoriy POST ga <b>Reply</b> qilib xuddi avvalgidek sana/vaqt yozing:\n"
            "<code>2026-04-20 15:30</code>\n\n"
            "Va u to'liq ushbu ommaviy konfiguratsiya bilan tayyorlanib, navbatga qoshiladi!\n"
            "Chiqish uchun pastdagi bekor qilish tugmasini bosing.",
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
        await state.update_data(bot_id=bot_id)
        await state.set_state(MassMailingSetup.waiting_for_posts)
    

    await callback.answer()


@router.message(MassMailingSetup.waiting_for_buttons)
async def process_mass_mailing_btn(message: Message, state: FSMContext):
    import re, json
    text = message.text or message.caption or ""
    data = await state.get_data()
    bot_id = data.get("bot_id")
    from database.db import update_mass_settings, get_bot
    bot = await get_bot(bot_id)
    
    if text.strip().lower() == 'skip':
        await update_mass_settings(bot['token'], {
            "buttons_json": None
        })
        await message.answer("<b>✅ Ommaviy tugmalar o'chirildi!</b>", parse_mode="HTML")
        # trigger main overview
        from keyboards.inline import mass_mailing_editor_keyboard
        from database.db import get_mass_settings
        s = await get_mass_settings(bot['token'])
        await message.answer(get_mass_info_text(bot, s), parse_mode="HTML", reply_markup=mass_mailing_editor_keyboard(bot_id, s))
        await state.clear()
        return
        
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    parsed_buttons = []
    color_map = {'blue': 'primary', 'red': 'danger', 'green': 'success'}
    raw_text = message.text or message.caption or ""
    
    for line in lines:
        match = re.match(r"^(.*?)\s*-\s*(https?://.*?)(?:\s*::(blue|red|green))?$", line, re.IGNORECASE)
        if not match:
            return await message.answer(f"⚠️ Noto'g'ri format ushbu qatorda:\n<code>{line}</code>\nIltimos shablondagidek kiriting.", parse_mode="HTML")
            
        btn_text = match.group(1).strip()
        url = match.group(2).strip()
        style = color_map.get(match.group(3).lower()) if match.group(3) else None
        
        emoji_id = None
        if message.entities:
            for ent in message.entities:
                if ent.type == 'custom_emoji':
                    line_start = raw_text.find(line)
                    if line_start != -1 and line_start <= ent.offset < line_start + len(line):
                        emoji_id = ent.custom_emoji_id
                        fallback_char = ent.extract_from(raw_text)
                        btn_text = btn_text.replace(fallback_char, "", 1).strip()
                        break

        parsed_buttons.append({
            "text": btn_text,
            "url": url,
            "style": style,
            "emoji_id": emoji_id
        })

    await update_mass_settings(bot['token'], {
        "buttons_json": json.dumps(parsed_buttons)
    })
    
    from keyboards.inline import cancel_keyboard
    await message.answer(f"<b>✅ {len(parsed_buttons)} ta tugma xotirlandi!</b>\n\nUlardan nechtasi <b>bitta post uchun</b> aralashtirilib (random) berilishini raqamda kiriting:\n<i>(Masalan, postlaringiz 1 tadan tugma bilan uzatilishi uchun <code>1</code> deb yozing)</i>", parse_mode="HTML", reply_markup=cancel_keyboard())
    await state.set_state(MassMailingSetup.waiting_for_random_count)

@router.message(MassMailingSetup.waiting_for_random_count)
async def process_mass_mailing_random_count(message: Message, state: FSMContext):
    data = await state.get_data()
    bot_id = data.get("bot_id")
    from database.db import update_mass_settings, get_bot, get_mass_settings
    bot = await get_bot(bot_id)
    
    try:
        cnt = int(message.text.strip())
        if cnt < 1: raise ValueError
    except:
        return await message.answer("⚠️ Iltimos raqam kiriting (masalan: 1 yoki 2)!", parse_mode="HTML")
        
    await update_mass_settings(bot['token'], {
        "random_btn_count": cnt
    })
    
    await message.answer("<b>✅ Tasdiqlandi!</b>", parse_mode="HTML")
    from keyboards.inline import mass_mailing_editor_keyboard
    s = await get_mass_settings(bot['token'])
    await message.answer(get_mass_info_text(bot, s), parse_mode="HTML", reply_markup=mass_mailing_editor_keyboard(bot_id, s))
    await state.clear()


@router.message(MassMailingSetup.waiting_for_posts)
async def process_mass_mailing_posts(message: Message, state: FSMContext):
    data = await state.get_data()
    bot_id = data.get("bot_id")
    from database.db import get_bot, get_mass_settings, create_mailing, update_mailing, populate_mailing_queue
    bot = await get_bot(bot_id)
    
    # Check if it is a reply
    if message.reply_to_message:
        import datetime, time, json, random
        text = message.text.strip()
        try:
            dt = datetime.datetime.strptime(text, '%Y-%m-%d %H:%M')
            tz_uz = datetime.timezone(datetime.timedelta(hours=5))
            dt = dt.replace(tzinfo=tz_uz)
            target = int(dt.timestamp())
        except ValueError:
            return await message.answer("⚠️ Bu matn vaqt formatida emas. Agar post jo'natayotgan bo'lsangiz ruxsat etiladi, agar vaqt belgileotgan bolsangiz formatni to'g'irlang (masalan: <code>2026-04-20 15:30</code>)", parse_mode="HTML")
            
        # Time is valid! Let's extract the replied message content
        orig = message.reply_to_message
        caption = orig.html_text or ""
        file_id, file_type = None, None
        
        if orig.photo:
            file_id = orig.photo[-1].file_id
            file_type = 'photo'
        elif orig.video:
            file_id = orig.video.file_id
            file_type = 'video'
            
        settings = await get_mass_settings(bot['token'])
        
        # Download media if needed (to keep logic identical to standard mailing)
        if file_id:
            file_path = f"media/{file_id}.{'jpg' if file_type=='photo' else 'mp4'}"
            obj = orig.photo[-1] if file_type=='photo' else orig.video
            await message.bot.download(obj, destination=file_path)
            file_id = file_path
            
        # Select random buttons
        mass_btns = []
        if settings.get('buttons_json'):
            mass_btns = json.loads(settings['buttons_json'])
            
        selected_btns = []
        if mass_btns:
            pick_count = min(len(mass_btns), settings.get('random_btn_count', 1))
            selected_btns = random.sample(mass_btns, pick_count)
            
        # Create new logical mailing
        m_id = await create_mailing(bot['token'])
        total = await populate_mailing_queue(m_id, bot['token'])
        
        await update_mailing(m_id, {
            "message": caption,
            "file_id": file_id,
            "file_type": file_type,
            "btn_text": json.dumps(selected_btns) if selected_btns else None,
            "disable_preview": settings.get('disable_preview', 0),
            "disable_notify": settings.get('disable_notify', 0),
            "protect_content": settings.get('protect_content', 0),
            "pin_message": settings.get('pin_message', 0),
            "speed": settings.get('speed', 'medium'),
            "schedule_time": target,
            "status": "scheduled",
            "total_cnt": total
        })
        
        from keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ TAYYOR", callback_data=f"mass_maindone_{bot_id}")
        ]])
        
        await message.answer(f"<b>✅ Ommaviy rejalashtirish amalga oshirildi!</b>\nRassilka #{m_id} tayyor (Kutmoqda). Shu zaylda boshqa yuborilgan postlarga ham reply qilib vaqtini e'lon qilavering.", parse_mode="HTML", reply_markup=kb)
        
    else:
        # User just sending a message to store for later. We can react to let them know it's fine.
        try:
            await message.react([{"type": "emoji", "emoji": "👍"}])
        except:
            pass


@router.message(MailingSetup.waiting_for_message)
async def process_mailing_msg(message: Message, state: FSMContext):
    data = await state.get_data()
    m_id = data.get("mailing_id")
    bot_id = data.get("bot_id")
    file_id, file_type = None, None
    caption = message.html_text or ""
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
        
    if file_id:
        file_path = f"media/{file_id}.{'jpg' if file_type=='photo' else 'mp4'}"
        obj = message.photo[-1] if file_type=='photo' else message.video
        await message.bot.download(obj, destination=file_path)
        file_id = file_path

    from database.db import update_mailing, get_mailing
    await update_mailing(m_id, {
        "message": caption,
        "file_id": file_id,
        "file_type": file_type
    })
    
    from keyboards.inline import mailing_editor_keyboard
    m = await get_mailing(m_id)
    bot = await get_bot(bot_id)
    info = get_mailing_info_text(bot, m)
    await message.answer(info, parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
    await state.clear()


@router.message(MailingSetup.waiting_for_button)
async def process_mailing_btn(message: Message, state: FSMContext):
    import re
    text = message.text or message.caption or ""
    data = await state.get_data()
    m_id = data.get("mailing_id")
    bot_id = data.get("bot_id")
    
    from database.db import update_mailing, get_mailing, get_bot
    if text.strip().lower() == 'skip':
        await update_mailing(m_id, {
            "btn_text": None, "btn_url": None, "btn_style": None, "btn_emoji_id": None
        })
        m = await get_mailing(m_id)
        bot = await get_bot(bot_id)
        info = get_mailing_info_text(bot, m)
        from keyboards.inline import mailing_editor_keyboard
        await message.answer(info, parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
        await state.clear()
        return
        
    import json
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    parsed_buttons = []
    
    color_map = {'blue': 'primary', 'red': 'danger', 'green': 'success'}
    raw_text = message.text or message.caption or ""
    
    for line in lines:
        match = re.match(r"^(.*?)\s*-\s*(https?://.*?)(?:\s*::(blue|red|green))?$", line, re.IGNORECASE)
        if not match:
            return await message.answer(f"⚠️ Noto'g'ri format ushbu qatorda:\n<code>{line}</code>\nIltimos shablondagidek kiriting.", parse_mode="HTML")
            
        btn_text = match.group(1).strip()
        url = match.group(2).strip()
        style = color_map.get(match.group(3).lower()) if match.group(3) else None
        
        emoji_id = None
        if message.entities:
            for ent in message.entities:
                if ent.type == 'custom_emoji':
                    # Check if emoji is within this specific line
                    line_start = raw_text.find(line)
                    if line_start != -1 and line_start <= ent.offset < line_start + len(line):
                        emoji_id = ent.custom_emoji_id
                        fallback_char = ent.extract_from(raw_text)
                        btn_text = btn_text.replace(fallback_char, "", 1).strip()
                        break

        parsed_buttons.append({
            "text": btn_text,
            "url": url,
            "style": style,
            "emoji_id": emoji_id
        })

    # Store JSON string in btn_text, and clear other old fields
    await update_mailing(m_id, {
        "btn_text": json.dumps(parsed_buttons), 
        "btn_url": None, 
        "btn_style": None, 
        "btn_emoji_id": None
    })
    
    from keyboards.inline import mailing_editor_keyboard
    m = await get_mailing(m_id)
    bot = await get_bot(bot_id)
    info = get_mailing_info_text(bot, m)
    await message.answer(info, parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
    await state.clear()


@router.message(MailingSetup.waiting_for_date)
async def process_mailing_date(message: Message, state: FSMContext):
    import datetime, time
    text = message.text.strip()
    try:
        dt = datetime.datetime.strptime(text, '%Y-%m-%d %H:%M')
        # Parse it strictly as UTC+5 (Tashkent Time)
        tz_uz = datetime.timezone(datetime.timedelta(hours=5))
        dt = dt.replace(tzinfo=tz_uz)
        target = int(dt.timestamp())
    except ValueError:
        return await message.answer("⚠️ Noto'g'ri format. Format: <code>2026-04-20 15:30</code>", parse_mode="HTML")
        
    data = await state.get_data()
    m_id = data.get("mailing_id")
    bot_id = data.get("bot_id")
    
    from database.db import update_mailing, get_mailing, populate_mailing_queue, get_bot
    bot = await get_bot(bot_id)
    total = await populate_mailing_queue(m_id, bot['token'])
    
    await update_mailing(m_id, {
        "schedule_time": target,
        "status": "scheduled",
        "total_cnt": total
    })
    
    from keyboards.inline import mailing_editor_keyboard
    m = await get_mailing(m_id)
    info = get_mailing_info_text(bot, m)
    await message.answer(info, parse_mode="HTML", reply_markup=mailing_editor_keyboard(bot_id, m))
    await state.clear()


# ===== BASE MANAGEMENT HANDLERS =====

@router.callback_query(F.data.startswith("base_import_"))
async def start_base_import(callback: CallbackQuery, state: FSMContext):
    bot_id = int(callback.data.split("_")[2])
    await state.update_data(bot_id=bot_id)
    await state.set_state(BaseManagement.waiting_for_json)
    
    await callback.message.edit_text(
        "<tg-emoji emoji-id=\"6039802767931871481\">📥</tg-emoji> <b>Bazani import qilish</b>\n\n"
        "Iltimos, user ID'lari yozilgan <code>.json</code> faylini yuboring.\n"
        "Format: <code>[12345, 67890, ...]</code>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )

@router.callback_query(F.data.startswith("base_export_"))
async def process_base_export(callback: CallbackQuery):
    bot_id = int(callback.data.split("_")[2])
    bot = await get_bot(bot_id)
    if not bot:
        return await callback.answer("Bot topilmadi.")
    
    user_ids = await get_bot_user_ids(bot['token'])
    if not user_ids:
        return await callback.answer("Baza bo'sh.", show_alert=True)
    
    file_content = json.dumps(user_ids).encode('utf-8')
    file_name = f"users_{bot['username']}.json"
    
    input_file = BufferedInputFile(file_content, filename=file_name)
    
    await callback.message.answer_document(
        document=input_file,
        caption=f"<tg-emoji emoji-id=\"5963103826075456248\">📤</tg-emoji> @{bot['username']} botining bazasi ({len(user_ids)} ta user)"
    )
    await callback.answer()

@router.message(BaseManagement.waiting_for_json, F.document)
async def process_json_import(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    bot_id = data.get('bot_id')
    child_bot = await get_bot(bot_id)
    
    if not child_bot:
        await state.clear()
        return await message.answer("Bot topilmadi.")

    if not message.document.file_name.endswith(".json"):
        return await message.answer("⚠️ Faqat JSON fayl qabul qilinadi.", parse_mode="HTML")
    
    status_msg = await message.answer("⏳ Fayl ishlanmoqda...")
    
    try:
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path
        
        # Download file content
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.telegram.org/file/bot{bot.token}/{file_path}") as resp:
                content = await resp.read()
        
        user_ids = json.loads(content)
        
        if not isinstance(user_ids, list):
            return await message.answer("Xato: JSON fayl massiv (list) ko'rinishida bo'lishi kerak.")
        
        # Filter only integers
        user_ids = [int(uid) for uid in user_ids if str(uid).isdigit()]
        
        if not user_ids:
            return await message.answer("Faylda yaroqli user ID'lar topilmadi.")
        
        await import_bot_users(child_bot['token'], user_ids)
        
        await status_msg.edit_text(
            f"<tg-emoji emoji-id=\"5870633910337015697\">✅</tg-emoji> <b>Import muvaffaqiyatli yakunlandi!</b>\n\n"
            f"Jami userlar faylda: {len(user_ids)}\n"
            f"Yangi qo'shilganlar: (Dublikatlar tashlab ketildi)\n\n"
            f"Boshqaruv menyusiga qayting.",
            parse_mode="HTML",
            reply_markup=bot_dashboard_keyboard(bot_id)
        )
        await state.clear()
        
    except Exception as e:
        await status_msg.edit_text(f"<tg-emoji emoji-id=\"5870657884844462243\">❌</tg-emoji> Xatolik yuz berdi: {str(e)}")
        await state.clear()
