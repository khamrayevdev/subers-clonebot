
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import ChatJoinRequest, Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile, LinkPreviewOptions
from typing import Dict, Any
from database.db import get_bot_by_token, add_pending_request, remove_pending_request, pop_due_requests, increment_stat, add_bot_user, is_channel_allowed, update_bot_field, record_join_event, count_join_events
import time

async def send_welcome_message(bot: Bot, bot_config: dict, user_id: int):
    # bot_config has: welcome_message, welcome_file_id, welcome_file_type, welcome_btn_text, welcome_btn_url
    if not bot_config['welcome_active']:
        return

    text = bot_config['welcome_message'] or ""
        
    kb = None
    if bot_config['welcome_btn_text'] and bot_config['welcome_btn_url']:
        btn_kwargs = {'text': bot_config['welcome_btn_text'], 'url': bot_config['welcome_btn_url']}
        if bot_config.get('welcome_btn_style'):
            btn_kwargs['style'] = bot_config['welcome_btn_style']
        if bot_config.get('welcome_btn_emoji_id'):
            btn_kwargs['icon_custom_emoji_id'] = bot_config['welcome_btn_emoji_id']
            
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(**btn_kwargs)
        ]])
    
    # Flag: if style/emoji causes API error, we'll retry without them
    _styled_kb = kb

    try:
        photo_or_video = bot_config['welcome_file_id']
        final_file = None
        is_local = False
        
        if photo_or_video:
            if photo_or_video.startswith('child:'):
                final_file = photo_or_video.replace('child:', '')
            elif '/' in photo_or_video:
                final_file = FSInputFile(photo_or_video)
                is_local = True
            elif not photo_or_video.startswith('http'):
                final_file = "legacy"
        if bot_config['welcome_file_type'] == 'photo' and final_file and final_file != "legacy":
            msg = await bot.send_photo(user_id, photo=final_file, caption=text, reply_markup=kb, parse_mode="HTML")
            if is_local:
                await update_bot_field(bot_config['id'], 'welcome_file_id', f"child:{msg.photo[-1].file_id}")
        elif bot_config['welcome_file_type'] == 'video' and final_file and final_file != "legacy":
            msg = await bot.send_video(user_id, video=final_file, caption=text, reply_markup=kb, parse_mode="HTML")
            if is_local:
                await update_bot_field(bot_config['id'], 'welcome_file_id', f"child:{msg.video.file_id}")
        elif bot_config['welcome_file_type'] in ['photo', 'video'] and final_file == "legacy":
            await bot.send_message(user_id, text=text + "\n\n<i>[Eski Media! Bot egasi uni yangilashi kerak]</i>", reply_markup=kb, parse_mode="HTML")
        else:
            await bot.send_message(user_id, text=text, reply_markup=kb, parse_mode="HTML")
            
        await increment_stat(bot_config['token'], 'welcomes_sent')
    except Exception as e:
        print("Welcome Send Error", e)

async def send_goodbye_message(bot: Bot, bot_config: dict, user_id: int):
    if not bot_config.get('goodbye_message'):
        return
    try:
        text = bot_config['goodbye_message']
        kb = None
        if bot_config.get('goodbye_btn_text') and bot_config.get('goodbye_btn_url'):
            btn_kwargs = {'text': bot_config['goodbye_btn_text'], 'url': bot_config['goodbye_btn_url']}
            if bot_config.get('goodbye_btn_style'):
                btn_kwargs['style'] = bot_config['goodbye_btn_style']
            if bot_config.get('goodbye_btn_emoji_id'):
                btn_kwargs['icon_custom_emoji_id'] = bot_config['goodbye_btn_emoji_id']
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(**btn_kwargs)]])
        
        gfile = bot_config.get('goodbye_file_id')
        final_file = None
        is_local = False
        if gfile:
            if gfile.startswith('child_gb:'):
                final_file = gfile.replace('child_gb:', '')
            elif '/' in gfile:
                final_file = FSInputFile(gfile)
                is_local = True
        
        if bot_config.get('goodbye_file_type') == 'photo' and final_file:
            msg = await bot.send_photo(user_id, photo=final_file, caption=text, reply_markup=kb, parse_mode="HTML")
            if is_local:
                await update_bot_field(bot_config['id'], 'goodbye_file_id', f"child_gb:{msg.photo[-1].file_id}")
        elif bot_config.get('goodbye_file_type') == 'video' and final_file:
            msg = await bot.send_video(user_id, video=final_file, caption=text, reply_markup=kb, parse_mode="HTML")
            if is_local:
                await update_bot_field(bot_config['id'], 'goodbye_file_id', f"child_gb:{msg.video.file_id}")
        else:
            await bot.send_message(user_id, text=text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        print("Goodbye Send Error", e)


class ChildBotManager:
    def __init__(self):
        self.bots: Dict[str, Bot] = {}
        self.polling_tasks: Dict[str, asyncio.Task] = {}
        self.dispatcher = Dispatcher()
        self.setup_handlers()
        self.background_task = None

    def get_bot(self, token: str) -> Bot:
        return self.bots.get(token)

    async def start_manager(self):
        self.background_task = asyncio.create_task(self.pending_worker())
        self.mailing_task = asyncio.create_task(self.mailing_worker())

    async def pending_worker(self):
        while True:
            try:
                due_requests = await pop_due_requests()
                if due_requests:
                    for req_id, token, chat_id, user_id in due_requests:
                        bot = self.get_bot(token)
                        if bot:
                            bot_config = await get_bot_by_token(token)
                            if bot_config:
                                try:
                                    await bot.approve_chat_join_request(chat_id, user_id)
                                    await increment_stat(token, 'users_accepted')
                                    await add_bot_user(token, user_id)
                                    await send_welcome_message(bot, bot_config, user_id)
                                except Exception as e:
                                    pass
            except Exception as e:
                print("Pending worker error", e)
            await asyncio.sleep(10)

    async def mailing_worker(self):
        from database.db import get_pending_mailings, get_active_mailings, update_mailing, get_mailing_queue_batch, mark_queue_sent, increment_mailing_sent, populate_mailing_queue
        while True:
            try:
                # 1. Activate scheduled mailings whose time has come
                pending = await get_pending_mailings()
                for p in pending:
                    # Populate queue if empty
                    await populate_mailing_queue(p['id'], p['bot_token'])
                    await update_mailing(p['id'], {'status': 'running'})
                
                # 2. Process active mailings
                active = await get_active_mailings()
                for m in active:
                    bot = self.get_bot(m['bot_token'])
                    if not bot: continue
                    
                    # Determine batch size / sleep per speed
                    # low = 1 msg/sec, medium = 5 msg/sec, high = 15 msg/sec
                    b_size = {'low': 1, 'medium': 5, 'high': 15}.get(m['speed'], 5)
                    slp = 1.0 # process batch every second ideally
                    
                    queue = await get_mailing_queue_batch(m['id'], limit=b_size)
                    if not queue:
                        # Finished!
                        await update_mailing(m['id'], {'status': 'completed'})
                        from database.db import cleanup_media_file
                        if m.get('file_id'):
                            await cleanup_media_file(m['file_id'])
                        continue
                        
                    # Prepare keyboard and media
                    kb = None
                    if m.get('btn_text'):
                        btn_txt = m['btn_text']
                        if btn_txt.startswith('['):
                            import json
                            try:
                                btn_list = json.loads(btn_txt)
                                inline_kb = []
                                for btn in btn_list:
                                    t = btn['text']
                                    u = btn['url']
                                    kw = {'text': t, 'url': u}
                                    if btn.get('style'): kw['style'] = btn['style']
                                    else:
                                        # Parse ::color if style not present
                                        lower_t = t.lower()
                                        if '::red' in lower_t: kw['style'] = 'danger'; kw['text'] = t.replace('::red', '').strip()
                                        elif '::blue' in lower_t: kw['style'] = 'primary'; kw['text'] = t.replace('::blue', '').strip()
                                        elif '::green' in lower_t: kw['style'] = 'success'; kw['text'] = t.replace('::green', '').strip()
                                    
                                    if btn.get('emoji_id'): kw['icon_custom_emoji_id'] = btn['emoji_id']
                                    inline_kb.append([InlineKeyboardButton(**kw)])
                                kb = InlineKeyboardMarkup(inline_keyboard=inline_kb)
                            except Exception:
                                pass
                        elif m.get('btn_url'):
                            btn_kwargs = {'text': btn_txt, 'url': m['btn_url']}
                            if m.get('btn_style'): btn_kwargs['style'] = m['btn_style']
                            if m.get('btn_emoji_id'): btn_kwargs['icon_custom_emoji_id'] = m['btn_emoji_id']
                            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(**btn_kwargs)]])
                        
                    text = m['message'] or ""
                    gfile = m.get('file_id')
                    final_file = gfile
                    
                    if gfile and gfile.startswith('child'):
                        # Actually we saved regular file_id inside process_mailing_msg, because media gets downloaded.
                        # So it will be 'media/XXX.jpg' or simple remote link if unchanged
                        pass
                    if gfile and '/' in gfile:
                        final_file = FSInputFile(gfile)

                    # Advanced options
                    preview_opt = LinkPreviewOptions(is_disabled=bool(m.get('disable_preview')))
                    notify_opt = bool(m.get('disable_notify'))
                    protect_opt = bool(m.get('protect_content'))
                    pin_msg = bool(m.get('pin_message'))
                    del_hours = m.get('auto_delete_hours', 0)

                    # Send to batch
                    for q in queue:
                        try:
                            msg_obj = None
                            if m.get('file_type') == 'photo' and final_file:
                                msg_obj = await bot.send_photo(
                                    q['user_id'], photo=final_file, caption=text, reply_markup=kb, 
                                    parse_mode="HTML", disable_notification=notify_opt, protect_content=protect_opt
                                )
                            elif m.get('file_type') == 'video' and final_file:
                                msg_obj = await bot.send_video(
                                    q['user_id'], video=final_file, caption=text, reply_markup=kb, 
                                    parse_mode="HTML", disable_notification=notify_opt, protect_content=protect_opt
                                )
                            else:
                                msg_obj = await bot.send_message(
                                    q['user_id'], text=text, reply_markup=kb, 
                                    parse_mode="HTML", link_preview_options=preview_opt, 
                                    disable_notification=notify_opt, protect_content=protect_opt
                                )
                                
                            # Post-send actions
                            if msg_obj:
                                if pin_msg:
                                    try:
                                        await bot.pin_chat_message(q['user_id'], msg_obj.message_id)
                                    except Exception:
                                        pass

                            # Mark sent
                            await mark_queue_sent(q['id'])
                            await increment_mailing_sent(m['id'])

                        except Exception as e:
                            from database.db import mark_queue_failed, increment_mailing_blocked
                            await mark_queue_failed(q['id'])
                            await increment_mailing_blocked(m['id'])
                    # Sleep slightly per batch to spread load
                    await asyncio.sleep(slp)

            except Exception as e:
                print("Mailing worker error", e)
            await asyncio.sleep(2)
            

    def setup_handlers(self):
        router = Router()

        @router.chat_join_request()
        async def process_chat_join_request(update: ChatJoinRequest, bot: Bot):
            bot_config = await get_bot_by_token(bot.token)
            if not bot_config:
                return
                
            # Channel restriction check
            if not await is_channel_allowed(bot.token, update.chat.id):
                return
                
            auto_accept = bot_config.get('auto_accept', 1)
            deferred_time = bot_config.get('deferred_time', 0)
            delay = deferred_time if auto_accept else 99999999
            
            # ===== PROTECTION FILTERS =====
            user = update.from_user
            name = (user.first_name or "") + " " + (user.last_name or "")
            
            def has_hieroglyphs(text):
                import unicodedata
                for ch in text:
                    block = unicodedata.name(ch, "").lower()
                    if any(x in block for x in ["cjk", "hiragana", "katakana", "hangul", "bopomofo", "kangxi"]):
                        return True
                return False
            
            def has_rtl(text):
                import unicodedata
                rtl_chars = set("اأإآبتثجحخدذرزسشصضطظعغفقكلمنهوؤيئىةء" + "אבגדהוזחטיכלמנסעפצקרשת")
                return any(ch in rtl_chars for ch in text)
            
            rejected = False
            if bot_config.get('filter_hieroglyphs') and has_hieroglyphs(name):
                rejected = True
            if bot_config.get('filter_rtl') and has_rtl(name):
                rejected = True
            if bot_config.get('filter_no_photo'):
                # Check via get_user_profile_photos (premium status is irrelevant)
                try:
                    photos = await bot.get_user_profile_photos(user.id, limit=1)
                    if photos.total_count == 0:
                        rejected = True
                except Exception:
                    pass
            
            if rejected:
                try:
                    await bot.decline_chat_join_request(update.chat.id, user.id)
                except Exception:
                    pass
                return
            # ===== END FILTERS =====
            
            # ===== LIMIT CHECK =====
            if bot_config.get('limit_check'):
                jlimit = bot_config.get('join_limit', 50)
                ltime = bot_config.get('limit_time', 1)
                recent = await count_join_events(bot.token, update.chat.id, ltime)
                if recent >= jlimit:
                    # Limit exceeded — decline this request
                    try:
                        punishment = bot_config.get('limit_punishment', 'kick')
                        await bot.decline_chat_join_request(update.chat.id, user.id)
                        if punishment == 'ban':
                            await bot.ban_chat_member(update.chat.id, user.id)
                    except Exception:
                        pass
                    return
                # Record this join event
                await record_join_event(bot.token, update.chat.id)
            # ===== END LIMIT =====
            
            await add_pending_request(bot.token, update.chat.id, update.from_user.id, delay)

            # Send Captcha Message (Media + ReplyKeyboardMarkup)
            c_text = bot_config['captcha_text'] or ""
            c_btn = bot_config['captcha_btn_text'] or "✅ Men robot emasman"
            
            kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=c_btn)]], resize_keyboard=True)

            try:
                media = bot_config['captcha_file_id']
                final_file = None
                is_local = False
                
                if media:
                    if media.startswith('child:'):
                        final_file = media.replace('child:', '')
                    elif '/' in media:
                        from aiogram.types import FSInputFile
                        final_file = FSInputFile(media)
                        is_local = True
                    elif not media.startswith('http'):
                        final_file = "legacy"

                if bot_config['captcha_file_type'] == 'photo' and final_file != "legacy":
                    msg = await bot.send_photo(update.from_user.id, photo=final_file, caption=c_text, reply_markup=kb, parse_mode="HTML")
                    if is_local:
                        from database.db import update_bot_field
                        await update_bot_field(bot_config['id'], 'captcha_file_id', f"child:{msg.photo[-1].file_id}")
                elif bot_config['captcha_file_type'] == 'video' and final_file != "legacy":
                    msg = await bot.send_video(update.from_user.id, video=final_file, caption=c_text, reply_markup=kb, parse_mode="HTML")
                    if is_local:
                        from database.db import update_bot_field
                        await update_bot_field(bot_config['id'], 'captcha_file_id', f"child:{msg.video.file_id}")
                elif bot_config['captcha_file_type'] in ['photo', 'video'] and final_file == "legacy":
                    await bot.send_message(update.from_user.id, text=c_text + "\n\n<i>[Eski Media! Bot egasi uni yangilashi kerak]</i>", reply_markup=kb, parse_mode="HTML")
                else:
                    await bot.send_message(update.from_user.id, text=c_text, reply_markup=kb, parse_mode="HTML")
            except Exception as e:
                print("Captcha Send Error:", e)


        @router.chat_member()
        async def on_user_leave(update: ChatMemberUpdated, bot: Bot):
            if not await is_channel_allowed(bot.token, update.chat.id):
                return
                
            if update.old_chat_member.status in ["member", "administrator", "creator"] \
               and update.new_chat_member.status in ["left", "kicked"]:
                bot_config = await get_bot_by_token(bot.token)
                if bot_config:
                    await send_goodbye_message(bot, bot_config, update.from_user.id)

        @router.message()
        async def handle_messages(msg: Message, bot: Bot):
            bot_config = await get_bot_by_token(bot.token)
            if not bot_config:
                return

            # Check if this text matches Captcha Button
            if msg.text and bot_config['captcha_btn_text'] and msg.text == bot_config['captcha_btn_text']:
                # The user passed captcha early!
                # Note: We need chat_id to approve, but typical private messages don't have channel chat_id.
                # Since we lack chat_id here, wait... aiogram allows fetching it if we stored it?
                # Actually, our pending_requests has the chat_id. Let's fetch it.
                # However, SQLite lookup by user_id and token
                from database.db import DB_NAME
                import aiosqlite
                async with aiosqlite.connect(DB_NAME) as db:
                    async with db.execute('SELECT chat_id FROM pending_requests WHERE bot_token = ? AND user_id = ?', (bot.token, msg.from_user.id)) as cursor:
                        row = await cursor.fetchone()
                
                if row:
                    chat_id = row[0]
                    # Tasdiqlaymiz va pendingdan olib tashlaymiz
                    await remove_pending_request(bot.token, chat_id, msg.from_user.id)
                    try:
                        await bot.approve_chat_join_request(chat_id, msg.from_user.id)
                        await increment_stat(bot.token, 'users_accepted')
                        await increment_stat(bot.token, 'captcha_passed')
                        await add_bot_user(bot.token, msg.from_user.id)
                        
                        # Remove ReplyKeyboard silently
                        rm_msg = await msg.answer("⏳", reply_markup=ReplyKeyboardRemove())
                        await rm_msg.delete()
                        
                        # Send Welcome Message
                        await send_welcome_message(bot, bot_config, msg.from_user.id)
                    except Exception as e:
                        pass
            
            # Other messages (Autoresponders) can be handled here later

        self.dispatcher.include_router(router)

    async def start_bot(self, token: str):
        if token in self.bots:
            return 
        bot = Bot(token=token)
        self.bots[token] = bot
        task = asyncio.create_task(self.dispatcher.start_polling(bot))
        self.polling_tasks[token] = task

    async def stop_bot(self, token: str):
        if token in self.polling_tasks:
            self.polling_tasks[token].cancel()
            del self.polling_tasks[token]
            bot = self.bots.pop(token, None)
            if bot:
                await bot.session.close()

    async def stop_all(self):
        """Cleanly shuts down everything managed by the bot manager"""
        # 1. Stop background workers
        if hasattr(self, 'background_task') and self.background_task:
            self.background_task.cancel()
        if hasattr(self, 'mailing_task') and self.mailing_task:
            self.mailing_task.cancel()
            
        # 2. Stop all child bots
        tokens = list(self.polling_tasks.keys())
        for token in tokens:
            await self.stop_bot(token)
            
        # 3. Final wait for cancellations
        tasks = []
        if hasattr(self, 'background_task') and self.background_task: tasks.append(self.background_task)
        if hasattr(self, 'mailing_task') and self.mailing_task: tasks.append(self.mailing_task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        print("Bot Manager: All background tasks and child bots stopped.")

bot_manager = ChildBotManager()
