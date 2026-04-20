from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Bekor qilish", callback_data="cancel_action", icon_custom_emoji_id="5870657884844462243")]]
    )

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Botlar ro'yxati", callback_data="bot_list", icon_custom_emoji_id="6030400221232501136")
            ]
        ]
    )

def bot_list_keyboard(bots: list) -> InlineKeyboardMarkup:
    kb = []
    for bot in bots:
        bot_name = bot.get('username')
        if not bot_name:
            bot_name = bot['token'][:10] + "..."
        kb.append([InlineKeyboardButton(text=f"@{bot_name}", callback_data=f"bot_menu_{bot['id']}", icon_custom_emoji_id="5870764288364252592")])
        
    kb.append([InlineKeyboardButton(text="Bot yaratish", callback_data="create_bot", icon_custom_emoji_id="5771851822897566479")])
    kb.append([InlineKeyboardButton(text="Ortga", callback_data="main_menu", icon_custom_emoji_id="5893057118545646106")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def bot_dashboard_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Zayavkalarni qayta ishlash", callback_data=f"b_processing_{bot_id}", icon_custom_emoji_id="5870633910337015697")
            ],
            [
                InlineKeyboardButton(text="Xabarlar", callback_data=f"b_msgs_{bot_id}", icon_custom_emoji_id="6039422865189638057"),
                InlineKeyboardButton(text="Yubormalar", callback_data=f"b_mailings_{bot_id}", icon_custom_emoji_id="5963103826075456248")
            ],
            [
                InlineKeyboardButton(text="Ssilkalar", callback_data=f"b_links_{bot_id}", icon_custom_emoji_id="5769289093221454192"),
                InlineKeyboardButton(text="Platformalar", callback_data=f"b_platforms_{bot_id}", icon_custom_emoji_id="6039451237743595514")
            ],
            [
                InlineKeyboardButton(text="Himoya", callback_data=f"b_protection_{bot_id}", icon_custom_emoji_id="6037243349675544634"),
                InlineKeyboardButton(text="Baza boshqaruvi", callback_data=f"b_base_{bot_id}", icon_custom_emoji_id="5870772616305839506")
            ],
            [
                InlineKeyboardButton(text="Botni o'chirish", callback_data=f"b_delete_{bot_id}", icon_custom_emoji_id="5870875489362513438")
            ],
            [
                InlineKeyboardButton(text="Ortga", callback_data="bot_list", icon_custom_emoji_id="5893057118545646106")
            ]
        ]
    )

def request_processing_keyboard(bot_id: int, is_auto_accept: bool, deferred_time: int) -> InlineKeyboardMarkup:
    auto_status = "yoqilgan" if is_auto_accept else "o'chirilgan"
    deferred_status = f"{deferred_time} daq." if deferred_time > 0 else "o'chirilgan"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"Avto-qabul: {auto_status}", callback_data=f"req_auto_{bot_id}", icon_custom_emoji_id="5778672437122045013")
            ],
            [
                InlineKeyboardButton(text="Qabul qilish", callback_data=f"req_accept_{bot_id}", icon_custom_emoji_id="5891207662678317861"),
                InlineKeyboardButton(text="Rad etish", callback_data=f"req_reject_{bot_id}", icon_custom_emoji_id="5893192487324880883")
            ],
            [
                InlineKeyboardButton(text=f"Kechiktirilgan qabul: {deferred_status}", callback_data=f"req_defer_{bot_id}", icon_custom_emoji_id="5983150113483134607")
            ],
            [
                InlineKeyboardButton(text="Ortga", callback_data=f"bot_menu_{bot_id}", icon_custom_emoji_id="5893057118545646106")
            ]
        ]
    )

def req_percentage_keyboard(bot_id: int, action_type: str) -> InlineKeyboardMarkup:
    # action_type can be "accept" or "reject"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="20%", callback_data=f"req_percent_{bot_id}_{action_type}_20"),
                InlineKeyboardButton(text="30%", callback_data=f"req_percent_{bot_id}_{action_type}_30"),
                InlineKeyboardButton(text="40%", callback_data=f"req_percent_{bot_id}_{action_type}_40"),
                InlineKeyboardButton(text="50%", callback_data=f"req_percent_{bot_id}_{action_type}_50")
            ],
            [
                InlineKeyboardButton(text="100%", callback_data=f"req_percent_{bot_id}_{action_type}_100")
            ],
            [
                InlineKeyboardButton(text="O'zingiz belgilang", callback_data=f"req_percent_{bot_id}_{action_type}_custom")
            ],
            [
                InlineKeyboardButton(text="Ortga", callback_data=f"b_processing_{bot_id}", icon_custom_emoji_id="5893057118545646106")
            ]
        ]
    )

def bot_messages_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Kapcha", callback_data=f"msgset_{bot_id}_captcha", icon_custom_emoji_id="6037249452824072506")
            ],
            [
                InlineKeyboardButton(text="Salomlashuv", callback_data=f"msgset_{bot_id}_welcome", icon_custom_emoji_id="5870764288364252592"),
                InlineKeyboardButton(text="Xayrlashuv", callback_data=f"msgset_{bot_id}_goodbye", icon_custom_emoji_id="5870764288364252592")
            ],
            [
                InlineKeyboardButton(text="Ortga", callback_data=f"bot_menu_{bot_id}", icon_custom_emoji_id="5893057118545646106")
            ]
        ]
    )

def bot_platforms_keyboard(bot_id: int, channels: list) -> InlineKeyboardMarkup:
    kb = []
    for c in channels:
        kb.append([InlineKeyboardButton(text=f"{c['chat_title']}", callback_data=f"plat_{bot_id}_{c['chat_id']}")])
    
    kb.append([InlineKeyboardButton(text="➕ Connect (Kanal ulash)", callback_data=f"platadd_{bot_id}")])
    kb.append([InlineKeyboardButton(text="◀️ Ortga", callback_data=f"bot_menu_{bot_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def platform_manage_keyboard(bot_id: int, chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Active", callback_data="dummy_active")],
            [InlineKeyboardButton(text="🗑 Delete (O'chirish)", callback_data=f"platdel_{bot_id}_{chat_id}")],
            [InlineKeyboardButton(text="◀️ Ortga", callback_data=f"b_platforms_{bot_id}")]
        ]
    )

def bot_links_keyboard(bot_id: int, channels: list) -> InlineKeyboardMarkup:
    kb = []
    for c in channels:
        kb.append([InlineKeyboardButton(text=f"🔗 {c['chat_title']}", callback_data=f"linknew_{bot_id}_{c['chat_id']}", icon_custom_emoji_id="5769289093221454192")])
    kb.append([InlineKeyboardButton(text="Ortga", callback_data=f"bot_menu_{bot_id}", icon_custom_emoji_id="5893057118545646106")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def link_type_keyboard(bot_id: int, chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Zayavkali Ssilka", callback_data=f"linktype_{bot_id}_{chat_id}_req")],
            [InlineKeyboardButton(text="Oddiy Ssilka", callback_data=f"linktype_{bot_id}_{chat_id}_norm")],
            [InlineKeyboardButton(text="◀️ Ortga", callback_data=f"b_links_{bot_id}")]
        ]
    )

def get_broadcast_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Matnli xabar 📝", callback_data="bc_text")],
            [InlineKeyboardButton(text="Rasm/Video + Matn 🖼", callback_data="bc_media")],
            [InlineKeyboardButton(text="Ortga 🔙", callback_data="cancel_action")]
        ]
    )

def protection_keyboard(bot_id: int, bot_config: dict) -> InlineKeyboardMarkup:
    def toggle(val): return "🟢" if val else "⚪️"
    
    hier = bot_config.get('filter_hieroglyphs', 0)
    rtl  = bot_config.get('filter_rtl', 0)
    noph = bot_config.get('filter_no_photo', 0)
    # join_limit: not activated for now (shown as disabled)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{toggle(hier)} Ieroglif (漢字) filtri",
                callback_data=f"prot_hieroglyphs_{bot_id}"
            )],
            [InlineKeyboardButton(
                text=f"{toggle(rtl)} RTL belgilari filtri (عربى)",
                callback_data=f"prot_rtl_{bot_id}"
            )],
            [InlineKeyboardButton(
                text=f"{toggle(noph)} Rasmsiz akkauntlar filtri",
                callback_data=f"prot_nophoto_{bot_id}"
            )],
            [InlineKeyboardButton(
                text="⛔ Limit",
                callback_data=f"prot_limit_{bot_id}",
                icon_custom_emoji_id="6037243349675544634"
            )],
            [InlineKeyboardButton(text="Ortga", callback_data=f"bot_menu_{bot_id}", icon_custom_emoji_id="5893057118545646106")]
        ]
    )

def limit_keyboard(bot_id: int, bot_config: dict) -> InlineKeyboardMarkup:
    check = bot_config.get('limit_check', 0)
    punishment = bot_config.get('limit_punishment', 'kick')
    ltime = bot_config.get('limit_time', 1)
    jlimit = bot_config.get('join_limit', 50)
    
    check_icon = "🔍 Check: yoqilgan ✅" if check else "🔍 Check: o'chirilgan ⚪️"
    pun_label = "🕵️ Jazo: Kick" if punishment == 'kick' else "🕵️ Jazo: Ban"
    
    time_options = [1, 5, 15, 30, 60, 180]
    time_label_map = {1: "1 daq", 5: "5 daq", 15: "15 daq", 30: "30 daq", 60: "1 soat", 180: "3 soat"}
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=check_icon, callback_data=f"lim_check_{bot_id}")],
            [InlineKeyboardButton(text=pun_label, callback_data=f"lim_pun_{bot_id}")],
            [InlineKeyboardButton(text=f"🕐 Vaqt: {time_label_map.get(ltime, str(ltime)+' daq')}", callback_data=f"lim_time_{bot_id}")],
            [InlineKeyboardButton(text=f"⛔ Limit: > {jlimit}", callback_data=f"lim_count_{bot_id}")],
            [InlineKeyboardButton(text="◀️ Ortga", callback_data=f"b_protection_{bot_id}")]
        ]
    )


# ===== MAILING SYSTEM KEYBOARDS =====

def mailing_main_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Create mailing", callback_data=f"mail_create_{bot_id}", icon_custom_emoji_id="5771851822897566479")],
            [InlineKeyboardButton(text="Scheduled", callback_data=f"mail_list_{bot_id}", icon_custom_emoji_id="5890937706803894250")],
            [InlineKeyboardButton(text="Massoviy Rassilka", callback_data=f"mass_main_{bot_id}", icon_custom_emoji_id="5884479287171485878")],
            [InlineKeyboardButton(text="Back", callback_data=f"bot_menu_{bot_id}", icon_custom_emoji_id="5893057118545646106")]
        ]
    )

def mailing_list_keyboard(bot_id: int, mailings: list) -> InlineKeyboardMarkup:
    kb = []
    for m in mailings:
        status_emoji = {
            'draft': '📝', 'scheduled': '⏳', 'running': '🟢', 
            'paused': '⏸', 'completed': '✅'
        }.get(m['status'], '❓')
        name = f"{status_emoji} Mailing #{m['id']} " + (f"({m['sent_cnt']}/{m['total_cnt']})" if m['total_cnt'] else "")
        kb.append([InlineKeyboardButton(text=name, callback_data=f"mail_edit_{bot_id}_{m['id']}")])
    kb.append([InlineKeyboardButton(text="◀️ Back", callback_data=f"mail_main_{bot_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def mailing_editor_keyboard(bot_id: int, mailing: dict) -> InlineKeyboardMarkup:
    kb = []
    mid = mailing['id']
    st = mailing['status']
    
    if st in ['draft', 'scheduled']:
        kb.append([
            InlineKeyboardButton(text="Edit Msg/Media", callback_data=f"mail_setmsg_{bot_id}_{mid}", icon_custom_emoji_id="5870676941614354370")
        ])
        kb.append([
            InlineKeyboardButton(text="URL-buttons", callback_data=f"mail_setbtn_{bot_id}_{mid}", icon_custom_emoji_id="5769289093221454192")
        ])
        
        preview_lbl = "Preview: none" if mailing.get('disable_preview') else "Preview: yes"
        notify_lbl = "Notify: no" if mailing.get('disable_notify') else "Notify: yes"
        kb.append([
            InlineKeyboardButton(text=preview_lbl, callback_data=f"mail_togpreview_{bot_id}_{mid}", icon_custom_emoji_id="6037397706505195857"),
            InlineKeyboardButton(text=notify_lbl, callback_data=f"mail_tognotify_{bot_id}_{mid}", icon_custom_emoji_id="6039486778597970865")
        ])
        
        protect_lbl = "Protect: yes" if mailing.get('protect_content') else "Protect: no"
        pin_lbl = "Pin: yes" if mailing.get('pin_message') else "Pin: no"
        kb.append([
            InlineKeyboardButton(text=protect_lbl, callback_data=f"mail_togprotect_{bot_id}_{mid}", icon_custom_emoji_id="6037243349675544634"),
            InlineKeyboardButton(text=pin_lbl, callback_data=f"mail_togpin_{bot_id}_{mid}", icon_custom_emoji_id="5870801517140775623")
        ])
        
        sp_map = {'low': 'Low', 'medium': 'Medium', 'high': 'High'}
        speed_lbl = f"Speed: {sp_map.get(mailing['speed'], 'Medium')}"
        kb.append([
            InlineKeyboardButton(text=speed_lbl, callback_data=f"mail_speed_{bot_id}_{mid}", icon_custom_emoji_id="5870930636742595124")
        ])

        if st == 'scheduled':
            kb.append([
                InlineKeyboardButton(text="Schedule", callback_data=f"mail_sched_{bot_id}_{mid}", icon_custom_emoji_id="5983150113483134607"),
                InlineKeyboardButton(text="Save", callback_data=f"mail_list_{bot_id}", icon_custom_emoji_id="5870528606328852614")
            ])
        else:
            kb.append([
                InlineKeyboardButton(text="Schedule", callback_data=f"mail_sched_{bot_id}_{mid}", icon_custom_emoji_id="5983150113483134607"),
                InlineKeyboardButton(text="Start", callback_data=f"mail_start_{bot_id}_{mid}", icon_custom_emoji_id="5963103826075456248")
            ])
    if st == 'running':
        kb.append([InlineKeyboardButton(text="⏸ Pause", callback_data=f"mail_pause_{bot_id}_{mid}")])
    elif st == 'paused':
        kb.append([InlineKeyboardButton(text="▶ Resume", callback_data=f"mail_resume_{bot_id}_{mid}")])
        
    if st not in ['completed']:
        kb.append([InlineKeyboardButton(text="Cancel / Delete", callback_data=f"mail_del_{bot_id}_{mid}", icon_custom_emoji_id="5870875489362513438")])
    
    kb.append([InlineKeyboardButton(text="Back", callback_data=f"mail_list_{bot_id}", icon_custom_emoji_id="5893057118545646106")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def mass_mailing_editor_keyboard(bot_id: int, settings: dict) -> InlineKeyboardMarkup:
    kb = []
    
    kb.append([
        InlineKeyboardButton(text="↗ Ommaviy Tugmalar", callback_data=f"mass_setbtn_{bot_id}")
    ])
    
    preview_lbl = "Preview: none" if settings.get('disable_preview') else "Preview: yes"
    notify_lbl = "Notify: no" if settings.get('disable_notify') else "Notify: yes"
    kb.append([
        InlineKeyboardButton(text=preview_lbl, callback_data=f"mass_togpreview_{bot_id}", icon_custom_emoji_id="6037397706505195857"),
        InlineKeyboardButton(text=notify_lbl, callback_data=f"mass_tognotify_{bot_id}", icon_custom_emoji_id="6039486778597970865")
    ])
    
    protect_lbl = "Protect: yes" if settings.get('protect_content') else "Protect: no"
    pin_lbl = "Pin: yes" if settings.get('pin_message') else "Pin: no"
    kb.append([
        InlineKeyboardButton(text=protect_lbl, callback_data=f"mass_togprotect_{bot_id}", icon_custom_emoji_id="6037243349675544634"),
        InlineKeyboardButton(text=pin_lbl, callback_data=f"mass_togpin_{bot_id}", icon_custom_emoji_id="5870801517140775623")
    ])
    
    sp_map = {'low': 'Low', 'medium': 'Medium', 'high': 'High'}
    speed_lbl = f"Speed: {sp_map.get(settings.get('speed', 'medium'), 'Medium')}"
    kb.append([
        InlineKeyboardButton(text=speed_lbl, callback_data=f"mass_speed_{bot_id}", icon_custom_emoji_id="5870930636742595124")
    ])

    kb.append([
        InlineKeyboardButton(text="✅ Sozlamalarni saqlash va Post yuborish", callback_data=f"mass_sendposts_{bot_id}")
    ])
    kb.append([InlineKeyboardButton(text="◀️ Back", callback_data=f"mail_main_{bot_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
def bot_base_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Bazani import qilish (JSON)", callback_data=f"base_import_{bot_id}", icon_custom_emoji_id="6039802767931871481")
            ],
            [
                InlineKeyboardButton(text="Bazani yuklab olish (JSON)", callback_data=f"base_export_{bot_id}", icon_custom_emoji_id="5963103826075456248")
            ],
            [
                InlineKeyboardButton(text="Ortga", callback_data=f"bot_menu_{bot_id}", icon_custom_emoji_id="5893057118545646106")
            ]
        ]
    )
