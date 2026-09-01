import requests
import urllib.parse
from pyrogram import Client, filters, StopPropagation
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os
import asyncio
import aiohttp
import random
import re
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

# ==============================================================================
# تنظیمات اولیه و متغیرهای سراسری
# ==============================================================================

bot_username = "Helperbotpersian_bot" # یوزرنیم ربات هلپر بدون @

USER_ID = None
PHONE = None
API_ID = 35656061
API_HASH = "b37f2596516bc0439bf505d1d230395c"

if len(sys.argv) > 1:
    USER_ID = int(sys.argv[1])
if len(sys.argv) > 2:
    PHONE = sys.argv[2]
if len(sys.argv) > 3:
    API_ID = int(sys.argv[3])
if len(sys.argv) > 4:
    API_HASH = sys.argv[4]

if USER_ID:
    session_name = f"sessions/{USER_ID}"
else:
    session_name = "self"

app = Client(session_name, api_id=API_ID, api_hash=API_HASH)

# ==============================================================================
# مسیرهای فایل و دایرکتوری‌ها
# ==============================================================================

SAVED_PHOTOS_DIR = "saved_photos"
INSULTS_FILE = "insults.txt"
ENEMIES_FILE = "enemies.txt"
BACKUPS_DIR = "backups"
NOTES_FILE = "notes.json"

os.makedirs(SAVED_PHOTOS_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)

# ==============================================================================
# تنظیمات اکشن‌ها و فرمت‌ها و قفل‌ها
# ==============================================================================

action_settings = {
    "typing": False, 
    "upload_photo": False, 
    "record_audio": False, 
    "upload_video": False, 
    "upload_document": False,
    "record_video": False, 
    "upload_audio": False, 
    "playing": False, 
    "choose_contact": False, 
    "find_location": False, 
    "choose_sticker": False
}

ACTION_MAP = {
    "typing": enums.ChatAction.TYPING,
    "upload_photo": enums.ChatAction.UPLOAD_PHOTO,
    "record_audio": enums.ChatAction.RECORD_AUDIO,
    "upload_video": enums.ChatAction.UPLOAD_VIDEO,
    "upload_document": enums.ChatAction.UPLOAD_DOCUMENT,
    "record_video": enums.ChatAction.RECORD_VIDEO,
    "upload_audio": enums.ChatAction.UPLOAD_AUDIO,
    "playing": enums.ChatAction.PLAYING,
    "choose_contact": enums.ChatAction.CHOOSE_CONTACT,
    "find_location": enums.ChatAction.FIND_LOCATION,
    "choose_sticker": enums.ChatAction.CHOOSE_STICKER
}

format_settings = {
    "بولد": False,
    "ایتالیک": False,
    "زیر خط": False,
    "خط‌ خورده": False,
    "اسپویلر": False,
    "کد": False
}

lock_settings = {
    "همه": False,
    "مدیا": False,
    "استیکر": False,
    "فوروارد": False,
    "ویس": False,
    "پیام": False,
    "فایل": False
}

html_tags = {
    "بولد": "<b>{}</b>",
    "ایتالیک": "<i>{}</i>",
    "زیر خط": "<u>{}</u>",
    "خط‌ خورده": "<s>{}</s>",
    "اسپویلر": "<spoiler>{}</spoiler>",
    "کد": "<code>{}</code>"
}

# ==============================================================================
# متغیرهای وضعیت سیستم
# ==============================================================================

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

FONTS = {
    1: {'0':'𝟎','1':'𝟏','2':'𝟐','3':'𝟑','4':'𝟒','5':'𝟓','6':'𝟔','7':'𝟕','8':'𝟖','9':'𝟗'},
    2: {'0':'𝟬','1':'𝟭','2':'𝟮','3':'𝟯','4':'𝟰','5':'𝟱','6':'𝟲','7':'𝟳','8':'𝟴','9':'𝟵'},
    3: {'0':'０','1':'１','2':'２','3':'３','4':'４','5':'５','6':'۶','7':'７','8':'８','9':'９'},
    4: {'0':'𝟢','1':'𝟣','2':'𝟤','3':'𝟥','4':'𝟦','5':'𝟧','6':'𝟨','7':'𝟩','8':'𝟪','9':'𝟫'},
    5: {'0':'𝟘','1':'𝟙','2':'𝟚','3':'𝟛','4':'𝟜','5':'𝟝','6':'𝟞','7':'𝟟','8':'𝟠','9':'𝟡'},
    6: {'0':'0҉','1':'1҉','2':'2҉','3':'3҉','4':'4҉','5':'5҉','6':'6҉','7':'7҉','8':'8҉','9':'9҉'}
}

# ==============================================================================
# توابع مدیریت فایل‌ها
# ==============================================================================

def load_notes():
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_notes(notes):
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False)

def load_insults():
    try:
        if os.path.exists(INSULTS_FILE):
            with open(INSULTS_FILE, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        return []
    except:
        return []

def save_insults(insults_list):
    try:
        with open(INSULTS_FILE, 'w', encoding='utf-8') as f:
            for insult in insults_list:
                f.write(insult + '\n')
        return True
    except:
        return False

def load_enemies():
    try:
        if os.path.exists(ENEMIES_FILE):
            with open(ENEMIES_FILE, 'r', encoding='utf-8') as f:
                return set(int(line.strip()) for line in f.readlines() if line.strip())
        return set()
    except:
        return set()

def save_enemies(enemies_set):
    try:
        with open(ENEMIES_FILE, 'w', encoding='utf-8') as f:
            for enemy_id in enemies_set:
                f.write(str(enemy_id) + '\n')
        return True
    except:
        return False

def is_enemy(user_id):
    return user_id in enemies

def save_reactions():
    try:
        with open("mmauto_reactions.json", "w", encoding="utf-8") as f:
            json.dump(auto_reactions, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

def load_reactions():
    try:
        if os.path.exists("mmauto_reactions.json"):
            with open("mmauto_reactions.json", "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        return {}
    except:
        return {}

enemies = load_enemies()
auto_reactions = load_reactions()

# ==============================================================================
# ساخت کیبوردهای شیشه‌ای تعاملی (Glass Buttons)
# ==============================================================================

def get_format_keyboard():
    """ساخت کیبورد شیشه‌ای برای فرمت متن"""
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("✅ بولد" if format_settings.get("بولد") else "بولد"),
                KeyboardButton("✅ ایتالیک" if format_settings.get("ایتالیک") else "ایتالیک"),
                KeyboardButton("✅ زیر خط" if format_settings.get("زیر خط") else "زیر خط")
            ],
            [
                KeyboardButton("✅ خط‌ خورده" if format_settings.get("خط‌ خورده") else "خط‌ خورده"),
                KeyboardButton("✅ اسپویلر" if format_settings.get("اسپویلر") else "اسپویلر"),
                KeyboardButton("✅ کد" if format_settings.get("کد") else "کد")
            ],
            [
                KeyboardButton("🟢 معمولی (ریست)"),
                KeyboardButton("❌ بستن منو")
            ]
        ],
        resize_keyboard=True
    )

def get_action_keyboard():
    """ساخت کیبورد شیشه‌ای برای اکشن‌ها"""
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("✅ تایپ" if action_settings.get("typing") else "تایپ"),
                KeyboardButton("✅ آپلود عکس" if action_settings.get("upload_photo") else "آپلود عکس")
            ],
            [
                KeyboardButton("✅ ضبط ویس" if action_settings.get("record_audio") else "ضبط ویس"),
                KeyboardButton("✅ بازی" if action_settings.get("playing") else "بازی")
            ],
            [
                KeyboardButton("🔴 خاموش (ریست)"),
                KeyboardButton("❌ بستن منو")
            ]
        ],
        resize_keyboard=True
    )

def get_settings_keyboard():
    """ساخت کیبورد شیشه‌ای برای تنظیمات سریع"""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("✅ آنلاین" if always_online_enabled else "🌐 آنلاین")],
            [KeyboardButton("✅ شنود" if tag_logger_on else "👂 شنود")],
            [KeyboardButton("✅ انتی لاگین" if anti_login_enabled else "🛡️ انتی لاگین")],
            [KeyboardButton("❌ بستن منو")]
        ],
        resize_keyboard=True
    )

# ==============================================================================
# هندلرهای باز کردن منوهای شیشه‌ای
# ==============================================================================

@app.on_message(filters.me & filters.command("منوی متن", prefixes=""))
async def open_text_menu(client, message):
    """باز کردن منوی تنظیم متن"""
    user_menu_mode[message.from_user.id] = "text"
    await message.reply_text(
        "🎛 **منوی تنظیم متن فعال شد**\n\n"
        "با کلیک روی دکمه‌ها، فرمت را روشن/خاموش کنید (تیک ✅ می‌خورد).\n"
        "سپس متن خود را بفرستید تا با فرمت انتخاب شده ارسال شود.",
        reply_markup=get_format_keyboard()
    )
    await message.delete()

@app.on_message(filters.me & filters.command("منوی اکشن", prefixes=""))
async def open_action_menu(client, message):
    """باز کردن منوی تنظیم اکشن"""
    user_menu_mode[message.from_user.id] = "action"
    await message.reply_text(
        "🎭 **منوی تنظیم اکشن فعال شد**\n\n"
        "با کلیک روی دکمه‌ها، اکشن را روشن/خاموش کنید.",
        reply_markup=get_action_keyboard()
    )
    await message.delete()

@app.on_message(filters.me & filters.command("منوی تنظیمات", prefixes=""))
async def open_settings_menu(client, message):
    """باز کردن منوی تنظیمات سریع"""
    user_menu_mode[message.from_user.id] = "settings"
    await message.reply_text(
        "⚙️ **منوی تنظیمات سریع فعال شد**",
        reply_markup=get_settings_keyboard()
    )
    await message.delete()

# ==============================================================================
# هندلر مدیریت دکمه‌های شیشه‌ای (تیک خوردن و خاموش شدن)
# ==============================================================================

@app.on_message(filters.me & filters.regex(r'^(بولد|✅ بولد|ایتالیک|✅ ایتالیک|زیر خط|✅ زیر خط|خط‌ خورده|✅ خط‌ خورده|اسپویلر|✅ اسپویلر|کد|✅ کد|🟢 معمولی \(ریست\)|تایپ|✅ تایپ|آپلود عکس|✅ آپلود عکس|ضبط ویس|✅ ضبط ویس|بازی|✅ بازی|🔴 خاموش \(ریست\)|🌐 آنلاین|✅ آنلاین|👂 شنود|✅ شنود|🛡️ انتی لاگین|✅ انتی لاگین|❌ بستن منو)$'))
async def handle_glass_menus(client, message):
    """مدیریت کلیک روی دکمه‌های شیشه‌ای"""
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
    """فرمت کردن متن در صورتی که منوی متن باز باشد"""
    if user_menu_mode.get(message.from_user.id) == "text" and any(format_settings.values()):
        formatted_text = message.text
        for fmt, is_on in format_settings.items():
            if is_on:
                formatted_text = html_tags.get(fmt, "{}").format(formatted_text)
        try: 
            await message.edit_text(formatted_text, parse_mode=enums.ParseMode.HTML)
        except: 
            pass

# ==============================================================================
# قابلیت‌های جدید اضافه شده (پروفایل، بایو، یادداشت، ترجمه و...)
# ==============================================================================

@app.on_message(filters.me & filters.command("پروفایل", prefixes="") & filters.regex(r"^پروفایل$"))
async def set_pfp(client, message):
    """تغییر عکس پروفایل با ریپلای روی عکس"""
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
    """تغییر بیوگرافی اکانت"""
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
    """تغییر یوزرنیم اکانت"""
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
    """ثبت یادداشت جدید"""
    if len(message.command) < 2:
        return await message.edit("❌ **استفاده:** `یادداشت متن`")
    notes = load_notes()
    note_id = str(len(notes) + 1)
    notes[note_id] = ' '.join(message.command[1:])
    save_notes(notes)
    await message.edit(f"✅ **یادداشت شماره {note_id} ذخیره شد**")

@app.on_message(filters.me & filters.command("یادداشت‌ها", prefixes=""))
async def list_notes(client, message):
    """نمایش لیست یادداشت‌ها"""
    notes = load_notes()
    if not notes:
        return await message.edit("❌ **هیچ یادداشتی ثبت نشده**")
    text = "📝 **لیست یادداشت‌ها**\n\n"
    for nid, txt in notes.items():
        text += f"**{nid}.** {txt[:50]}...\n"
    await message.edit(text)

@app.on_message(filters.me & filters.command("حذف یادداشت", prefixes=""))
async def del_note(client, message):
    """حذف یادداشت با آیدی"""
    if len(message.command) < 2:
        return await message.edit("❌ **استفاده:** `حذف یادداشت آیدی`")
    notes = load_notes()
    nid = message.command[1]
    if nid in notes:
        del notes[nid]
        save_notes(notes)
        await message.edit(f"✅ **یادداشت {nid} حذف شد**")
    else:
        await message.edit("❌ **یادداشت یافت نشد**")

@app.on_message(filters.me & filters.command("ترجمه", prefixes=""))
async def translate_text(client, message):
    """ترجمه متن به فارسی (با ریپلای یا تایپ مستقیم)"""
    text_to_translate = ""
    if message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
        text_to_translate = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 1:
        text_to_translate = ' '.join(message.command[1:])
    if not text_to_translate:
        return await message.edit("❌ **متنی برای ترجمه یافت نشد**")
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
    """نمایش وضعیت آب و هوا"""
    if len(message.command) < 2:
        return await message.edit("❌ **استفاده:** `آب و هوا تهران`")
    city = ' '.join(message.command[1:])
    loading_msg = await message.edit(f"🌤 **در حال دریافت آب و هوای {city}...**")
    try:
        resp = requests.get(f"https://wttr.in/{city}?format=%l:+%c+%t+%h+%w").text
        await loading_msg.edit(f"🌤 **آب و هوا**\n\n📍 {resp}")
    except Exception as e:
        await loading_msg.edit(f"❌ **خطا:** `{e}`")

@app.on_message(filters.me & filters.command("بارکد", prefixes=""))
async def qr_code(client, message):
    """ساخت بارکد QR"""
    if len(message.command) < 2:
        return await message.edit("❌ **استفاده:** `بارکد متن`")
    text = ' '.join(message.command[1:])
    loading_msg = await message.edit("🎨 **در حال ساخت بارکد...**")
    try:
        url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(text)}"
        resp = requests.get(url)
        if resp.status_code == 200:
            with open("qr.png", "wb") as f:
                f.write(resp.content)
            await client.send_photo(message.chat.id, "qr.png", caption=f"✅ **بارکد شما:**\n`{text}`")
            os.remove("qr.png")
            await loading_msg.delete()
        else:
            await loading_msg.edit("❌ **خطا در ساخت بارکد**")
    except Exception as e:
        await loading_msg.edit(f"❌ **خطا:** `{e}`")

@app.on_message(filters.me & filters.command("شنود", prefixes="") & filters.regex(r"^شنود (روشن|خاموش)$"))
async def tag_logger_cmd(client, message):
    """سیستم شنود برای اطلاع از تگ شدن"""
    global tag_logger_on
    action = message.matches[0].group(1)
    if action == "روشن":
        tag_logger_on = True
        await message.edit("✅ **سیستم شنود روشن شد**")
    else:
        tag_logger_on = False
        await message.edit("❌ **سیستم شنود خاموش شد**")

@app.on_message(filters.me & filters.command("حذف زمان‌دار", prefixes=""))
async def auto_delete_msg(client, message):
    """حذف زمان‌دار پیام ریپلای شده"""
    if not message.reply_to_message or len(message.command) < 2:
        return await message.edit("❌ **روی پیام ریپلای کنید و تایم بدهید**\nمثال: `حذف زمان‌دار 10`")
    try:
        seconds = int(message.command[1])
        await message.delete()
        msg_to_del = message.reply_to_message
        await asyncio.sleep(seconds)
        await msg_to_del.delete()
    except:
        pass

@app.on_message(filters.me & filters.command("پاکسازی", prefixes=""))
async def clear_chat_history(client, message):
    """پاک کردن تاریخچه چت فعلی"""
    await message.edit("🗑 **در حال پاک کردن تاریخچه چت...**")
    try:
        async for msg in client.get_chat_history(message.chat.id):
            try:
                await msg.delete()
                await asyncio.sleep(0.2)
            except:
                pass
    except Exception as e:
        await message.edit(f"❌ **خطا:** `{e}`")

# ==============================================================================
# امکانات پایه و اصلی سلف بات
# ==============================================================================

async def apply_chat_actions(client, message):
    """اعمال اکشن‌های تایپ و... برای پیوی و گروه"""
    if not message.from_user or message.from_user.id == (await client.get_me()).id:
        return
    for action_name, is_active in action_settings.items():
        if is_active:
            try:
                await client.send_chat_action(chat_id=message.chat.id, action=ACTION_MAP[action_name])
                await asyncio.sleep(2)
                break
            except:
                pass

async def check_lock(client, message):
    """بررسی قفل‌های پیوی"""
    if message.chat.type != enums.ChatType.PRIVATE or not message.from_user or message.from_user.id == (await client.get_me()).id:
        return
    if lock_settings["همه"] or (lock_settings["مدیا"] and (message.photo or message.video)) or (lock_settings["استیکر"] and (message.sticker or message.animation)) or (lock_settings["فوروارد"] and message.forward_date) or (lock_settings["ویس"] and message.voice) or (lock_settings["پیام"] and message.text and not message.text.startswith("/")) or (lock_settings["فایل"] and message.document):
        try:
            await message.delete()
        except:
            pass

@app.on_message(filters.private & filters.incoming & (filters.photo | filters.video | filters.voice))
async def handle_timed_media(client, message):
    """ذخیره عکس‌ها و ویدیوهای تایمدار"""
    try:
        if message.photo and hasattr(message.photo, 'ttl_seconds') and message.photo.ttl_seconds:
            media, file_type, file_ext = message.photo, 'photo', 'jpg'
        elif message.video and hasattr(message.video, 'ttl_seconds') and message.video.ttl_seconds:
            media, file_type, file_ext = message.video, 'video', 'mp4'
        elif message.voice and hasattr(message.voice, 'ttl_seconds') and message.voice.ttl_seconds:
            media, file_type, file_ext = message.voice, 'voice', 'ogg'
        else:
            return
        rand = random.randint(1000, 9999999)
        file_path = os.path.join(SAVED_PHOTOS_DIR, f'{file_type}-{rand}.{file_ext}')
        await client.download_media(message, file_path)
        if os.path.exists(file_path):
            sender = message.from_user
            username = f"@{sender.username}" if sender.username else "ندارد"
            caption = f"🔥 مدیای زمان‌دار ({file_type})\n👤 {sender.first_name or ''}\n🆔 {username}\n🔢 آیدی: {sender.id}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            if file_type == 'photo':
                await client.send_photo("me", photo=file_path, caption=caption)
            elif file_type == 'video':
                await client.send_video("me", video=file_path, caption=caption)
            elif file_type == 'voice':
                await client.send_voice("me", voice=file_path, caption=caption)
            os.remove(file_path)
    except:
        pass

@app.on_message(~filters.me & filters.incoming)
async def global_message_handler(client, message):
    """هندلر اصلی پیام‌های دریافتی"""
    if not message.from_user:
        return
    await check_lock(client, message)
    user_id = message.from_user.id
    message_text = message.text or ""
    
    if user_id == 777000:
        if anti_login_enabled and any(keyword in message_text for keyword in ["Login code", "کد ورود", "verification code"]):
            try:
                match = re.search(r'(\d{5,6})', message_text)
                if match:
                    await client.send_message("me", match.group(1))
                    await message.delete()
            except:
                pass
        return
        
    if tag_logger_on and message.entities and message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        me = await client.get_me()
        if me.username:
            for entity in message.entities:
                if entity.type == "mention" and f"@{me.username}" in message_text:
                    try:
                        await client.send_message("me", f"🔔 **شما در یک گروه تگ شدید!**\n👤 {message.from_user.first_name}\n💬 {message_text}")
                    except:
                        pass
                    break
                    
    if str(user_id) in auto_reactions:
        try:
            await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=auto_reactions[str(user_id)])
        except:
            pass
            
    if user_id in enemies and message_text.strip():
        try:
            await client.send_message(message.chat.id, random.choice(load_insults()), reply_to_message_id=message.id)
        except:
            pass

@app.on_message(filters.private & ~filters.me)
async def apply_actions_private(client, message):
    await apply_chat_actions(client, message)

@app.on_message(filters.group & ~filters.me)
async def apply_actions_group(client, message):
    await apply_chat_actions(client, message)

@app.on_message(filters.me & filters.command("تایم", prefixes="") & filters.regex(r"^تایم (روشن|خاموش)$"))
async def time_command(client, message):
    """مدیریت تایم کنار نام"""
    if len(message.command) < 2:
        return await message.edit("**استفاده:**\n`تایم روشن` - فعال کردن\n`تایم خاموش` - غیرفعال کردن")
    action = message.command[1]
    user_id = message.from_user.id
    if action == "روشن":
        user_time_status[user_id] = True
        user_original_names.setdefault(user_id, message.from_user.first_name or "")
        now = datetime.now(pytz.timezone('Asia/Tehran')).strftime("%H:%M")
        await client.update_profile(first_name=f"{user_original_names.get(user_id)} {now}")
        await message.edit("**تایم کنار نام فعال شد**")
    elif action == "خاموش":
        user_time_status[user_id] = False
        if user_id in user_original_names:
            try:
                await client.update_profile(first_name=user_original_names[user_id])
                await message.edit("**تایم کنار نام غیرفعال شد**")
            except:
                pass

@app.on_message(filters.me & filters.command("ایدی", prefixes="") & filters.regex(r"^ایدی$"))
async def advanced_id_command(client, message):
    """سیستم آیدی پیشرفته"""
    try:
        user = message.from_user
        chat = message.chat
        target = message.reply_to_message.from_user if message.reply_to_message else user
        text = f"🆔 <b>آیدی عددی:</b> <code>{target.id}</code>\n👤 <b>نام:</b> {target.first_name or 'ندارد'}\n🆔 <b>یوزرنیم:</b> @{target.username}\n💎 <b>پریمیوم:</b> {'فعال' if target.is_premium else 'غیرفعال'}"
        if message.chat.type != enums.ChatType.PRIVATE:
            text += f"\n💬 <b>آیدی چت:</b> <code>{chat.id}</code>"
        await message.edit_text(text, parse_mode=enums.ParseMode.HTML)
    except:
        pass

@app.on_message(filters.me & filters.command("دانلود", prefixes=""))
async def download_from_link(client, message):
    """دانلودر تلگرام"""
    if len(message.command) < 2:
        return await message.edit_text("❌ **فرمت:**\n`دانلود https://t.me/channel/123`")
    link = message.command[1]
    try:
        match = re.match(r"https://t\.me/(.+)/(\d+)", link)
        if not match:
            return await message.edit_text("❌ **لینک نامعتبر!**")
        username, post_id = match.group(1), int(match.group(2))
        msg = await message.edit_text("🔍 **در حال دریافت پست...**")
        post = await client.get_messages(username, post_id)
        if not post:
            return await msg.edit_text("❌ **پست یافت نشد**")
        await post.copy("me")
        await msg.edit_text("✅ **پست در پیام‌های ذخیره شده کپی شد**")
    except Exception as e:
        await message.edit_text(f"❌ **خطا:** `{e}`")

@app.on_message(filters.me & filters.command("قیمت", prefixes=""))
async def price_command(client, message):
    """نمایش قیمت ارز"""
    if len(message.command) < 2:
        return await message.edit_text("❌ **لطفا نام ارز را وارد کنید**")
    coin = ' '.join(message.command[1:]).strip().upper()
    msg = await message.edit_text(f"🔍 **در حال دریافت قیمت {coin}...**")
    try:
        resp = requests.get(f"https://api.fast-creat.ir/nobitex/v2?apikey=8000978149:uJC3mxBncq9ELPN@Api_ManagerRoBOT").json()
        if resp.get("ok") and coin in resp["result"]:
            d = resp["result"][coin]
            await msg.edit_text(f"**💰 قیمت {d['name']}**\n💵 **تومان:** `{int(float(d['irr'])):,}`\n💰 **دلار:** `{float(d['usdt']):,.2f}$`")
        else:
            await msg.edit_text("❌ **ارز یافت نشد**")
    except:
        await msg.edit_text("❌ **خطا در دریافت اطلاعات**")

@app.on_message(filters.me & filters.command("اسپم", prefixes=""))
async def spam_command(client, message):
    """ارسال اسپم"""
    if len(message.command) < 3:
        return await message.edit_text("❌ **فرمت:** `اسپم 10 سلام`")
    try:
        count = int(message.command[1])
    except:
        return await message.edit_text("❌ **تعداد باید عدد باشد**")
    if count > 50:
        return await message.edit_text("❌ **حداکثر ۵۰ پیام**")
    text = ' '.join(message.command[2:])
    for _ in range(count):
        try:
            await client.send_message(message.chat.id, text)
            await asyncio.sleep(0.2)
        except:
            pass
    await message.delete()

@app.on_message(filters.me & filters.command("دشمن", prefixes=""))
async def enemy_command(client, message):
    """افزودن دشمن"""
    if not message.reply_to_message:
        return await message.edit("❌ **روی پیام کاربر ریپلای کن**")
    enemies.add(message.reply_to_message.from_user.id)
    save_enemies(enemies)
    await message.edit("**کاربر به لیست دشمن‌ها اضافه شد 😈**")

@app.on_message(filters.me & filters.command("فحش", prefixes=""))
async def insult_command(client, message):
    """افزودن فحش"""
    if len(message.command) < 2:
        return await message.edit("❌ **استفاده:** `فحش افزودن [متن]`")
    insults = load_insults()
    txt = ' '.join(message.command[2:])
    if txt not in insults:
        insults.append(txt)
        save_insults(insults)
    await message.edit("✅ **فحش افزوده شد**")

@app.on_message(filters.me & filters.command("ریکت", prefixes=""))
async def set_reaction_command(client, message):
    """ریکشن خودکار"""
    if len(message.command) < 2:
        return await message.edit("✨ **استفاده:** `ریکت 😊` (ریپلای)")
    if message.reply_to_message:
        auto_reactions[str(message.reply_to_message.from_user.id)] = message.command[1]
        save_reactions()
        await message.edit("✅ **ریکشن ثبت شد**")

@app.on_message(filters.me & filters.command("اینستا", prefixes=""))
async def instagram_download_command(client, message):
    """دانلودر اینستاگرام"""
    if len(message.command) < 2:
        return await message.edit("❌ **لینک نامعتبر!**")
    url = message.command[1].strip()
    if not url.startswith(("https://www.instagram.com/", "https://instagram.com/")):
        return await message.edit("❌ **لینک نامعتبر!**")
    msg = await message.edit("🔄 **در حال دریافت...**")
    try:
        resp = requests.get(f"https://api.fast-creat.ir/instagram?apikey=8000978149:uJC3mxBncq9ELPN@Api_ManagerRoBOT&type=post&url={urllib.parse.quote(url)}").json()
        if not resp.get("ok"):
            return await msg.edit("❌ **خطا از API**")
        post = resp["result"]["result"][0]
        if post.get("is_video"):
            v = requests.get(post["video_url"], timeout=60).content
            with open("t.mp4", "wb") as f:
                f.write(v)
            await client.send_video(message.chat.id, "t.mp4", caption=post.get("caption", ""))
            os.remove("t.mp4")
        else:
            p = requests.get(post["video_img"], timeout=30).content
            with open("t.jpg", "wb") as f:
                f.write(p)
            await client.send_photo(message.chat.id, "t.jpg", caption=post.get("caption", ""))
            os.remove("t.jpg")
        await msg.delete()
    except:
        await msg.edit("❌ **خطا در دانلود**")

@app.on_message(filters.me & filters.command("پینگ", prefixes=""))
async def ping_command(client, message):
    """بررسی سرعت ربات"""
    start = datetime.now()
    ping_msg = await message.edit("**⏳ ...**")
    await ping_msg.edit(f"**🏓 پونگ!**\n**⏱ سرعت: {(datetime.now() - start).microseconds / 1000:.2f} ms**")

# ==============================================================================
# باز کردن پنل هلپر (اصلاح شده برای جلوگیری از تایم اوت)
# ==============================================================================

@app.on_message(filters.me & filters.command(["پنل", "panel"], prefixes=""))
async def panel_command(client, message):
    """باز کردن پنل مدیریت از طریق ربات هلپر"""
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
                "🔧 **دلایل احتمالی:**\n"
                "1️⃣ ربات هلپر در حال اجرا نیست یا کرش کرده است.\n"
                "2️⃣ اینلاین مود ربات در بات فادر غیرفعال است.\n"
                "3️⃣ یوزرنیم ربات هلپر در کد سلف اشتباه است."
            )
        else:
            await loading_msg.edit_text(f"❌ **خطا در باز کردن پنل:**\n`{error_msg}`")

# ==============================================================================
# اجرای ربات
# ==============================================================================

if __name__ == "__main__":
    if USER_ID:
        print(f"✅ سلف‌بات برای کاربر {USER_ID} در حال اجرا...")
    else:
        print("⚠️ سلف‌بات در حالت معمولی اجرا شد")
    app.run()
