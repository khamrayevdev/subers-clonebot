import aiosqlite
import time
from typing import Union

DB_NAME = "database.sqlite"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
        ''')
        # bots table expansion
        await db.execute('''
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            token TEXT UNIQUE,
            username TEXT,
            welcome_message TEXT,
            welcome_file_id TEXT,
            welcome_file_type TEXT,
            welcome_btn_text TEXT,
            welcome_btn_url TEXT,
            welcome_btn_style TEXT,
            welcome_btn_emoji_id TEXT,
            
            captcha_text TEXT,
            captcha_file_id TEXT,
            captcha_file_type TEXT,
            captcha_btn_text TEXT,
            
            goodbye_message TEXT,
            goodbye_file_id TEXT,
            goodbye_file_type TEXT,
            goodbye_btn_text TEXT,
            goodbye_btn_url TEXT,
            goodbye_btn_style TEXT,
            goodbye_btn_emoji_id TEXT,
            is_active BOOLEAN DEFAULT 1,
            welcome_active BOOLEAN DEFAULT 1,
            auto_accept BOOLEAN DEFAULT 1,
            deferred_time INTEGER DEFAULT 0,
            filter_hieroglyphs BOOLEAN DEFAULT 0,
            filter_rtl BOOLEAN DEFAULT 0,
            filter_no_photo BOOLEAN DEFAULT 0,
            join_limit INTEGER DEFAULT 50,
            limit_check BOOLEAN DEFAULT 0,
            limit_punishment TEXT DEFAULT 'kick',
            limit_time INTEGER DEFAULT 1
        )
        ''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS join_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_token TEXT,
            chat_id INTEGER,
            joined_at INTEGER
        )
        ''')
        # pending_requests for delayed acceptance
        await db.execute('''
        CREATE TABLE IF NOT EXISTS pending_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_token TEXT,
            chat_id INTEGER,
            user_id INTEGER,
            join_time INTEGER,
            target_time INTEGER
        )
        ''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS bot_users (
            bot_token TEXT,
            user_id INTEGER,
            joined_at INTEGER,
            PRIMARY KEY (bot_token, user_id)
        )
        ''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS bot_stats (
            bot_token TEXT PRIMARY KEY,
            users_accepted INTEGER DEFAULT 0,
            captcha_passed INTEGER DEFAULT 0,
            welcomes_sent INTEGER DEFAULT 0
        )
        ''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_token TEXT,
            chat_id INTEGER,
            chat_title TEXT
        )
        ''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS mailings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_token TEXT,
            message TEXT,
            file_id TEXT,
            file_type TEXT,
            btn_text TEXT,
            btn_url TEXT,
            btn_style TEXT,
            btn_emoji_id TEXT,
            speed TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'draft',
            schedule_time INTEGER DEFAULT 0,
            created_at INTEGER,
            total_cnt INTEGER DEFAULT 0,
            sent_cnt INTEGER DEFAULT 0,
            disable_preview BOOLEAN DEFAULT 0,
            disable_notify BOOLEAN DEFAULT 0,
            protect_content BOOLEAN DEFAULT 0,
            pin_message BOOLEAN DEFAULT 0,
            auto_delete_hours INTEGER DEFAULT 0,
            blocked_cnt INTEGER DEFAULT 0
        )
        ''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS mailing_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mailing_id INTEGER,
            bot_token TEXT,
            user_id INTEGER,
            status TEXT DEFAULT 'pending'
        )
        ''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS mass_mailing_settings (
            bot_token TEXT PRIMARY KEY,
            disable_preview BOOLEAN DEFAULT 0,
            disable_notify BOOLEAN DEFAULT 0,
            protect_content BOOLEAN DEFAULT 0,
            pin_message BOOLEAN DEFAULT 0,
            auto_delete_hours INTEGER DEFAULT 0,
            speed TEXT DEFAULT 'medium',
            buttons_json TEXT,
            random_btn_count INTEGER DEFAULT 1
        )
        ''')
        await db.commit()


async def add_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        await db.commit()

async def add_bot(owner_id: int, token: str, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        default_welcome = "<b>Assalomu alaykum! Zayavka qabul qilindi.</b>"
        default_url = "https://t.me"
        default_btn = "Kanalga o'tish"
        
        default_captcha = "<b>Salom!</b> Botimizga qo'shilish uchun o'zingizni tasdiqlang."
        default_cbtn = "✅ Men robot emasman"

        await db.execute('''
            INSERT INTO bots (owner_id, token, welcome_message, welcome_btn_text, welcome_btn_url, captcha_text, captcha_btn_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (owner_id, token, default_welcome, default_btn, default_url, default_captcha, default_cbtn))
        await db.execute('INSERT OR IGNORE INTO bot_stats (bot_token) VALUES (?)', (token,))
        await db.commit()

async def get_bot(bot_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM bots WHERE id = ?', (bot_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_bot_by_token(token: str):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM bots WHERE token = ?', (token,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_bots_by_owner(owner_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM bots WHERE owner_id = ?', (owner_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_all_active_bots():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM bots WHERE is_active = 1') as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def count_bots():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT count(id) FROM bots') as cursor:
            res = await cursor.fetchone()
            return res[0] if res else 0

async def count_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT count(user_id) FROM users') as cursor:
            res = await cursor.fetchone()
            return res[0] if res else 0

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id FROM users') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def update_bot_field(bot_id: int, field: str, value: Union[str, int, None]):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f'UPDATE bots SET {field} = ? WHERE id = ?', (value, bot_id))
        await db.commit()

async def update_bot_fields(bot_id: int, updates: dict):
    if not updates: return
    fields = ', '.join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values())
    values.append(bot_id)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f'UPDATE bots SET {fields} WHERE id = ?', values)
        await db.commit()

# Stats
async def increment_stat(token: str, field: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f'UPDATE bot_stats SET {field} = {field} + 1 WHERE bot_token = ?', (token,))
        await db.commit()

async def get_bot_stats(token: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT users_accepted, captcha_passed, welcomes_sent FROM bot_stats WHERE bot_token = ?', (token,)) as cursor:
            row = await cursor.fetchone()
            return dict(zip(['users_accepted', 'captcha_passed', 'welcomes_sent'], row)) if row else None

# Pending Requests
async def add_pending_request(token: str, chat_id: int, user_id: int, delay_minutes: int):
    now = int(time.time())
    target = now + (delay_minutes * 60)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT INTO pending_requests (bot_token, chat_id, user_id, join_time, target_time) VALUES (?, ?, ?, ?, ?)', (token, chat_id, user_id, now, target))
        await db.commit()

async def remove_pending_request(token: str, chat_id: int, user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM pending_requests WHERE bot_token = ? AND chat_id = ? AND user_id = ?', (token, chat_id, user_id))
        await db.commit()

async def get_pending_requests_count(token: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT count(id) FROM pending_requests WHERE bot_token = ?', (token,)) as cursor:
            res = await cursor.fetchone()
            return res[0] if res else 0

async def get_pending_requests(token: str, limit: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT id, chat_id, user_id FROM pending_requests WHERE bot_token = ? LIMIT ?', (token, limit)) as cursor:
            return await cursor.fetchall()

async def pop_due_requests():
    now = int(time.time())
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT id, bot_token, chat_id, user_id FROM pending_requests WHERE target_time <= ?', (now,)) as cursor:
            rows = await cursor.fetchall()
            if rows:
                ids = [r[0] for r in rows]
                placeholders = ','.join('?' for _ in ids)
                await db.execute(f'DELETE FROM pending_requests WHERE id IN ({placeholders})', ids)
                await db.commit()
            return rows

async def add_bot_user(token: str, user_id: int):
    now = int(time.time())
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR IGNORE INTO bot_users (bot_token, user_id, joined_at) VALUES (?, ?, ?)', (token, user_id, now))
        await db.commit()

async def get_bot_user_count(token: str) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT COUNT(*) FROM bot_users WHERE bot_token = ?', (token,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def import_bot_users(token: str, user_ids: list):
    now = int(time.time())
    async with aiosqlite.connect(DB_NAME) as db:
        # Prepare data for batch execution
        data = [(token, uid, now) for uid in user_ids]
        await db.executemany('''
            INSERT OR IGNORE INTO bot_users (bot_token, user_id, joined_at)
            VALUES (?, ?, ?)
        ''', data)
        await db.commit()

async def get_bot_user_ids(token: str) -> list:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id FROM bot_users WHERE bot_token = ?', (token,)) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

async def add_channel(bot_token: str, chat_id: int, chat_title: str):
    async with aiosqlite.connect(DB_NAME) as db:
        # Check if already exists
        async with db.execute('SELECT id FROM channels WHERE bot_token = ? AND chat_id = ?', (bot_token, chat_id)) as cursor:
            if await cursor.fetchone():
                return False
        await db.execute('INSERT INTO channels (bot_token, chat_id, chat_title) VALUES (?, ?, ?)', (bot_token, chat_id, chat_title))
        await db.commit()
        return True

async def get_channels(bot_token: str):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM channels WHERE bot_token = ?', (bot_token,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def delete_channel(bot_token: str, chat_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM channels WHERE bot_token = ? AND chat_id = ?', (bot_token, chat_id))
        await db.commit()

async def is_channel_allowed(bot_token: str, chat_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT id FROM channels WHERE bot_token = ? AND chat_id = ?', (bot_token, chat_id)) as cursor:
            return bool(await cursor.fetchone())

# ===== JOIN EVENTS (Limit) =====
async def record_join_event(bot_token: str, chat_id: int):
    now = int(time.time())
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT INTO join_events (bot_token, chat_id, joined_at) VALUES (?, ?, ?)', (bot_token, chat_id, now))
        await db.commit()

async def count_join_events(bot_token: str, chat_id: int, minutes: int) -> int:
    since = int(time.time()) - (minutes * 60)
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            'SELECT COUNT(*) FROM join_events WHERE bot_token = ? AND chat_id = ? AND joined_at >= ?',
            (bot_token, chat_id, since)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def cleanup_old_join_events():
    """Delete join events older than 24 hours (run periodically)"""
    cutoff = int(time.time()) - 86400
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM join_events WHERE joined_at < ?', (cutoff,))
        await db.commit()

# ===== MAILING SYSTEM =====
async def create_mailing(bot_token: str) -> int:
    now = int(time.time())
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('INSERT INTO mailings (bot_token, created_at) VALUES (?, ?)', (bot_token, now))
        await db.commit()
        return cursor.lastrowid

async def get_mailing(mailing_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM mailings WHERE id = ?', (mailing_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_mailing(mailing_id: int, updates: dict):
    if not updates: return
    fields = ', '.join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values())
    values.append(mailing_id)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f'UPDATE mailings SET {fields} WHERE id = ?', values)
        await db.commit()

async def get_scheduled_mailings(bot_token: str):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        # Get all mailings that are scheduled or active
        async with db.execute("SELECT * FROM mailings WHERE bot_token = ? AND status IN ('scheduled', 'paused', 'running', 'draft') ORDER BY id DESC", (bot_token,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def delete_mailing(mailing_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT file_id FROM mailings WHERE id = ?", (mailing_id,)) as cursor:
            row = await cursor.fetchone()
            file_path = row['file_id'] if row else None
            
        await db.execute('DELETE FROM mailings WHERE id = ?', (mailing_id,))
        await db.execute('DELETE FROM mailing_queue WHERE mailing_id = ?', (mailing_id,))
        await db.commit()
        
        if file_path and file_path.startswith('media/'):
            await cleanup_media_file(file_path)

async def is_file_in_use(file_path: str) -> bool:
    """Checks if a file path is referenced in any mailing or bot setting"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Check mailings (scheduled, running, paused, draft)
        async with db.execute("SELECT COUNT(id) FROM mailings WHERE file_id = ? AND status != 'completed'", (file_path,)) as cursor:
            if (await cursor.fetchone())[0] > 0: return True
            
        # Check bot settings (welcome, goodbye, captcha)
        async with db.execute("""
            SELECT COUNT(id) FROM bots 
            WHERE welcome_file_id = ? OR goodbye_file_id = ? OR captcha_file_id = ?
        """, (file_path, file_path, file_path)) as cursor:
            if (await cursor.fetchone())[0] > 0: return True
            
    return False

async def cleanup_media_file(file_path: str):
    """Deletes a file if it's not in use anywhere else"""
    if not file_path or not file_path.startswith('media/'):
        return
    
    import os
    if not await is_file_in_use(file_path):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up unused media: {file_path}")
        except Exception as e:
            print(f"Error cleaning up media {file_path}: {e}")

async def populate_mailing_queue(mailing_id: int, bot_token: str) -> int:
    """Gets all bot users and pushes them to mailing_queue"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Check if already populated
        async with db.execute("SELECT COUNT(id) FROM mailing_queue WHERE mailing_id = ?", (mailing_id,)) as cursor:
            count = (await cursor.fetchone())[0]
            if count > 0:
                return count
        
        # Populate
        await db.execute("""
            INSERT INTO mailing_queue (mailing_id, bot_token, user_id)
            SELECT ?, ?, user_id FROM bot_users WHERE bot_token = ?
        """, (mailing_id, bot_token, bot_token))
        await db.commit()
        
        # Count total
        async with db.execute("SELECT COUNT(id) FROM mailing_queue WHERE mailing_id = ?", (mailing_id,)) as cursor:
            return (await cursor.fetchone())[0]

async def get_pending_mailings():
    """Worker picks up scheduled mailings whose trigger time is met"""
    now = int(time.time())
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mailings WHERE status = 'scheduled' AND schedule_time <= ?", (now,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_active_mailings():
    """Worker picks up running mailings"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mailings WHERE status = 'running'") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_mailing_queue_batch(mailing_id: int, limit: int = 50):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mailing_queue WHERE mailing_id = ? AND status = 'pending' LIMIT ?", (mailing_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def mark_queue_sent(queue_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE mailing_queue SET status = 'sent' WHERE id = ?", (queue_id,))
        await db.commit()

async def increment_mailing_sent(mailing_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE mailings SET sent_cnt = sent_cnt + 1 WHERE id = ?", (mailing_id,))
        await db.commit()

async def increment_mailing_blocked(mailing_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE mailings SET blocked_cnt = blocked_cnt + 1 WHERE id = ?", (mailing_id,))
        await db.commit()

async def mark_queue_failed(queue_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE mailing_queue SET status = 'failed' WHERE id = ?", (queue_id,))
        await db.commit()


async def get_mass_settings(bot_token: str) -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mass_mailing_settings WHERE bot_token = ?", (bot_token,)) as cursor:
            row = await cursor.fetchone()
            if row: return dict(row)
            # Create default row if missing
            await db.execute("INSERT INTO mass_mailing_settings (bot_token) VALUES (?)", (bot_token,))
            await db.commit()
            async with db.execute("SELECT * FROM mass_mailing_settings WHERE bot_token = ?", (bot_token,)) as cursor2:
                row2 = await cursor2.fetchone()
                return dict(row2)

async def update_mass_settings(bot_token: str, fields: dict):
    if not fields: return
    async with aiosqlite.connect(DB_NAME) as db:
        sets = []
        vals = []
        for k, v in fields.items():
            sets.append(f"{k} = ?")
            vals.append(v)
        vals.append(bot_token)
        query = f"UPDATE mass_mailing_settings SET {', '.join(sets)} WHERE bot_token = ?"
        await db.execute(query, tuple(vals))
        await db.commit()
