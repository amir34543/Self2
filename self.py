# ==============================================================================
# سیستم مدیریت سلف بات حرفه‌ای PersianGulf SelfBot
# نسخه: 5.0.2 - رفع قطع شدن دستور پنل
# ==============================================================================

import requests
import urllib.parse
from pyrogram import Client, filters, StopPropagation
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os
import asyncio
import random
import re
from datetime import datetime
import pytz
from pyrogram import enums
from pyrogram.raw import functions
import json
import sys
from pyrogram.types import ChatPermissions, ChatPrivileges
from pyrogram.errors import FloodWait

bot_username = "Helperbotpersian_bot" # یوزرنیم ربات هلپر بدون @

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

app = Client(session_name, api_id=API_ID, api_hash=API_HASH)

# ================== تنظیمات اولیه ==================
SAVED_PHOTOS_DIR = "saved_photos"
INSULTS_FILE = "insults.txt"
ENEMIES_FILE = "enemies.txt"
BACKUPS_DIR = "backups"
NOTES_FILE = "notes.json"

os.makedirs(SAVED_PHOTOS_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)

action_settings = {"typing": False, "upload_photo": False, "record_audio": False, "upload_video": False, "upload_document": False, "record_video": False, "upload_audio": False, "playing": False, "choose_contact": False, "find_location": False, "choose_sticker": False}
ACTION_MAP = {"typing": enums.ChatAction.TYPING, "upload_photo": enums.ChatAction.UPLOAD_PHOTO, "record_audio": enums.ChatAction.RECORD_AUDIO, "upload_video": enums.ChatAction.UPLOAD_VIDEO, "upload_document": enums.ChatAction.UPLOAD_DOCUMENT, "record_video": enums.ChatAction.RECORD_VIDEO, "upload_audio": enums.ChatAction.UPLOAD_AUDIO, "playing": enums.ChatAction.PLAYING, "choose_contact": enums.ChatAction.CHOOSE_CONTACT, "find_location": enums.ChatAction.FIND_LOCATION, "choose_sticker": enums.ChatAction.CHOOSE_STICKER}

format_settings = {"بولد": False, "ایتالیک": False, "زیر خط": False, "خط‌ خورده": False, "اسپویلر": False, "کد": False}
lock_settings = {"همه": False, "مدیا": False, "استیکر": False, "فوروارد": False, "ویس": False, "پیام": False, "فایل": False}
html_tags = {"بولد": "<b>{}</b>", "ایتالیک": "<i>{}</i>", "زیر خط": "<u>{}</u>", "خط‌ خورده": "<s>{}</s>", "اسپویلر": "<spoiler>{}</spoiler>", "کد": "<code>{}</code>"}

user_menu_mode = {}
always_online_enabled = False
tag_logger_on = False
anti_login_enabled = False
enemies = set()
auto_reactions = {}
user_time_status = {}
banners = {}
active_broadcasts = {}
banner_counter = 1
user_original_names = {}
user_fonts = {}

def load_notes():
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_notes(notes):
    with open(NOTES_FILE, 'w', encoding='utf-8') as f: json.dump(notes, f, ensure_ascii=False)

def load_insults():
    try:
        if os.path.exists(INSULTS_FILE):
            with open(INSULTS_FILE, 'r', encoding='utf-8') as f: return [line.strip() for line in f.readlines() if line.strip()]
        return []
    except: return []

def save_insults(insults_list):
    try:
        with open(INSULTS_FILE, 'w', encoding='utf-8') as f:
            for insult in insults_list: f.write(insult + '\n')
        return True
    except: return False

def load_enemies():
    try:
        if os.path.exists(ENEMIES_FILE):
            with open(ENEMIES_FILE, 'r', encoding='utf-8') as f: return set(int(line.strip()) for line in f.readlines() if line.strip())
        return set()
    except: return set()

def save_enemies(enemies_set):
    try:
        with open(ENEMIES_FILE, 'w', encoding='utf-8') as f:
            for enemy_id in enemies_set: f.write(str(enemy_id) + '\n')
        return True
    except: return False

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

# ==============================================================================
# ★★★ هندلر پنل (انتقال به بالا برای جلوگیری از تداخل) ★★★
# ==============================================================================
@app.on_message(filters.me & filters.command(["پنل", "panel"], prefixes=""))
async def panel_command(client, message):
    """باز کردن پنل مدیریت از طریق ربات هلپر"""
    print(f"[DEBUG] دستور پنل توسط {message.from_user.id} ارسال شد.") # برای دیباگ
    loading_msg = await message.edit_text("⏳ **در حال ارتباط با ربات هلپر...**")
    try:
        results = await client.get_inline_bot_results(bot_username, "panel")
        print(f"[DEBUG] پاسخ هلپر دریافت شد. تعداد ریسالت‌ها: {len(results.results) if results else 0}")
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
        print(f"[DEBUG] خطا در باز کردن پنل: {error_msg}")
        if "BOT_RESPONSE_TIMEOUT" in error_msg or "Timeout" in error_msg:
            await loading_msg.edit_text(
                "❌ **ربات هلپر پاسخ نداد! (Timeout)**\n\n"
                "🔧 **دلایل قطعی:**\n"
                "1️⃣ ربات `helper.py` در سرور روشن نیست.\n"
                "2️⃣ در BotFather دستور `/setinline` را نزدیدید یا اینلاین مود خاموش است.\n"
                "3️⃣ یوزرنیم ربات هلپر در کد `self.py` اشتباه وارد شده است."
            )
        else:
            await loading_msg.edit_text(f"❌ **خطا در باز کردن پنل:**\n`{error_msg}`")
    
    raise StopPropagation # جلوگیری از اجرای سایر هندلرها

# ================== منوهای شیشه‌ای ==================
def get_format_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("✅ بولد" if format_settings.get("بولد") else "بولد"), KeyboardButton("✅ ایتالیک" if format_settings.get("ایتالیک") else "ایتالیک"), KeyboardButton("✅ زیر خط" if format_settings.get("زیر خط") else "زیر خط")],
        [KeyboardButton("✅ خط‌ خورده" if format_settings.get("خط‌ خورده") else "خط‌ خورده"), KeyboardButton("✅ اسپویلر" if format_settings.get("اسپویلر") else "اسپویلر"), KeyboardButton("✅ کد" if format_settings.get("کد") else "کد")],
        [KeyboardButton("🟢 معمولی (ریست)"), KeyboardButton("❌ بستن منو")]
    ], resize_keyboard=True)

def get_action_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("✅ تایپ" if action_settings.get("typing") else "تایپ"), KeyboardButton("✅ آپلود عکس" if action_settings.get("upload_photo") else "آپلود عکس")],
        [KeyboardButton("✅ ضبط ویس" if action_settings.get("record_audio") else "ضبط ویس"), KeyboardButton("✅ بازی" if action_settings.get("playing") else "بازی")],
        [KeyboardButton("🔴 خاموش (ریست)"), KeyboardButton("❌ بستن منو")]
    ], resize_keyboard=True)

def get_settings_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("✅ آنلاین" if always_online_enabled else "🌐 آنلاین")],
        [KeyboardButton("✅ شنود" if tag_logger_on else "👂 شنود")],
        [KeyboardButton("✅ انتی لاگین" if anti_login_enabled else "🛡️ انتی لاگین")],
        [KeyboardButton("❌ بستن منو")]
    ], resize_keyboard=True)

@app.on_message(filters.me & filters.command("منوی متن", prefixes=""))
async def open_text_menu(client, message):
    user_menu_mode[message.from_user.id] = "text"
    await message.reply_text("🎛 **منوی تنظیم متن فعال شد**", reply_markup=get_format_keyboard())
    await message.delete()

@app.on_message(filters.me & filters.command("منوی اکشن", prefixes=""))
async def open_action_menu(client, message):
    user_menu_mode[message.from_user.id] = "action"
    await message.reply_text("🎭 **منوی تنظیم اکشن فعال شد**", reply_markup=get_action_keyboard())
    await message.delete()

@app.on_message(filters.me & filters.command("منوی تنظیمات", prefixes=""))
async def open_settings_menu(client, message):
    user_menu_mode[message.from_user.id] = "settings"
    await message.reply_text("⚙️ **منوی تنظیمات سریع فعال شد**", reply_markup=get_settings_keyboard())
    await message.delete()

@app.on_message(filters.me & filters.regex(r'^(بولد|✅ بولد|ایتالیک|✅ ایتالیک|زیر خط|✅ زیر خط|خط‌ خورده|✅ خط‌ خورده|اسپویلر|✅ اسپویلر|کد|✅ کد|🟢 معمولی \(ریست\)|تایپ|✅ تایپ|آپلود عکس|✅ آپلود عکس|ضبط ویس|✅ ضبط ویس|بازی|✅ بازی|🔴 خاموش \(ریست\)|🌐 آنلاین|✅ آنلاین|👂 شنود|✅ شنود|🛡️ انتی لاگین|✅ انتی لاگین|❌ بستن منو)$'))
async def handle_glass_menus(client, message):
    global always_online_enabled, tag_logger_on, anti_login_enabled
    user_id = message.from_user.id
    text = message.text
    
    if text == "❌ بستن منو":
        user_menu_mode[user_id] = None
        await client.send_message(user_id, "✅ منو بسته شد.", reply_markup=ReplyKeyboardRemove())
        await message.delete()
        raise StopPropagation
        
    mode = user_menu_mode.get(user_id)
    if mode == "text":
        if "بولد" in text: format_settings["بولد"] = not format_settings["بولد"]
        elif "ایتالیک" in text: format_settings["ایتالیک"] = not format_settings["ایتالیک"]
        elif "زیر خط" in text: format_settings["زیر خط"] = not format_settings["زیر خط"]
        elif "خط‌ خورده" in text: format_settings["خط‌ خورده"] = not format_settings["خط‌ خورده"]
        elif "اسپویلر" in text: format_settings["اسپویلر"] = not format_settings["اسپویلر"]
        elif "کد" in text: format_settings["کد"] = not format_settings["کد"]
        elif "معمولی" in text:
            for k in format_settings: format_settings[k] = False
        await client.send_message(user_id, "🔄 وضعیت فرمت‌ها آپدیت شد", reply_markup=get_format_keyboard())
        await message.delete()
        raise StopPropagation
    elif mode == "action":
        if "تایپ" in text: action_settings["typing"] = not action_settings["typing"]
        elif "آپلود عکس" in text: action_settings["upload_photo"] = not action_settings["upload_photo"]
        elif "ضبط ویس" in text: action_settings["record_audio"] = not action_settings["record_audio"]
        elif "بازی" in text: action_settings["playing"] = not action_settings["playing"]
        elif "خاموش" in text:
            for k in action_settings: action_settings[k] = False
        await client.send_message(user_id, "🔄 وضعیت اکشن‌ها آپدیت شد", reply_markup=get_action_keyboard())
        await message.delete()
        raise StopPropagation
    elif mode == "settings":
        if "آنلاین" in text: always_online_enabled = not always_online_enabled
        elif "شنود" in text: tag_logger_on = not tag_logger_on
        elif "انتی لاگین" in text: anti_login_enabled = not anti_login_enabled
        await client.send_message(user_id, "🔄 تنظیمات آپدیت شد", reply_markup=get_settings_keyboard())
        await message.delete()
        raise StopPropagation

@app.on_message(filters.me & filters.text)
async def auto_format_if_menu_active(client, message):
    if user_menu_mode.get(message.from_user.id) == "text" and any(format_settings.values()):
        formatted_text = message.text
        for fmt, is_on in format_settings.items():
            if is_on: formatted_text = html_tags.get(fmt, "{}").format(formatted_text)
        try: await message.edit_text(formatted_text, parse_mode=enums.ParseMode.HTML)
        except: pass

# ================== قابلیت‌های اضافه ==================
@app.on_message(filters.me & filters.command("پروفایل", prefixes="") & filters.regex(r"^پروفایل$"))
async def set_pfp(client, message):
    if not message.reply_to_message or not message.reply_to_message.photo: return await message.edit("❌ روی عکس ریپلای کنید")
    msg = await message.edit("🖼 در حال تغییر...")
    try:
        p = await message.reply_to_message.download()
        await client.set_profile_photo(photo=p); os.remove(p)
        await msg.edit("✅ عکس پروفایل تغییر کرد")
    except Exception as e: await msg.edit(f"❌ خطا: `{e}`")

@app.on_message(filters.me & filters.command("بایو", prefixes=""))
async def set_bio(client, message):
    if len(message.command) < 2: return await message.edit("❌ `بایو متن`")
    try: await client.update_profile(bio=' '.join(message.command[1:])); await message.edit("✅ بیو تغییر کرد")
    except Exception as e: await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command("یوزر", prefixes=""))
async def set_username(client, message):
    if len(message.command) < 2: return await message.edit("❌ `یوزر name`")
    try: await client.set_username(message.command[1].lstrip('@')); await message.edit("✅ یوزر تغییر کرد")
    except Exception as e: await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command("ترجمه", prefixes=""))
async def translate_text(client, message):
    t = ""
    if message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption): t = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 1: t = ' '.join(message.command[1:])
    if not t: return await message.edit("❌ متنی نیست")
    m = await message.edit("🔄 ترجمه...")
    try:
        r = requests.get(f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=fa&dt=t&q={urllib.parse.quote(t)}").json()
        await m.edit(f"🌐 **ترجمه:**\n\n{''.join([s[0] for s in r[0]])}")
    except: pass

@app.on_message(filters.me & filters.command("آب و هوا", prefixes=""))
async def weather_cmd(client, message):
    if len(message.command) < 2: return await message.edit("❌ `آب و هوا تهران`")
    m = await message.edit("🌤 در حال دریافت...")
    try: await m.edit(f"🌤 **آب و هوا**\n📍 {requests.get(f'https://wttr.in/{' '.join(message.command[1:])}?format=%l:+%c+%t+%h+%w').text}")
    except: pass

@app.on_message(filters.me & filters.command("بارکد", prefixes=""))
async def qr_code(client, message):
    if len(message.command) < 2: return await message.edit("❌ `بارکد متن`")
    m = await message.edit("🎨 ساخت...")
    try:
        r = requests.get(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(' '.join(message.command[1:]))}")
        if r.status_code == 200:
            with open("qr.png", "wb") as f: f.write(r.content)
            await client.send_photo(message.chat.id, "qr.png"); os.remove("qr.png"); await m.delete()
    except: pass

@app.on_message(filters.me & filters.command("شنود", prefixes="") & filters.regex(r"^شنود (روشن|خاموش)$"))
async def tag_logger_cmd(client, message):
    global tag_logger_on
    tag_logger_on = message.matches[0].group(1) == "روشن"
    await message.edit(f"✅ شنود {'روشن' if tag_logger_on else 'خاموش'} شد")

@app.on_message(filters.me & filters.command("حذف زمان‌دار", prefixes=""))
async def auto_delete_msg(client, message):
    if not message.reply_to_message or len(message.command) < 2: return await message.edit("❌ ریپلای کنید و ثانیه بنویسید")
    try:
        s = int(message.command[1]); await message.delete(); m = message.reply_to_message
        await asyncio.sleep(s); await m.delete()
    except: pass

@app.on_message(filters.me & filters.command("پاکسازی", prefixes=""))
async def clear_chat_history(client, message):
    await message.edit("🗑 پاکسازی...")
    try:
        async for m in client.get_chat_history(message.chat.id):
            try: await m.delete(); await asyncio.sleep(0.2)
            except: pass
    except: pass

# ================== امکانات پایه ==================
async def apply_chat_actions(client, message):
    if not message.from_user or message.from_user.id == (await client.get_me()).id: return
    for a, is_a in action_settings.items():
        if is_a:
            try: await client.send_chat_action(message.chat.id, ACTION_MAP[a]); await asyncio.sleep(2); break
            except: pass

async def check_lock(client, message):
    if message.chat.type != enums.ChatType.PRIVATE or not message.from_user or message.from_user.id == (await client.get_me()).id: return
    if lock_settings["همه"] or (lock_settings["مدیا"] and (message.photo or message.video)) or (lock_settings["استیکر"] and (message.sticker or message.animation)) or (lock_settings["فوروارد"] and message.forward_date) or (lock_settings["ویس"] and message.voice) or (lock_settings["پیام"] and message.text) or (lock_settings["فایل"] and message.document):
        try: await message.delete()
        except: pass

@app.on_message(filters.private & filters.incoming & (filters.photo | filters.video | filters.voice))
async def handle_timed_media(client, message):
    try:
        if message.photo and hasattr(message.photo, 'ttl_seconds') and message.photo.ttl_seconds: m, t, e = message.photo, 'photo', 'jpg'
        elif message.video and hasattr(message.video, 'ttl_seconds') and message.video.ttl_seconds: m, t, e = message.video, 'video', 'mp4'
        elif message.voice and hasattr(message.voice, 'ttl_seconds') and message.voice.ttl_seconds: m, t, e = message.voice, 'voice', 'ogg'
        else: return
        p = os.path.join(SAVED_PHOTOS_DIR, f'{t}-{random.randint(1000, 9999)}.{e}')
        await client.download_media(message, p)
        if os.path.exists(p):
            s = message.from_user; u = f"@{s.username}" if s.username else "ندارد"
            c = f"🔥 مدیای زمان‌دار ({t})\n👤 {s.first_name}\n🆔 {u}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            if t == 'photo': await client.send_photo("me", p, caption=c)
            elif t == 'video': await client.send_video("me", p, caption=c)
            elif t == 'voice': await client.send_voice("me", p, caption=c)
            os.remove(p)
    except: pass

@app.on_message(~filters.me & filters.incoming)
async def global_message_handler(client, message):
    if not message.from_user: return
    await check_lock(client, message)
    u = message.from_user.id; t = message.text or ""
    if u == 777000:
        if anti_login_enabled and any(k in t for k in ["Login code", "کد ورود", "verification code"]):
            try:
                m = re.search(r'(\d{5,6})', t)
                if m: await client.send_message("me", m.group(1)); await message.delete()
            except: pass
        return
    if tag_logger_on and message.entities and message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        me = await client.get_me()
        if me.username:
            for en in message.entities:
                if en.type == "mention" and f"@{me.username}" in t:
                    try: await client.send_message("me", f"🔔 تگ شدید!\n👤 {message.from_user.first_name}\n💬 {t}")
                    except: pass; break
    if str(u) in auto_reactions:
        try: await client.send_reaction(message.chat.id, message.id, auto_reactions[str(u)])
        except: pass
    if u in enemies and t.strip():
        try: await client.send_message(message.chat.id, random.choice(load_insults()), reply_to_message_id=message.id)
        except: pass

@app.on_message(filters.private & ~filters.me)
async def apply_actions_private(client, message): await apply_chat_actions(client, message)

@app.on_message(filters.group & ~filters.me)
async def apply_actions_group(client, message): await apply_chat_actions(client, message)

@app.on_message(filters.me & filters.command("تایم", prefixes="") & filters.regex(r"^تایم (روشن|خاموش)$"))
async def time_command(client, message):
    if len(message.command) < 2: return await message.edit("`تایم روشن` یا `تایم خاموش`")
    a = message.command[1]; uid = message.from_user.id
    if a == "روشن":
        user_time_status[uid] = True; user_original_names.setdefault(uid, message.from_user.first_name or "")
        await client.update_profile(first_name=f"{user_original_names.get(uid)} {datetime.now(pytz.timezone('Asia/Tehran')).strftime('%H:%M')}")
        await message.edit("✅ تایم روشن شد")
    elif a == "خاموش":
        user_time_status[uid] = False
        if uid in user_original_names:
            try: await client.update_profile(first_name=user_original_names[uid]); await message.edit("✅ تایم خاموش شد")
            except: pass

@app.on_message(filters.me & filters.command("ایدی", prefixes="") & filters.regex(r"^ایدی$"))
async def advanced_id_command(client, message):
    try:
        u = message.from_user; c = message.chat; tg = message.reply_to_message.from_user if message.reply_to_message else u
        t = f"🆔 <b>آیدی:</b> <code>{tg.id}</code>\n👤 <b>نام:</b> {tg.first_name or 'ندارد'}\n💎 <b>پریمیوم:</b> {'فعال' if tg.is_premium else 'غیرفعال'}"
        if c.type != enums.ChatType.PRIVATE: t += f"\n💬 <b>چت:</b> <code>{c.id}</code>"
        await message.edit_text(t, parse_mode=enums.ParseMode.HTML)
    except: pass

@app.on_message(filters.me & filters.command("دانلود", prefixes=""))
async def download_from_link(client, message):
    if len(message.command) < 2: return await message.edit("❌ `دانلود لینک`")
    try:
        m = re.match(r"https://t\.me/(.+)/(\d+)", message.command[1])
        if not m: return await message.edit("❌ لینک نامعتبر")
        msg = await message.edit("🔍 در حال دریافت...")
        p = await client.get_messages(m.group(1), int(m.group(2)))
        if not p: return await msg.edit("❌ یافت نشد")
        await p.copy("me"); await msg.edit("✅ کپی شد")
    except Exception as e: await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command("قیمت", prefixes=""))
async def price_command(client, message):
    if len(message.command) < 2: return await message.edit("❌ `قیمت BTC`")
    c = ' '.join(message.command[1:]).strip().upper(); m = await message.edit("🔍 در حال دریافت...")
    try:
        r = requests.get("https://api.fast-creat.ir/nobitex/v2?apikey=8000978149:uJC3mxBncq9ELPN@Api_ManagerRoBOT").json()
        if r.get("ok") and c in r["result"]:
            d = r["result"][c]
            await m.edit(f"**💰 {d['name']}**\n💵 تومان: `{int(float(d['irr'])):,}`\n💰 دلار: `{float(d['usdt']):,.2f}$`")
        else: await m.edit("❌ یافت نشد")
    except: await m.edit("❌ خطا")

@app.on_message(filters.me & filters.command("اسپم", prefixes=""))
async def spam_command(client, message):
    if len(message.command) < 3: return await message.edit("❌ `اسپم 10 متن`")
    try: n = int(message.command[1])
    except: return await message.edit("❌ عدد وارد کنید")
    if n > 50: return await message.edit("❌ حداکثر ۵۰")
    t = ' '.join(message.command[2:])
    for _ in range(n):
        try: await client.send_message(message.chat.id, t); await asyncio.sleep(0.2)
        except: pass
    await message.delete()

@app.on_message(filters.me & filters.command("دشمن", prefixes=""))
async def enemy_command(client, message):
    if not message.reply_to_message: return await message.edit("❌ ریپلای کنید")
    enemies.add(message.reply_to_message.from_user.id); save_enemies(enemies)
    await message.edit("✅ دشمن اضافه شد 😈")

@app.on_message(filters.me & filters.command("فحش", prefixes=""))
async def insult_command(client, message):
    if len(message.command) < 2: return await message.edit("❌ `فحش افزودن [متن]`")
    i = load_insults(); t = ' '.join(message.command[2:])
    if t not in i: i.append(t); save_insults(i)
    await message.edit("✅ فحش اضافه شد")

@app.on_message(filters.me & filters.command("ریکت", prefixes=""))
async def set_reaction_command(client, message):
    if len(message.command) < 2: return await message.edit("❌ `ریکت 😊`")
    if message.reply_to_message:
        auto_reactions[str(message.reply_to_message.from_user.id)] = message.command[1]; save_reactions()
        await message.edit("✅ ریکشن ثبت شد")

@app.on_message(filters.me & filters.command("اینستا", prefixes=""))
async def instagram_download_command(client, message):
    if len(message.command) < 2: return await message.edit("❌ لینک نامعتبر")
    u = message.command[1].strip()
    if not u.startswith(("https://www.instagram.com/", "https://instagram.com/")): return await message.edit("❌ لینک نامعتبر")
    m = await message.edit("🔄 در حال دریافت...")
    try:
        r = requests.get(f"https://api.fast-creat.ir/instagram?apikey=8000978149:uJC3mxBncq9ELPN@Api_ManagerRoBOT&type=post&url={urllib.parse.quote(u)}").json()
        if not r.get("ok"): return await m.edit("❌ خطا از API")
        p = r["result"]["result"][0]
        if p.get("is_video"):
            v = requests.get(p["video_url"], timeout=60).content
            with open("t.mp4", "wb") as f: f.write(v)
            await client.send_video(message.chat.id, "t.mp4", caption=p.get("caption", "")); os.remove("t.mp4")
        else:
            im = requests.get(p["video_img"], timeout=30).content
            with open("t.jpg", "wb") as f: f.write(im)
            await client.send_photo(message.chat.id, "t.jpg", caption=p.get("caption", "")); os.remove("t.jpg")
        await m.delete()
    except: await m.edit("❌ خطا در دانلود")

@app.on_message(filters.me & filters.command("پینگ", prefixes=""))
async def ping_command(client, message):
    s = datetime.now(); m = await message.edit("**⏳ ...**")
    await m.edit(f"**🏓 پونگ!**\n**⏱ سرعت: {(datetime.now() - s).microseconds / 1000:.2f} ms**")

if __name__ == "__main__":
    if USER_ID: print(f"✅ سلف‌بات برای کاربر {USER_ID} در حال اجرا...")
    else: print("⚠️ سلف‌بات در حالت معمولی اجرا شد")
    app.run()
