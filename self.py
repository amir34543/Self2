# ==============================================================================
#  PersianGulf SelfBot — نسخه 7.0.0 «شاهکار»
#  پنل دوطبقه + بیش از ۴۰ قابلیت جدید
# ==============================================================================

import requests
import urllib.parse
from pyrogram import Client, filters, StopPropagation
from pyrogram.types import (Message, ReplyKeyboardMarkup, KeyboardButton,
                            ReplyKeyboardRemove, ChatPermissions)
import os, asyncio, random, re, json, sys, time
from datetime import datetime
import pytz
from pyrogram import enums
from pyrogram.raw import functions as rawfn
from pyrogram.errors import FloodWait

bot_username = "Helperbotpersian_bot"  # یوزرنیم ربات هلپر بدون @

USER_ID = None
PHONE = None
API_ID = 35656061
API_HASH = "b37f2596516bc0439bf505d1d230395c"

if len(sys.argv) > 1: USER_ID = int(sys.argv[1])
if len(sys.argv) > 2: PHONE = sys.argv[2]
if len(sys.argv) > 3: API_ID = int(sys.argv[3])
if len(sys.argv) > 4: API_HASH = sys.argv[4]

session_name = f"sessions/{USER_ID}" if USER_ID else "self"
app = Client(session_name, api_id=API_ID, api_hash=API_HASH)

# --- کش get_me: هر get_me یک درخواست users.GetFullUser است و فراخوانی مکرر FLOOD_WAIT می‌دهد ---
_orig_get_me = app.get_me
_me_cache = {"me": None, "ts": 0.0}
ME_CACHE_TTL = 90

async def _cached_get_me(*args, **kwargs):
    now = time.time()
    if _me_cache["me"] is None or now - _me_cache["ts"] > ME_CACHE_TTL:
        try:
            _me_cache["me"] = await _orig_get_me()
            _me_cache["ts"] = now
        except FloodWait as e:
            if _me_cache["me"] is None:
                await asyncio.sleep(e.value + 1)
                _me_cache["me"] = await _orig_get_me()
                _me_cache["ts"] = time.time()
            else:
                _me_cache["ts"] = now + e.value   # تا پایان فلود از کش استفاده کن
    return _me_cache["me"]

app.get_me = _cached_get_me

# ================== فایل‌ها و پوشه‌ها ==================
SAVED_PHOTOS_DIR = "saved_photos"
INSULTS_FILE = "insults.txt"
ENEMIES_FILE = "enemies.txt"
BACKUPS_DIR = "backups"
NOTES_FILE = "notes.json"
os.makedirs(SAVED_PHOTOS_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)

def jload(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                c = f.read().strip()
                return json.loads(c) if c else default
    except Exception:
        pass
    return default

def jsave(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return True
    except Exception:
        return False

# ================== وضعیت‌ها ==================
action_settings = {"typing": False, "upload_photo": False, "record_audio": False, "upload_video": False,
                   "upload_document": False, "record_video": False, "upload_audio": False, "playing": False,
                   "choose_contact": False, "find_location": False, "choose_sticker": False}
ACTION_MAP = {"typing": enums.ChatAction.TYPING, "upload_photo": enums.ChatAction.UPLOAD_PHOTO,
              "record_audio": enums.ChatAction.RECORD_AUDIO, "upload_video": enums.ChatAction.UPLOAD_VIDEO,
              "upload_document": enums.ChatAction.UPLOAD_DOCUMENT, "record_video": enums.ChatAction.RECORD_VIDEO,
              "upload_audio": enums.ChatAction.UPLOAD_AUDIO, "playing": enums.ChatAction.PLAYING,
              "choose_contact": enums.ChatAction.CHOOSE_CONTACT, "find_location": enums.ChatAction.FIND_LOCATION,
              "choose_sticker": enums.ChatAction.CHOOSE_STICKER}

format_settings = {"بولد": False, "ایتالیک": False, "زیر خط": False, "خط‌ خورده": False, "اسپویلر": False, "کد": False}
html_tags = {"بولد": "<b>{}</b>", "ایتالیک": "<i>{}</i>", "زیر خط": "<u>{}</u>",
             "خط‌ خورده": "<s>{}</s>", "اسپویلر": "<spoiler>{}</spoiler>", "کد": "<code>{}</code>"}
lock_settings = {"همه": False, "مدیا": False, "استیکر": False, "فوروارد": False, "ویس": False, "پیام": False, "فایل": False}

user_menu_mode = {}
always_online_enabled = False
tag_logger_on = False
anti_login_enabled = False
afk_mode = False
afk_reason = ""
afk_notified = set()
signature_on = False
signature_text = "• 『 پیام من 』"
auto_delete_seconds = 0
banner_active = None
banner_interval_min = 5
last_banner = 0
START_TIME = time.time()

user_time_status = {}
user_original_names = {}
user_fonts = {int(k): v for k, v in jload("fonts.json", {}).items()}
auto_reactions = jload("mmauto_reactions.json", {})
auto_replies = jload("auto_replies.json", {})
notes = jload(NOTES_FILE, {})
banners = jload("banners.json", {})

def load_insults():
    try:
        if os.path.exists(INSULTS_FILE):
            with open(INSULTS_FILE, "r", encoding="utf-8") as f:
                return [l.strip() for l in f.readlines() if l.strip()]
    except Exception:
        pass
    return []

def save_insults(lst):
    try:
        with open(INSULTS_FILE, "w", encoding="utf-8") as f:
            for i in lst: f.write(i + "\n")
        return True
    except Exception:
        return False

def load_enemies():
    try:
        if os.path.exists(ENEMIES_FILE):
            with open(ENEMIES_FILE, "r", encoding="utf-8") as f:
                return set(int(l.strip()) for l in f.readlines() if l.strip())
    except Exception:
        pass
    return set()

def save_enemies(es):
    try:
        with open(ENEMIES_FILE, "w", encoding="utf-8") as f:
            for e in es: f.write(str(e) + "\n")
        return True
    except Exception:
        return False

enemies = load_enemies()

FULL_PERMS = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True,
                             can_send_other_messages=True, can_add_web_page_previews=True,
                             can_change_info=True, can_invite_users=True, can_pin_messages=True)
NO_PERMS = ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_polls=False,
                           can_send_other_messages=False, can_add_web_page_previews=False)

# ================== فونت زمان / فانتزی / جک ==================
TIME_FONTS = {1: "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗", 2: "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟯", 3: "０１２３４５６７８９",
              4: "𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫", 5: "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡", 6: "dashed"}

def fa_time_str(fid=1):
    t = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M")
    if fid == 6:
        return "".join(ch + "\u0334" for ch in t)
    digits = TIME_FONTS.get(fid, TIME_FONTS[1])
    return t.translate(str.maketrans("0123456789", digits))

def _alpha(lo, up):
    return str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", lo + up)

FANCY_TRANS = {
    1: _alpha("𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇", "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"),
    2: _alpha("𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻", "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡"),
    3: _alpha("𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫", "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"),
    4: _alpha("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"),
    5: _alpha("ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ", "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ"),
    6: _alpha("𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟", "𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅"),
}
WRAPPERS = {1: ("꧁ ", " ꧂"), 2: ("✦ ", " ✦"), 3: ("༺ ", " ༻"), 4: ("「 ", " 」"), 5: ("★ ", " ★"), 6: ("『 ", " 』")}

JOKES = [
    "به یارو میگن چرا شب‌ها در اتاقت رو قفل می‌کنی؟ میگه تا صبح کسی خوابش نپره! 😂",
    "معلم: یک جمله بگو که توش «خواب» باشد. دانش‌آموز: دیروز ۴۰ نفر در کلاس خواب دیدند! 😴",
    "یارو به دکتر میگه هر جا میرم بقیه از من کپی میبرند! دکتر: خب عکس بنداز جلو نری 😂",
    "گفتند چرا گوشیت رو تو یخچال میذاری؟ گفت اس‌ام‌اس‌ها سرد بشه بهتره! 🥶",
    "به یارو گفتن چرا پشت چراغ قرمز بوق زدی؟ گفت داشتم برف‌پاک‌کن‌ها رو پارک می‌کردم! 🚗",
    "یه بار یارو تو آزمایشگاه آب را به خودش زد، از آن به بعد شد ابرمرد... نه اشتباه کردم، شد مرطوب! 💧",
]

CMD_STARTERS = ("بایو", "یوزر", "نام", "ترجمه", "آب", "بارکد", "دانلود", "قیمت", "اسپم", "فحش", "دشمن",
                "ریکت", "اینستا", "پینگ", "پاسخ", "افک", "همگانی", "حذف", "سیو", "یادداشت", "ویس", "حساب",
                "آمار", "سشن", "خروج", "بلاک", "آنبلاک", "ساخت", "پین", "آنپین", "کیک", "بن", "آنبن",
                "افزودن", "سکوت", "رفع", "مخاطب", "شماره", "تاس", "ریسه", "جک", "شانس", "قلم", "ویوئر",
                "فضول", "سلامت", "ویرایش", "تنظیم", "لیست", "فرمت", "انتی", "آنلاین", "شنود", "تایم",
                "پاکسازی", "منوی", "بنر", "زمان", "وضعیت", "ریست", "قفل", "بازکردن", "پروفایل", "عکس",
                "پنل", "panel", "منش", "امضا")

# ==============================================================================
# ★ هندلر پنل (اول از همه تا با بقیه تداخل نکند) ★
# ==============================================================================
@app.on_message(filters.me & filters.command(["پنل", "panel"], prefixes=""))
async def panel_command(client, message):
    loading_msg = await message.edit_text("⏳ **در حال باز کردن پنل Persian Gulf Self...**")
    try:
        results = await client.get_inline_bot_results(bot_username, "panel")
        if results and results.results:
            await client.send_inline_bot_result(chat_id=message.chat.id,
                                                query_id=results.query_id,
                                                result_id=results.results[0].id)
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("❌ **پنل یافت نشد**\nربات هلپر روشن است اما پاسخی نداد.")
    except Exception as e:
        err = str(e)
        if "BOT_RESPONSE_TIMEOUT" in err or "Timeout" in err:
            await loading_msg.edit_text("❌ **هلپر پاسخ نداد (Timeout)**\n\n1️⃣ helper.py روشن نیست\n2️⃣ `/setinline` در BotFather تنظیم نشده\n3️⃣ یوزرنیم هلپر در self.py اشتباه است")
        else:
            await loading_msg.edit_text(f"❌ **خطا:**\n`{err}`")
    raise StopPropagation

# ================== منوهای شیشه‌ای ==================
def get_format_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("✅ بولد" if format_settings["بولد"] else "بولد"),
         KeyboardButton("✅ ایتالیک" if format_settings["ایتالیک"] else "ایتالیک"),
         KeyboardButton("✅ زیر خط" if format_settings["زیر خط"] else "زیر خط")],
        [KeyboardButton("✅ خط‌ خورده" if format_settings["خط‌ خورده"] else "خط‌ خورده"),
         KeyboardButton("✅ اسپویلر" if format_settings["اسپویلر"] else "اسپویلر"),
         KeyboardButton("✅ کد" if format_settings["کد"] else "کد")],
        [KeyboardButton("🟢 معمولی (ریست)"), KeyboardButton("❌ بستن منو")]
    ], resize_keyboard=True)

def get_action_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("✅ تایپ" if action_settings["typing"] else "تایپ"),
         KeyboardButton("✅ آپلود عکس" if action_settings["upload_photo"] else "آپلود عکس")],
        [KeyboardButton("✅ ضبط ویس" if action_settings["record_audio"] else "ضبط ویس"),
         KeyboardButton("✅ بازی" if action_settings["playing"] else "بازی")],
        [KeyboardButton("🔴 خاموش (ریست)"), KeyboardButton("❌ بستن منو")]
    ], resize_keyboard=True)

def get_quick_settings_keyboard():
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
    await message.reply_text("⚙️ **منوی تنظیمات سریع فعال شد**", reply_markup=get_quick_settings_keyboard())
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
        await client.send_message(user_id, "🔄 تنظیمات آپدیت شد", reply_markup=get_quick_settings_keyboard())
        await message.delete()
        raise StopPropagation

# ================== فرمت خودکار + امضا (پیام‌های خروجی) ==================
async def _is_command_message(client, message):
    """True اگر پیام یکی از دستورهای سلف‌بات (هندلرهای گروه ۰) باشد"""
    try:
        handlers = client.dispatcher.groups.get(0, [])
        if handlers:
            for h in handlers:
                try:
                    if await h.check(client, message):
                        return True
                except Exception:
                    continue
            return False
    except Exception:
        pass
    # حالت پشتیبان اگر دسترسی به هندلرها ممکن نبود
    return (message.text or "").startswith(CMD_STARTERS)

@app.on_message(filters.me & filters.text, group=1)
async def outgoing_text_handler(client, message):
    text = message.text or ""
    if not text or await _is_command_message(client, message):
        return
    active = [k for k, on in format_settings.items() if on]
    want_sig = signature_on and not text.endswith(signature_text)
    if not active and not want_sig:
        return
    try:
        body = message.text.html if hasattr(message.text, "html") else text
    except Exception:
        body = text
    if active:
        for fmt in active:
            body = html_tags.get(fmt, "{}").format(body)
    if want_sig:
        body += "\n\n" + signature_text
    try:
        await message.edit(body, parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass

@app.on_message(filters.me & ~filters.service, group=2)
async def auto_delete_own_handler(client, message):
    if auto_delete_seconds > 0:
        async def _later():
            await asyncio.sleep(auto_delete_seconds)
            try: await message.delete()
            except Exception: pass
        asyncio.create_task(_later())

# ================== 🪄 پروفایل ==================
@app.on_message(filters.me & filters.regex(r"^پروفایل$"))
async def set_pfp(client, message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.edit("❌ روی عکس ریپلای کنید")
    msg = await message.edit("🖼 در حال تغییر...")
    try:
        p = await message.reply_to_message.download()
        await client.set_profile_photo(photo=p); os.remove(p)
        await msg.edit("✅ عکس پروفایل تغییر کرد")
    except Exception as e:
        await msg.edit(f"❌ خطا: `{e}`")

@app.on_message(filters.me & filters.regex(r"^حذف عکس$"))
async def del_last_photo(client, message):
    m = await message.edit("🗑 در حال حذف...")
    try:
        photos = await app.get_profile_photos("me", limit=1)
        if photos:
            await app.delete_profile_photos([photos[0].file_id])
            await m.edit("✅ آخرین عکس پروفایل حذف شد")
        else:
            await m.edit("❌ عکسی موجود نیست")
    except Exception as e:
        await m.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.regex(r"^حذف همه عکس$"))
async def del_all_photos(client, message):
    m = await message.edit("🗑 در حال حذف همه عکس‌ها...")
    try:
        photos = await app.get_profile_photos("me", limit=100)
        ids = [p.file_id for p in photos]
        for i in range(0, len(ids), 90):
            await app.delete_profile_photos(ids[i:i+90])
        await m.edit(f"✅ {len(ids)} عکس حذف شد")
    except Exception as e:
        await m.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command("بایو", prefixes=""))
async def set_bio(client, message):
    if len(message.command) < 2: return await message.edit("❌ `بایو متن`")
    try:
        await app.update_profile(bio=' '.join(message.command[1:]))
        await message.edit("✅ بیو تغییر کرد")
    except Exception as e: await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command("یوزر", prefixes=""))
async def set_username(client, message):
    if len(message.command) < 2: return await message.edit("❌ `یوزر name`")
    try:
        await app.set_username(message.command[1].lstrip('@'))
        await message.edit("✅ یوزر تغییر کرد")
    except Exception as e: await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command("نام", prefixes=""))
async def set_name(client, message):
    if len(message.command) < 2: return await message.edit("❌ `نام جدید` یا `نام کامل نام فامیلی`")
    txt = message.text
    try:
        if txt.startswith("نام کامل "):
            parts = txt[9:].strip().split(" ", 1)
            await app.update_profile(first_name=parts[0], last_name=parts[1] if len(parts) > 1 else "")
        else:
            await app.update_profile(first_name=' '.join(message.command[1:]))
        await message.edit("✅ نام تغییر کرد")
    except Exception as e: await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command("تایم", prefixes="") & filters.regex(r"^تایم (روشن|خاموش)$"))
async def time_command(client, message):
    global user_fonts
    a = message.command[1]
    uid = message.from_user.id
    if a == "روشن":
        user_time_status[uid] = True
        user_original_names.setdefault(uid, message.from_user.first_name or "")
        fid = user_fonts.get(uid, 1)
        await app.update_profile(first_name=f"{user_original_names.get(uid)} {fa_time_str(fid)}")
        await message.edit(f"✅ تایم روشن شد\n⏰ {fa_time_str(fid)}")
    else:
        user_time_status[uid] = False
        if uid in user_original_names:
            try: await app.update_profile(first_name=user_original_names[uid])
            except Exception: pass
        await message.edit("✅ تایم خاموش شد")

@app.on_message(filters.me & filters.regex(r"^(لیست فونت|تنظیم فونت \d)$"))
async def font_cmd(client, message):
    global user_fonts
    t = message.text
    if t == "لیست فونت":
        preview = "\n".join(f"{i} - «{fa_time_str(i)}»" for i in TIME_FONTS)
        await message.edit(f"🔤 **فونت‌های زمان:**\n\n{preview}\n\n✅ با `تنظیم فونت شماره` انتخاب کنید")
    else:
        fid = int(t.split()[-1])
        if fid in TIME_FONTS:
            user_fonts[message.from_user.id] = fid
            jsave("fonts.json", user_fonts)
            await message.edit(f"✅ فونت {fid} تنظیم شد\n⏰ پیش‌نمایش: {fa_time_str(fid)}")

# ================== 👥 گروه ==================
@app.on_message(filters.me & filters.regex(r"^ساخت گروه .+"))
async def create_group_cmd(client, message):
    title = message.text.split(" ", 2)[2]
    m = await message.edit("👥 در حال ساخت گروه...")
    try:
        await app.create_group(title, [])
        await m.edit(f"✅ گروه «{title}» ساخته شد")
    except Exception as e:
        await m.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.regex(r"^(قفل گروه|بازکردن گروه)$"))
async def group_lock_cmd(client, message):
    try:
        closed = message.text == "قفل گروه"
        await app.set_chat_permissions(message.chat.id, NO_PERMS if closed else FULL_PERMS)
        await message.edit("🔒 گروه قفل شد" if closed else "🔓 گروه باز شد")
    except Exception as e:
        await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.regex(r"^(پین|آنپین)$"))
async def pin_cmd(client, message):
    try:
        if message.text == "پین":
            if not message.reply_to_message: return await message.edit("❌ ریپلای کنید")
            await message.reply_to_message.pin()
            await message.edit("📌 پیام پین شد")
        else:
            await app.unpin_chat_message(message.chat.id)
            await message.edit("📌 پین آخر برداشته شد")
    except Exception as e:
        await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.regex(r"^(کیک|بن|آنبن)$"))
async def kick_ban_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.edit("❌ روی پیام کاربر ریپلای کنید")
    uid = message.reply_to_message.from_user.id
    try:
        if message.text == "کیک":
            await app.ban_chat_member(message.chat.id, uid)
            await app.unban_chat_member(message.chat.id, uid)
            await message.edit("👢 کاربر اخراج شد")
        elif message.text == "بن":
            await app.ban_chat_member(message.chat.id, uid)
            await message.edit("🔨 کاربر بن شد")
        else:
            await app.unban_chat_member(message.chat.id, uid)
            await message.edit("✅ کاربر آنبن شد")
    except Exception as e:
        await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.regex(r"^تعداد (کانال ها|گروه ها)$"))
async def count_chats_cmd(client, message):
    chans = groups = 0
    async for d in app.get_dialogs(limit=500):
        t = d.chat.type
        if t == enums.ChatType.CHANNEL: chans += 1
        elif t in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP): groups += 1
    k = message.matches[0].group(1)
    await message.edit(f"📊 **تعداد {k}:** {chans if 'کانال' in k else groups}")

@app.on_message(filters.me & filters.regex(r"^خروج همه (کانال|گروه)$"))
async def leave_all_cmd(client, message):
    kind = message.matches[0].group(1)
    m = await message.edit(f"🚪 در حال خروج از همه {kind}‌ها...")
    n = 0
    async for d in app.get_dialogs(limit=500):
        t = d.chat.type
        ok = (t == enums.ChatType.CHANNEL and kind == "کانال") or (t in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP) and kind == "گروه")
        if ok:
            try:
                await app.leave_chat(d.chat.id); n += 1; await asyncio.sleep(4)
            except Exception: pass
    await m.edit(f"✅ از {n} {kind} خارج شدید")

# ================== 🤝 دعوت و مخاطب ==================
@app.on_message(filters.me & filters.command("افزودن", prefixes=""))
async def add_member_cmd(client, message):
    if len(message.command) < 2: return await message.edit("❌ `افزودن @user`")
    try:
        await app.add_chat_members(message.chat.id, message.command[1].lstrip("@"))
        await message.edit("✅ عضو به گروه اضافه شد")
    except Exception as e:
        await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command("مخاطب", prefixes="") & filters.regex(r"^مخاطب \+?\d+ .+"))
async def contact_cmd(client, message):
    parts = message.text.split(" ", 2)
    await message.delete()
    await app.send_contact(message.chat.id, parts[1].lstrip("+"), parts[2])

@app.on_message(filters.me & filters.regex(r"^شماره من$"))
async def my_contact_cmd(client, message):
    me = await app.get_me()
    if not me.phone_number: return await message.edit("❌ شماره شما مخفی است")
    await message.delete()
    await app.send_contact(message.chat.id, me.phone_number, me.first_name or "من")

# ================== 🔇 سکوت و بلاک ==================
@app.on_message(filters.me & filters.regex(r"^(سکوت|رفع سکوت)$"))
async def mute_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.edit("❌ روی پیام کاربر ریپلای کنید")
    uid = message.reply_to_message.from_user.id
    try:
        if message.text == "سکوت":
            await app.restrict_chat_member(message.chat.id, uid, NO_PERMS)
            await message.edit("🔇 کاربر ساکت شد")
        else:
            await app.restrict_chat_member(message.chat.id, uid, FULL_PERMS)
            await message.edit("🔊 سکوت برداشته شد")
    except Exception as e:
        await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command(["بلاک", "آنبلاک"], prefixes=""))
async def block_cmd(client, message):
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        target = message.command[1].lstrip("@")
    if not target: return await message.edit("❌ ریپلای کنید یا `بلاک @user`")
    try:
        if message.command[0] == "بلاک":
            await app.block_user(target); await message.edit("🚫 کاربر بلاک شد")
        else:
            await app.unblock_user(target); await message.edit("✅ کاربر آنبلاک شد")
    except Exception as e:
        await message.edit(f"❌ `{e}`")

# ================== 😏 منش و AFK ==================
@app.on_message(filters.me & filters.regex(r"^افک (روشن|خاموش)( .+)?$"))
async def afk_cmd(client, message):
    global afk_mode, afk_reason, afk_notified
    if message.matches[0].group(1) == "روشن":
        afk_mode = True
        afk_reason = (message.matches[0].group(2) or "").strip()
        afk_notified = set()
        await message.edit("💤 **حالت AFK روشن شد**" + (f"\n📌 دلیل: {afk_reason}" if afk_reason else ""))
    else:
        afk_mode = False; afk_reason = ""
        await message.edit("✅ حالت AFK خاموش شد — خوش برگشتی!")

@app.on_message(filters.me & filters.regex(r"^(منش روشن|منش خاموش)$"))
async def sig_toggle_cmd(client, message):
    global signature_on
    signature_on = message.text == "منش روشن"
    await message.edit(f"✍️ امضای خودکار {'روشن' if signature_on else 'خاموش'} شد")

@app.on_message(filters.me & filters.regex(r"^امضا .+"))
async def sig_set_cmd(client, message):
    global signature_text, signature_on
    signature_text = message.text[5:].strip()
    signature_on = True
    await message.edit(f"✅ امضا تنظیم شد:\n{signature_text}")

@app.on_message(filters.me & filters.command("ریکت", prefixes=""))
async def set_reaction_cmd(client, message):
    if len(message.command) < 2: return await message.edit("❌ `ریکت 😊` (با ریپلای)")
    if message.reply_to_message:
        auto_reactions[str(message.reply_to_message.from_user.id)] = message.command[1]
        jsave("mmauto_reactions.json", auto_reactions)
        await message.edit(f"✅ ریکشن {message.command[1]} ثبت شد")

@app.on_message(filters.me & filters.regex(r"^(حذف ریکت)$"))
async def del_reaction_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.edit("❌ ریپلای کنید")
    uid = str(message.reply_to_message.from_user.id)
    if uid in auto_reactions:
        del auto_reactions[uid]; jsave("mmauto_reactions.json", auto_reactions)
        await message.edit("🗑 ریکشن کاربر حذف شد")
    else:
        await message.edit("❌ ریکشتی برای این کاربر نیست")

@app.on_message(filters.me & filters.regex(r"^(لیست ریکت|پاکسازی ریکت)$"))
async def list_reaction_cmd(client, message):
    if message.text == "پاکسازی ریکت":
        auto_reactions.clear(); jsave("mmauto_reactions.json", auto_reactions)
        return await message.edit("🧹 همه ریکشن‌ها پاک شد")
    if auto_reactions:
        lines = []
        for uid, emo in auto_reactions.items():
            try:
                u = await app.get_users(int(uid))
                lines.append(f"• {u.first_name} → {emo}")
            except Exception:
                lines.append(f"• `{uid}` → {emo}")
        await message.edit("🎭 **ریکشن‌های خودکار:**\n" + "\n".join(lines))
    else:
        await message.edit("لیست ریکشن خالی است")

# ================== 🗑 پاک‌سازی خودکار ==================
@app.on_message(filters.me & filters.regex(r"^حذف خودکار (روشن|خاموش)( \d+)?$"))
async def autodel_cmd(client, message):
    global auto_delete_seconds
    if message.matches[0].group(1) == "روشن":
        auto_delete_seconds = int((message.matches[0].group(2) or "30").strip())
        await message.edit(f"🗑 **حذف خودکار روشن شد**\nپیام‌های شما بعد از {auto_delete_seconds} ثانیه حذف می‌شوند")
    else:
        auto_delete_seconds = 0
        await message.edit("✅ حذف خودکار خاموش شد")

@app.on_message(filters.me & filters.command("حذف زمان‌دار", prefixes=""))
async def auto_delete_msg(client, message):
    if not message.reply_to_message or len(message.command) < 2:
        return await message.edit("❌ ریپلای کنید و ثانیه بنویسید")
    try:
        s = int(message.command[1])
        await message.delete()
        m = message.reply_to_message
        await asyncio.sleep(s)
        await m.delete()
    except Exception:
        pass

# ================== 🚀 سندر و بنر ==================
@app.on_message(filters.me & filters.command("همگانی", prefixes="") & filters.regex(r"^همگانی (گروه|پیوی|کانال|همه) .+"))
async def broadcast_cmd(client, message):
    kind = message.matches[0].group(1)
    text = message.text.split(" ", 2)[2]
    m = await message.edit(f"🚀 **سندر {kind} شروع شد...**")
    sent = failed = 0
    async for d in app.get_dialogs(limit=300):
        t = d.chat.type
        ok = ((kind in ("گروه", "همه") and t in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP)) or
              (kind in ("پیوی", "همه") and t == enums.ChatType.PRIVATE) or
              (kind in ("کانال", "همه") and t == enums.ChatType.CHANNEL))
        if ok:
            try:
                await app.send_message(d.chat.id, text); sent += 1
                await asyncio.sleep(2)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                failed += 1
    await m.edit(f"✅ **سندر تمام شد**\n📤 ارسال‌شده: {sent}\n❌ ناموفق: {failed}")

@app.on_message(filters.me & filters.regex(r"^تنظیم بنر$"))
async def set_banner_cmd(client, message):
    if not message.reply_to_message:
        return await message.edit("❌ روی پیام بنر ریپلای کنید")
    code = str(len(banners) + 1)
    banners[code] = message.reply_to_message.text or message.reply_to_message.caption or ""
    jsave("banners.json", banners)
    await message.edit(f"✅ بنر با کد **{code}** ثبت شد")

@app.on_message(filters.me & filters.regex(r"^(لیست بنرها|بنر همگانی خاموش|زمان بنر \d+|بنر ارسال \d+|بنر همگانی \d+)$"))
async def banner_cmds(client, message):
    global banner_active, banner_interval_min, last_banner
    t = message.text
    if t == "لیست بنرها":
        if banners:
            await message.edit("📢 **بنرها:**\n" + "\n".join(f"• کد {k}: {v[:40]}..." for k, v in banners.items()))
        else:
            await message.edit("بنری ثبت نشده — با `تنظیم بنر` (ریپلای) ثبت کنید")
    elif t == "بنر همگانی خاموش":
        banner_active = None
        await message.edit("🛑 بنر همگانی خاموش شد")
    elif t.startswith("زمان بنر"):
        banner_interval_min = int(t.split()[-1])
        await message.edit(f"⏰ فاصله ارسال بنر: {banner_interval_min} دقیقه")
    elif t.startswith("بنر ارسال"):
        code = t.split()[-1]
        if code not in banners: return await message.edit("❌ کد بنر یافت نشد")
        m = await message.edit("📤 در حال ارسال فوری...")
        n = 0
        async for d in app.get_dialogs(limit=200):
            if d.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
                try:
                    await app.send_message(d.chat.id, banners[code]); n += 1; await asyncio.sleep(4)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception: pass
        await m.edit(f"✅ بنر به {n} گروه ارسال شد")
    elif t.startswith("بنر همگانی"):
        code = t.split()[-1]
        if code not in banners: return await message.edit("❌ کد بنر یافت نشد")
        banner_active = code
        last_banner = 0
        await message.edit(f"📢 بنر همگانی {code} روشن شد (هر {banner_interval_min} دقیقه)")

# ================== 🧹 تمیز ==================
@app.on_message(filters.me & filters.regex(r"^پاکسازی$"))
async def clear_chat_history(client, message):
    await message.edit("🗑 پاکسازی...")
    try:
        async for m in client.get_chat_history(message.chat.id):
            try:
                await m.delete(); await asyncio.sleep(0.2)
            except Exception: pass
    except Exception: pass

@app.on_message(filters.me & filters.regex(r"^حذف پیام \d+$"))
async def del_my_msgs_cmd(client, message):
    n = int(message.text.split()[-1])
    m = await message.edit(f"🗑 در حال حذف {n} پیام...")
    count = 0
    async for msg in app.get_chat_history(message.chat.id, limit=200):
        if count >= n: break
        if msg.from_user and msg.from_user.is_self:
            try:
                await msg.delete(); count += 1; await asyncio.sleep(0.3)
            except Exception: pass
    await m.edit(f"✅ {count} پیام شما حذف شد")

# ================== 📨 اسپم ==================
@app.on_message(filters.me & filters.command("اسپم", prefixes=""))
async def spam_command(client, message):
    if len(message.command) < 3: return await message.edit("❌ `اسپم 10 متن`")
    try: n = int(message.command[1])
    except Exception: return await message.edit("❌ عدد وارد کنید")
    if n > 50: return await message.edit("❌ حداکثر ۵۰")
    t = ' '.join(message.command[2:])
    for _ in range(n):
        try:
            await app.send_message(message.chat.id, t); await asyncio.sleep(0.2)
        except Exception: pass
    await message.delete()

# ================== 💭 پاسخ خودکار ==================
@app.on_message(filters.me & filters.command("پاسخ", prefixes=""))
async def auto_reply_cmd(client, message):
    t = message.text.strip()
    if t.startswith("پاسخ افزودن ") and "|" in t:
        pair = t.replace("پاسخ افزودن ", "", 1)
        k, v = pair.split("|", 1)
        auto_replies[k.strip()] = v.strip()
        jsave("auto_replies.json", auto_replies)
        await message.edit(f"✅ پاسخ «{k.strip()}» ثبت شد")
    elif t.startswith("پاسخ حذف "):
        k = t.replace("پاسخ حذف ", "", 1).strip()
        if k in auto_replies:
            del auto_replies[k]; jsave("auto_replies.json", auto_replies)
            await message.edit("🗑 پاسخ حذف شد")
        else:
            await message.edit("❌ یافت نشد")
    elif t == "پاسخ لیست":
        if auto_replies:
            await message.edit("💭 **پاسخ‌های خودکار:**\n" + "\n".join(f"• `{k}` → {v}" for k, v in auto_replies.items()))
        else:
            await message.edit("لیست پاسخ‌ها خالی است")
    else:
        await message.edit("❌ `پاسخ افزودن کلمه|پاسخ` | `پاسخ حذف کلمه` | `پاسخ لیست`")

# ================== 🛠 ابزار ==================
@app.on_message(filters.me & filters.command("ایدی", prefixes="") & filters.regex(r"^ایدی$"))
async def advanced_id_command(client, message):
    try:
        u = message.from_user; c = message.chat
        tg = message.reply_to_message.from_user if (message.reply_to_message and message.reply_to_message.from_user) else u
        t = (f"🆔 <b>آیدی:</b> <code>{tg.id}</code>\n👤 <b>نام:</b> {tg.first_name or 'ندارد'}\n"
             f"🔗 <b>یوزر:</b> @{tg.username or 'ندارد'}\n💎 <b>پریمیوم:</b> {'فعال' if tg.is_premium else 'غیرفعال'}")
        if c.type != enums.ChatType.PRIVATE:
            t += f"\n💬 <b>چت:</b> <code>{c.id}</code> | {c.title or ''}"
        await message.edit_text(t, parse_mode=enums.ParseMode.HTML)
    except Exception: pass

@app.on_message(filters.me & filters.command("ترجمه", prefixes=""))
async def translate_text(client, message):
    t = ""
    if message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
        t = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 1:
        t = ' '.join(message.command[1:])
    if not t: return await message.edit("❌ متنی نیست")
    m = await message.edit("🔄 ترجمه...")
    try:
        r = requests.get(f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=fa&dt=t&q={urllib.parse.quote(t)}").json()
        await m.edit(f"🌐 **ترجمه:**\n\n{''.join([s[0] for s in r[0]])}")
    except Exception: pass

@app.on_message(filters.me & filters.command("آب و هوا", prefixes=""))
async def weather_cmd(client, message):
    if len(message.command) < 2: return await message.edit("❌ `آب و هوا تهران`")
    m = await message.edit("🌤 در حال دریافت...")
    try:
        city = urllib.parse.quote(" ".join(message.command[1:]))
        res = requests.get(f"https://wttr.in/{city}?format=%l:+%c+%t+%h+%w", timeout=15).text
        await m.edit(f"🌤 **آب و هوا**\n📍 {res}")
    except Exception: pass

@app.on_message(filters.me & filters.command("بارکد", prefixes=""))
async def qr_code(client, message):
    if len(message.command) < 2: return await message.edit("❌ `بارکد متن`")
    m = await message.edit("🎨 ساخت...")
    try:
        r = requests.get(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(' '.join(message.command[1:]))}")
        if r.status_code == 200:
            with open("qr.png", "wb") as f: f.write(r.content)
            await app.send_photo(message.chat.id, "qr.png"); os.remove("qr.png"); await m.delete()
    except Exception: pass

@app.on_message(filters.me & filters.command("حساب", prefixes=""))
async def calc_cmd(client, message):
    if len(message.command) < 2: return await message.edit("❌ `حساب 2+2*5`")
    expr = ' '.join(message.command[1:])
    if not set(expr) <= set("0123456789+-*/().% "):
        return await message.edit("❌ فقط اعداد و عملیات مجاز است")
    try:
        r = eval(expr, {"__builtins__": {}}, {})
        await message.edit(f"🧮 `{expr}` = **{r}**")
    except Exception as e:
        await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command("قیمت", prefixes=""))
async def price_command(client, message):
    if len(message.command) < 2: return await message.edit("❌ `قیمت BTC`")
    c = ' '.join(message.command[1:]).strip().upper()
    m = await message.edit("🔍 در حال دریافت...")
    try:
        r = requests.get("https://api.fast-creat.ir/nobitex/v2?apikey=8000978149:uJC3mxBncq9ELPN@Api_ManagerRoBOT").json()
        if r.get("ok") and c in r["result"]:
            d = r["result"][c]
            await m.edit(f"**💰 {d['name']}**\n💵 تومان: `{int(float(d['irr'])):,}`\n💰 دلار: `{float(d['usdt']):,.2f}$`")
        else:
            await m.edit("❌ یافت نشد")
    except Exception:
        await m.edit("❌ خطا")

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
    except Exception as e:
        await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.command("اینستا", prefixes=""))
async def instagram_download_command(client, message):
    if len(message.command) < 2: return await message.edit("❌ لینک نامعتبر")
    u = message.command[1].strip()
    if not u.startswith(("https://www.instagram.com/", "https://instagram.com/")):
        return await message.edit("❌ لینک نامعتبر")
    m = await message.edit("🔄 در حال دریافت...")
    try:
        r = requests.get(f"https://api.fast-creat.ir/instagram?apikey=8000978149:uJC3mxBncq9ELPN@Api_ManagerRoBOT&type=post&url={urllib.parse.quote(u)}").json()
        if not r.get("ok"): return await m.edit("❌ خطا از API")
        p = r["result"]["result"][0]
        if p.get("is_video"):
            v = requests.get(p["video_url"], timeout=60).content
            with open("t.mp4", "wb") as f: f.write(v)
            await app.send_video(message.chat.id, "t.mp4", caption=p.get("caption", "")); os.remove("t.mp4")
        else:
            im = requests.get(p["video_img"], timeout=30).content
            with open("t.jpg", "wb") as f: f.write(im)
            await app.send_photo(message.chat.id, "t.jpg", caption=p.get("caption", "")); os.remove("t.jpg")
        await m.delete()
    except Exception:
        await m.edit("❌ خطا در دانلود")

# ================== 💾 ذخیره‌ساز ==================
@app.on_message(filters.me & filters.command("سیو", prefixes=""))
async def save_cmd(client, message):
    if message.reply_to_message:
        try:
            await message.reply_to_message.copy("me")
            await message.edit("💾 در پیام‌های ذخیره‌شده ذخیره شد")
        except Exception as e:
            await message.edit(f"❌ `{e}`")
    elif len(message.command) > 1 and message.command[1].startswith("@"):
        target = message.command[1]
        m = await message.edit("💾 در حال تهیه بکاپ...")
        try:
            fname = f"{BACKUPS_DIR}/backup_{int(time.time())}.txt"
            count = 0
            with open(fname, "w", encoding="utf-8") as f:
                async for msg in app.get_chat_history(target, limit=500):
                    sender = msg.from_user.first_name if msg.from_user else "?"
                    txt = msg.text or msg.caption or f"[{msg.media}]"
                    f.write(f"[{msg.date}] {sender}: {txt}\n")
                    count += 1
            await app.send_document("me", fname, caption=f"💾 بکاپ {target} — {count} پیام")
            os.remove(fname)
            await m.edit(f"✅ بکاپ {target} ({count} پیام) ارسال شد")
        except Exception as e:
            await m.edit(f"❌ `{e}`")
    else:
        await message.edit("❌ ریپلای برای ذخیره | `سیو @user` برای بکاپ")

@app.on_message(filters.me & filters.regex(r"^عکس سیو$"))
async def photo_save_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.edit("❌ روی عکس ریپلای کنید")
    p = await message.reply_to_message.download()
    s = message.reply_to_message.from_user
    cap = f"📸 عکس سیو شده\n👤 {s.first_name if s else '?'}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    await app.send_photo("me", p, caption=cap)
    os.remove(p)
    await message.edit("✅ عکس در پیام‌های ذخیره‌شده ذخیره شد")

@app.on_message(filters.me & filters.command("یادداشت", prefixes=""))
async def note_cmd(client, message):
    t = message.text.strip()
    if t.startswith("یادداشت حذف "):
        nid = t.split()[-1]
        if nid in notes:
            del notes[nid]; jsave(NOTES_FILE, notes)
            await message.edit(f"🗑 یادداشت {nid} حذف شد")
        else:
            await message.edit("❌ یافت نشد")
    elif len(message.command) > 1 and message.command[1] != "حذف":
        nid = str(len(notes) + 1)
        notes[nid] = ' '.join(message.command[1:])
        jsave(NOTES_FILE, notes)
        await message.edit(f"📝 یادداشت **{nid}** ثبت شد")
    else:
        await message.edit("❌ `یادداشت متن` | `یادداشت‌ها` | `یادداشت حذف شماره`")

@app.on_message(filters.me & filters.regex(r"^(یادداشت‌ها|یادداشت ها)$"))
async def notes_list_cmd(client, message):
    if notes:
        await message.edit("📝 **یادداشت‌ها:**\n" + "\n".join(f"• {k}: {v[:60]}" for k, v in notes.items()))
    else:
        await message.edit("یادداشتی ثبت نشده")

# ================== 🎵 موسیقی و صدا ==================
@app.on_message(filters.me & filters.regex(r"^(ویس|ویس کن)( .+)?$"))
async def tts_cmd(client, message):
    text = ""
    if message.text.startswith("ویس کن") and message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
    elif len(message.command) > 1:
        text = ' '.join(message.command[1:])
    if not text: return await message.edit("❌ `ویس متن` یا ریپلای + `ویس کن`")
    m = await message.edit("🎙 در حال تبدیل...")
    try:
        url = "https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=fa&q=" + urllib.parse.quote(text[:190])
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        with open("tts.mp3", "wb") as f: f.write(r.content)
        try:
            await app.send_voice(message.chat.id, "tts.mp3")
        except Exception:
            await app.send_audio(message.chat.id, "tts.mp3")
        os.remove("tts.mp3"); await m.delete()
    except Exception as e:
        await m.edit(f"❌ `{e}`")

# ================== 📊 سیستم و ❤️ سلامت ==================
@app.on_message(filters.me & filters.command("پینگ", prefixes=""))
async def ping_command(client, message):
    s = datetime.now()
    m = await message.edit("**⏳ ...**")
    await m.edit(f"**🏓 پونگ!**\n**⏱ سرعت: {(datetime.now() - s).microseconds / 1000:.2f} ms**")

@app.on_message(filters.me & filters.regex(r"^آمار$"))
async def stats_cmd(client, message):
    info = ""
    try:
        import psutil
        info = f"🖥 CPU: {psutil.cpu_percent()}%\n💾 RAM: {psutil.virtual_memory().percent}%\n"
    except Exception: pass
    up = int(time.time() - START_TIME)
    h, rem = divmod(up, 3600); mn, sec = divmod(rem, 60)
    chans = groups = privs = 0
    async for d in app.get_dialogs(limit=300):
        t = d.chat.type
        if t == enums.ChatType.CHANNEL: chans += 1
        elif t in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP): groups += 1
        elif t == enums.ChatType.PRIVATE: privs += 1
    await message.edit(f"📊 **آمار سیستم**\n⏱ آپتایم: {h}ساعت {mn}دقیقه {sec}ثانیه\n{info}"
                       f"👤 پیوی: {privs}\n👥 گروه: {groups}\n📢 کانال: {chans}\n"
                       f"👿 دشمنان: {len(enemies)}\n💭 پاسخ‌ها: {len(auto_replies)}")

@app.on_message(filters.me & filters.regex(r"^(سشن‌ها|سشن ها|سشن)$"))
async def sessions_cmd(client, message):
    try:
        r = await app.invoke(rawfn.account.GetAuthorizations())
        lines = []
        for a in r.authorizations:
            cur = " ✅ فعلی" if getattr(a, "current", False) else ""
            lines.append(f"• {a.device_model} | {getattr(a, 'country', '') or '?'} | hash: `{a.hash}`{cur}")
        await message.edit("📱 **سشن‌های فعال:**\n\n" + "\n".join(lines) + "\n\nبرای خروج: `خروج سشن هش`")
    except Exception as e:
        await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.regex(r"^خروج سشن \d+$"))
async def terminate_session_cmd(client, message):
    try:
        await app.invoke(rawfn.account.ResetAuthorization(hash=int(message.text.split()[-1])))
        await message.edit("✅ نشست خاتمه یافت")
    except Exception as e:
        await message.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.regex(r"^سلامت$"))
async def health_cmd(client, message):
    sess = "?"
    try:
        r = await app.invoke(rawfn.account.GetAuthorizations())
        sess = len(r.authorizations)
    except Exception: pass
    me = await app.get_me()
    up = int(time.time() - START_TIME)
    h, rem = divmod(up, 3600); mn, s2 = divmod(rem, 60)
    await message.edit(f"❤️ **سلامت اکانت**\n\n📱 سشن‌های فعال: {sess}\n"
                       f"💎 پریمیوم: {'دارد' if getattr(me, 'is_premium', False) else 'ندارد'}\n"
                       f"⏱ آپتایم سلف: {h}ساعت {mn}دقیقه\n🔒 قفل پیوی: {'فعال' if any(lock_settings.values()) else 'غیرفعال'}\n"
                       f"🛡 انتی‌لاگین: {'فعال' if anti_login_enabled else 'غیرفعال'}")

# ================== 👀 فضول یاب ==================
@app.on_message(filters.me & filters.regex(r"^فضول$"))
async def snooper_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.edit("❌ روی پیام کاربر ریپلای کنید")
    uid = message.reply_to_message.from_user.id
    m = await message.edit("🕵️ در حال بررسی...")
    try:
        commons = await app.get_common_chats(uid)
        names = "\n".join(f"• {c.title or c.first_name}" for c in commons[:10])
        await m.edit(f"👀 **فضول یاب**\n👤 کاربر: {message.reply_to_message.from_user.first_name}\n"
                     f"👥 گروه‌های مشترک: {len(commons)}\n{names}")
    except Exception as e:
        await m.edit(f"❌ `{e}`")

@app.on_message(filters.me & filters.regex(r"^ویوئر .+"))
async def story_viewers_cmd(client, message):
    link = message.text.split(" ", 1)[1].strip()
    mm = re.match(r"https://t\.me/([\w]+)/s/(\d+)", link)
    if not mm:
        return await message.edit("❌ لینک استوری بفرست:\n`ویوئر https://t.me/user/s/123`")
    m = await message.edit("👀 در حال دریافت بینندگان...")
    try:
        fn = getattr(rawfn.stories, "GetStoryViewsList", None)
        if not fn: return await m.edit("❌ این نسخه pyrogram از استوری پشتیبانی نمی‌کند")
        peer = await app.resolve_peer(mm.group(1))
        r = await app.invoke(fn(peer=peer, id=[int(mm.group(2))], limit=50, offset="", offset_reaction=""))
        viewers = getattr(r, "views", []) or []
        lines = "\n".join(f"• `{getattr(v, 'user_id', '?')}`" for v in viewers[:30])
        await m.edit(f"👀 **بینندگان استوری:** {len(viewers)} نفر\n\n{lines}")
    except Exception as e:
        await m.edit(f"❌ `{e}`")

# ================== 🎩 ترفند / 🎲 سرگرمی ==================
@app.on_message(filters.me & filters.regex(r"^قلم \d .+"))
async def fancy_cmd(client, message):
    parts = message.text.split(" ", 2)
    try: sid = int(parts[1])
    except Exception: return await message.edit("❌ `قلم 1 متن`")
    tr = FANCY_TRANS.get(sid); w = WRAPPERS.get(sid, ("", ""))
    out = w[0] + (parts[2].translate(tr) if tr else parts[2]) + w[1]
    await message.edit(out)

@app.on_message(filters.me & filters.regex(r"^(تاس|ریسه|بسکتبال|دارت|بولینگ)$"))
async def dice_cmd(client, message):
    emoji = {"تاس": "🎲", "ریسه": "🪙", "بسکتبال": "🏀", "دارت": "🎯", "بولینگ": "🎳"}[message.text]
    await message.delete()
    await app.send_dice(message.chat.id, emoji)

@app.on_message(filters.me & filters.regex(r"^شانس \d+ \d+$"))
async def random_cmd(client, message):
    a, b = map(int, message.text.replace("شانس", "").split())
    if a > b: a, b = b, a
    await message.edit(f"🎰 شانس با شما: **{random.randint(a, b)}**")

@app.on_message(filters.me & filters.regex(r"^جک$"))
async def joke_cmd(client, message):
    await message.edit("😂 " + random.choice(JOKES))

# ================== 😈 دشمن و فحش ==================
@app.on_message(filters.me & filters.regex(r"^(دشمن|حذف دشمن|لیست دشمن|دشمنان|پاک کردن دشمنان)$"))
async def enemy_cmd(client, message):
    t = message.text
    if t == "دشمن":
        if not message.reply_to_message: return await message.edit("❌ ریپلای کنید")
        enemies.add(message.reply_to_message.from_user.id); save_enemies(enemies)
        await message.edit("😈 دشمن اضافه شد")
    elif t == "حذف دشمن":
        if not message.reply_to_message: return await message.edit("❌ ریپلای کنید")
        enemies.discard(message.reply_to_message.from_user.id); save_enemies(enemies)
        await message.edit("✅ دشمن حذف شد")
    elif t in ("لیست دشمن", "دشمنان"):
        if enemies:
            lines = []
            for e in enemies:
                try:
                    u = await app.get_users(e)
                    lines.append(f"• {u.first_name} | @{u.username or 'ندارد'} | `{e}`")
                except Exception:
                    lines.append(f"• `{e}`")
            await message.edit(f"👿 **لیست دشمنان ({len(enemies)}):**\n" + "\n".join(lines))
        else:
            await message.edit("لیست دشمنان خالی است")
    else:
        enemies.clear(); save_enemies(enemies)
        await message.edit("🧹 لیست دشمنان پاک شد")

@app.on_message(filters.me & filters.command("فحش", prefixes=""))
async def insult_cmd(client, message):
    t = message.text.strip()
    if t.startswith("فحش افزودن "):
        ins = t.replace("فحش افزودن ", "", 1).strip()
        lst = load_insults()
        if ins and ins not in lst:
            lst.append(ins); save_insults(lst)
        await message.edit("✅ فحش اضافه شد")
    elif t.startswith("فحش حذف "):
        ins = t.replace("فحش حذف ", "", 1).strip()
        lst = load_insults()
        if ins in lst:
            lst.remove(ins); save_insults(lst)
            await message.edit("🗑 فحش حذف شد")
        else:
            await message.edit("❌ یافت نشد")
    else:
        lst = load_insults()
        await message.edit(f"💢 تعداد فحش‌ها: {len(lst)}\n\n`فحش افزودن متن` | `فحش حذف متن`")

# ================== 🎨 فرمت / 🔒 قفل / 🛡 حفاظت / ✏️ ویرایش ==================
_FMT_ALIAS = {"زیرخط": "زیر خط", "زیر خط": "زیر خط", "خط‌خورده": "خط‌ خورده", "خط‌ خورده": "خط‌ خورده", "خط خورده": "خط‌ خورده"}

@app.on_message(filters.me & filters.regex(r"^فرمت (بولد|ایتالیک|زیر خط|زیرخط|خط‌ خورده|خط‌خورده|خط خورده|اسپویلر|کد) (روشن|خاموش)$"))
async def format_toggle_cmd(client, message):
    g = message.matches[0].groups()
    key = _FMT_ALIAS.get(g[0], g[0])
    format_settings[key] = (g[1] == "روشن")
    await message.edit(f"🎨 فرمت «{key}» {'روشن' if g[1] == 'روشن' else 'خاموش'} شد")

@app.on_message(filters.me & filters.regex(r"^(فرمت وضعیت|فرمت ریست)$"))
async def format_status_cmd(client, message):
    if message.text == "فرمت ریست":
        for k in format_settings: format_settings[k] = False
        return await message.edit("🟢 همه فرمت‌ها ریست شد")
    st = "\n".join(f"• {k}: {'🟢' if v else '🔴'}" for k, v in format_settings.items())
    await message.edit(f"🎨 **وضعیت فرمت‌ها:**\n{st}")

LOCK_WORDS = "همه|مدیا|استیکر|فوروارد|ویس|پیام|فایل"

@app.on_message(filters.me & filters.regex(rf"^({LOCK_WORDS}) (روشن|خاموش)$"))
async def lock_toggle_cmd(client, message):
    g = message.matches[0].groups()
    lock_settings[g[0]] = (g[1] == "روشن")
    await message.edit(f"{'🔒' if g[1] == 'روشن' else '🔓'} قفل «{g[0]}» {'فعال' if g[1] == 'روشن' else 'غیرفعال'} شد")

@app.on_message(filters.me & filters.regex(r"^(وضعیت قفل|ریست قفل)$"))
async def lock_status_cmd(client, message):
    if message.text == "ریست قفل":
        for k in lock_settings: lock_settings[k] = False
        return await message.edit("🔓 همه قفل‌ها ریست شد")
    st = "\n".join(f"• {k}: {'🔒' if v else '🔓'}" for k, v in lock_settings.items())
    await message.edit(f"🔒 **وضعیت قفل پیوی:**\n{st}")

@app.on_message(filters.me & filters.regex(r"^(آنلاین روشن|آنلاین خاموش)$"))
async def online_toggle_cmd(client, message):
    global always_online_enabled
    always_online_enabled = message.text == "آنلاین روشن"
    await message.edit(f"🌐 همیشه آنلاین {'روشن' if always_online_enabled else 'خاموش'} شد")

@app.on_message(filters.me & filters.regex(r"^(انتی لاگین روشن|انتی لاگین خاموش)$"))
async def antilogin_toggle_cmd(client, message):
    global anti_login_enabled
    anti_login_enabled = message.text == "انتی لاگین روشن"
    await message.edit(f"🛡️ انتی‌لاگین {'روشن' if anti_login_enabled else 'خاموش'} شد")

@app.on_message(filters.me & filters.command("شنود", prefixes="") & filters.regex(r"^شنود (روشن|خاموش)$"))
async def tag_logger_cmd(client, message):
    global tag_logger_on
    tag_logger_on = message.matches[0].group(1) == "روشن"
    await message.edit(f"✅ شنود {'روشن' if tag_logger_on else 'خاموش'} شد")

@app.on_message(filters.me & filters.command("ویرایش", prefixes=""))
async def edit_cmd(client, message):
    if not message.reply_to_message or len(message.command) < 2:
        return await message.edit("❌ ریپلای + `ویرایش قدیم به جدید`")
    t = message.text.replace("ویرایش ", "", 1)
    if " به " not in t: return await message.edit("❌ `ویرایش قدیم به جدید`")
    old, new = t.split(" به ", 1)
    src = message.reply_to_message
    if src.text and old in src.text:
        await src.edit(src.text.replace(old, new))
        await message.delete()
    else:
        await message.edit("❌ کلمه در پیام پیدا نشد")

# ================== پیام‌های دریافتی ==================
async def apply_chat_actions(client, message):
    if not message.from_user or message.from_user.id == (await client.get_me()).id: return
    for a, is_a in action_settings.items():
        if is_a:
            try:
                await client.send_chat_action(message.chat.id, ACTION_MAP[a])
                await asyncio.sleep(2)
                break
            except Exception: pass

async def check_lock(client, message):
    if message.chat.type != enums.ChatType.PRIVATE or not message.from_user or message.from_user.id == (await client.get_me()).id:
        return
    if (lock_settings["همه"] or
        (lock_settings["مدیا"] and (message.photo or message.video)) or
        (lock_settings["استیکر"] and (message.sticker or message.animation)) or
        (lock_settings["فوروارد"] and message.forward_date) or
        (lock_settings["ویس"] and message.voice) or
        (lock_settings["پیام"] and message.text) or
        (lock_settings["فایل"] and message.document)):
        try: await message.delete()
        except Exception: pass

@app.on_message(filters.private & filters.incoming & (filters.photo | filters.video | filters.voice))
async def handle_timed_media(client, message):
    try:
        if message.photo and getattr(message.photo, 'ttl_seconds', None):
            m, t, e = message.photo, 'photo', 'jpg'
        elif message.video and getattr(message.video, 'ttl_seconds', None):
            m, t, e = message.video, 'video', 'mp4'
        elif message.voice and getattr(message.voice, 'ttl_seconds', None):
            m, t, e = message.voice, 'voice', 'ogg'
        else:
            return
        p = os.path.join(SAVED_PHOTOS_DIR, f'{t}-{random.randint(1000, 9999)}.{e}')
        await client.download_media(message, p)
        if os.path.exists(p):
            s = message.from_user
            u = f"@{s.username}" if s and s.username else "ندارد"
            c = f"🔥 مدیای زمان‌دار ({t})\n👤 {s.first_name if s else '?'}\n🆔 {u}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            if t == 'photo': await app.send_photo("me", p, caption=c)
            elif t == 'video': await app.send_video("me", p, caption=c)
            else: await app.send_voice("me", p, caption=c)
            os.remove(p)
    except Exception: pass

@app.on_message(~filters.me & filters.incoming)
async def global_message_handler(client, message):
    if not message.from_user: return
    await check_lock(client, message)
    u = message.from_user.id
    t = message.text or ""
    if u == 777000:
        if anti_login_enabled and any(k in t for k in ["Login code", "کد ورود", "verification code"]):
            try:
                m = re.search(r'(\d{5,6})', t)
                if m:
                    await client.send_message("me", m.group(1)); await message.delete()
            except Exception: pass
        return
    if afk_mode and message.chat.type == enums.ChatType.PRIVATE and u not in afk_notified:
        afk_notified.add(u)
        try:
            await message.reply_text("💤 **در دسترس نیستم**" + (f"\n📌 دلیل: {afk_reason}" if afk_reason else "") + "\n⏰ بعداً پیام بدهید")
        except Exception: pass
    if tag_logger_on and message.entities and message.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
        me = await client.get_me()
        if me.username:
            for en in message.entities:
                if en.type == "mention" and f"@{me.username}" in t:
                    try: await client.send_message("me", f"🔔 تگ شدید!\n👤 {message.from_user.first_name}\n💬 {t}")
                    except Exception: pass
                    break
    for k, v in auto_replies.items():
        if k in t:
            try: await message.reply_text(v)
            except Exception: pass
            break
    if str(u) in auto_reactions:
        try: await client.send_reaction(message.chat.id, message.id, auto_reactions[str(u)])
        except Exception: pass
    if u in enemies and t.strip():
        try: await client.send_message(message.chat.id, random.choice(load_insults()), reply_to_message_id=message.id)
        except Exception: pass

@app.on_message(filters.private & ~filters.me)
async def apply_actions_private(client, message): await apply_chat_actions(client, message)

@app.on_message(filters.group & ~filters.me)
async def apply_actions_group(client, message): await apply_chat_actions(client, message)

# ==============================================================================
# ★ ساخت بنر پنل (عکس پروفایل + اسم) با Pillow ★
# ==============================================================================
PANEL_BANNER_FILE = "panel_banner.png"      # خروجی؛ هلپر همین فایل را می‌خواند
PANEL_TEMPLATE_FILE = "panel_template.jpg"  # پس‌زمینه بنر (اگر نبود، بنر پیش‌فرض ساخته می‌شود)
PANEL_FONT_CANDIDATES = [
    "panel_font.ttf", "Vazirmatn-Bold.ttf", "Vazirmatn.ttf", "Vazir-Bold.ttf", "Vazir.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]
# موقعیت‌ها به‌صورت نسبت از عرض/ارتفاع بنر (از روی عکسی که فرستادی)
PANEL_AVATAR_CENTER = (0.883, 0.282)   # مرکز دایره عکس
PANEL_AVATAR_RADIUS = 0.0733           # شعاع دایره (نسبت به عرض)
PANEL_NAME_CENTER = (0.883, 0.516)      # مرکز کپسول اسم
PANEL_NAME_BOX_W = 0.217               # عرض کپسول اسم (نسبت به عرض)
PANEL_NAME_BOX_H = 0.09               # ارتفاع کپسول اسم (نسبت به ارتفاع)
PANEL_ACCENT = (255, 205, 90)          # رنگ طلایی قاب‌ها

def _panel_res(path):
    """فایل را اول نسبت به پوشه جاری و بعد کنار خود self.py پیدا می‌کند"""
    if os.path.isabs(path) or os.path.exists(path): return path
    alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    return alt if os.path.exists(alt) else path

def _panel_font(size):
    from PIL import ImageFont
    for path in PANEL_FONT_CANDIDATES:
        try: return ImageFont.truetype(_panel_res(path), size)
        except Exception: continue
    try: return ImageFont.load_default(size=size)
    except Exception: return ImageFont.load_default()

def _panel_clean_name(name):
    """ساعت داخل اسم (مثل 𝟏𝟐:𝟑𝟒) را حذف می‌کند؛ فونت‌ها این ارقام را ندارند"""
    import re as _re
    name = _re.sub(r"[\s\u0334]*(?:\d[\u0334]*){1,2}[\u0334]*:[\u0334]*(?:\d[\u0334]*){1,2}[\s\u0334]*", " ", name or "")
    return _re.sub(r"\s+", " ", name).strip()

def _panel_shape_text(text):
    """درست‌کردن حروف چسبیده و راست‌به‌چپ برای اسم فارسی"""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text

def _panel_default_template(w=1200, h=520):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (w, h), (14, 14, 18))
    d = ImageDraw.Draw(img)
    for y in range(h):   # گرادیان تیره
        k = y / h
        d.line([(0, y), (w, y)], fill=(int(14 + 22 * k), int(14 + 10 * k), int(18 + 6 * k)))
    d.ellipse([-200, h - 260, 500, h + 300], fill=(60, 28, 8))
    f1, f2 = _panel_font(150), _panel_font(60)
    d.text((70, 60), "PERSIAN GULF", font=_panel_font(110), fill=PANEL_ACCENT)
    d.text((76, 230), "S E L F", font=f2, fill=(235, 235, 235))
    return img

def make_panel_banner(avatar_path, name, out_path=PANEL_BANNER_FILE, template_path=PANEL_TEMPLATE_FILE):
    """بنر را می‌سازد و مسیر خروجی را برمی‌گرداند. avatar_path می‌تواند None باشد."""
    from PIL import Image, ImageDraw, ImageOps
    try: base = Image.open(_panel_res(template_path)).convert("RGB")
    except Exception: base = _panel_default_template()
    W, H = base.size
    ss = 3   # سوپرسمپل برای لبه‌های نرم
    layer = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # --- دایره عکس ---
    cx, cy, r = PANEL_AVATAR_CENTER[0] * W * ss, PANEL_AVATAR_CENTER[1] * H * ss, PANEL_AVATAR_RADIUS * W * ss
    d.ellipse([cx - r - 7 * ss, cy - r - 7 * ss, cx + r + 7 * ss, cy + r + 7 * ss], fill=(10, 10, 12, 255))
    d.ellipse([cx - r - 5 * ss, cy - r - 5 * ss, cx + r + 5 * ss, cy + r + 5 * ss], outline=PANEL_ACCENT + (255,), width=4 * ss)
    size = int(r * 2)
    try:
        av = ImageOps.fit(Image.open(avatar_path).convert("RGB"), (size, size), Image.LANCZOS)
    except Exception:   # بدون عکس: دایره ساده با حرف اول اسم
        av = Image.new("RGB", (size, size), (40, 40, 48))
        ad = ImageDraw.Draw(av)
        ch = (name or "?").strip()[:1] or "?"
        ft = _panel_font(int(size * 0.5))
        ch = _panel_shape_text(ch)
        bb = ad.textbbox((0, 0), ch, font=ft)
        ad.text(((size - (bb[2] - bb[0])) / 2 - bb[0], (size - (bb[3] - bb[1])) / 2 - bb[1]), ch, font=ft, fill=PANEL_ACCENT)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    layer.paste(av, (int(cx - r), int(cy - r)), mask)

    # --- کپسول اسم ---
    bw, bh = PANEL_NAME_BOX_W * W * ss, PANEL_NAME_BOX_H * H * ss
    nx, ny = PANEL_NAME_CENTER[0] * W * ss, PANEL_NAME_CENTER[1] * H * ss
    d.rounded_rectangle([nx - bw / 2, ny - bh / 2, nx + bw / 2, ny + bh / 2], radius=bh / 2,
                        fill=(8, 12, 26, 225), outline=PANEL_ACCENT + (255,), width=3 * ss)
    txt = _panel_shape_text((name or "").strip() or "Self")
    fs = int(bh * 0.62)
    ft = _panel_font(fs)
    while d.textlength(txt, font=ft) > bw * 0.86 and fs > 10:   # اسم بلند را کوچک کن
        fs -= 2; ft = _panel_font(fs)
    bb = d.textbbox((0, 0), txt, font=ft)
    d.text((nx - (bb[2] - bb[0]) / 2 - bb[0], ny - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=ft, fill=(255, 255, 255, 255))

    layer = layer.resize((W, H), Image.LANCZOS)
    base = base.convert("RGBA")
    base.alpha_composite(layer)
    base.convert("RGB").save(out_path, "PNG")
    return out_path

_panel_banner_key = None
_panel_banner_busy = False
_panel_banner_backoff = 0
_panel_banner_uploaded_at = 0
_panel_banner_next_try = 0
_bg_tasks = set()

def _spawn(coro):
    t = asyncio.create_task(coro)
    _bg_tasks.add(t)
    t.add_done_callback(_bg_tasks.discard)
    return t

async def upload_banner_to_helper():
    """بنر را به پیوی ربات هلپر می‌فرستد تا file_id بگیرد (هلپر خودش پیام را پاک می‌کند)"""
    global _panel_banner_uploaded_at, _panel_banner_next_try
    try:
        sig = str(int(os.path.getmtime(PANEL_BANNER_FILE)))
        sent = await app.send_photo(bot_username, PANEL_BANNER_FILE, caption=f"PANELBANNER|{sig}")
        _panel_banner_uploaded_at = time.time()
        print("🖼 بنر پنل برای هلپر ارسال شد")
        async def _cleanup():
            await asyncio.sleep(90)
            try: await sent.delete(revoke=True)
            except Exception: pass
        _spawn(_cleanup())
    except Exception as e:
        _panel_banner_next_try = time.time() + 120
        print("⚠️ ارسال بنر به هلپر ناموفق بود:", e)

async def refresh_panel_banner():
    """اگر اسم یا عکس پروفایل عوض شده باشد بنر را می‌سازد و برای هلپر می‌فرستد"""
    global _panel_banner_key, _panel_banner_busy, _panel_banner_backoff
    if _panel_banner_busy or time.time() < _panel_banner_backoff: return
    _panel_banner_busy = True
    try:
        me = await app.get_me()
        name = (me.first_name or "").strip()
        if user_time_status.get(me.id) and user_original_names.get(me.id):
            name = user_original_names[me.id].strip()   # اسم بدون ساعت
        name = _panel_clean_name(name)
        ph = me.photo
        pid = None
        if ph:
            pid = (getattr(ph, "big_photo_unique_id", None) or getattr(ph, "big_file_unique_id", None)
                   or getattr(ph, "big_file_id", None))
        key = (pid, name)
        changed = key != _panel_banner_key or not os.path.exists(PANEL_BANNER_FILE)
        if changed:
            av = None
            if me.photo:
                try: av = await app.download_media(me.photo.big_file_id)
                except Exception: av = None
            await asyncio.to_thread(make_panel_banner, av, name)
            _panel_banner_key = key
            print("🎨 بنر پنل ساخته شد")
        now = time.time()
        # هر ۶ ساعت هم دوباره ارسال می‌شود تا file_id تازه بماند
        if (changed or now - _panel_banner_uploaded_at > 6 * 3600) and now >= _panel_banner_next_try:
            await upload_banner_to_helper()
    except Exception as e:
        _panel_banner_backoff = time.time() + 60
        import traceback
        print("⚠️ ساخت بنر پنل ناموفق بود [r7]:", repr(e))
        print(traceback.format_exc())
    finally:
        _panel_banner_busy = False

# ==============================================================================
# ★ سیستم پنل — ارتباط زنده با هلپر (فایل مشترک) ★
# ==============================================================================
STATE_FILE = "selfbot_state.json"
ACTIONS_FILE = "panel_actions.json"

def _atomic_write_json(path, data):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception: pass

_bio_cache = {"bio": "", "ts": 0.0}

async def build_panel_state():
    me = await app.get_me()
    bio = _bio_cache["bio"]
    if time.time() - _bio_cache["ts"] > 300:
        _bio_cache["ts"] = time.time()
        try: bio = _bio_cache["bio"] = (await app.get_chat(me.id)).bio or ""
        except Exception: pass
    return {
        "updated": int(time.time()),
        "banner": os.path.abspath(PANEL_BANNER_FILE),
        "account": {
            "first_name": me.first_name or "", "last_name": me.last_name or "",
            "username": me.username or "", "id": me.id,
            "premium": bool(getattr(me, "is_premium", False)),
            "phone": me.phone_number or "", "bio": bio,
        },
        "settings": {
            "always_online": always_online_enabled, "tag_logger": tag_logger_on,
            "anti_login": anti_login_enabled, "afk": afk_mode,
            "signature": signature_on, "auto_delete": auto_delete_seconds > 0,
            "time_on": bool(user_time_status.get(me.id)),
            "actions": dict(action_settings), "formats": dict(format_settings),
            "locks": dict(lock_settings),
            "enemies_count": len(enemies), "reactions_count": len(auto_reactions),
            "replies_count": len(auto_replies), "notes_count": len(notes),
        }
    }

async def refresh_panel_state():
    try: _atomic_write_json(STATE_FILE, await build_panel_state())
    except Exception: pass

async def panel_state_loop():
    while True:
        await refresh_panel_state()
        _spawn(refresh_panel_banner())
        await asyncio.sleep(15)

async def execute_panel_action(item):
    global always_online_enabled, tag_logger_on, anti_login_enabled
    global afk_mode, signature_on, auto_delete_seconds
    name = item.get("action", "")
    try:
        if name == "toggle_online": always_online_enabled = not always_online_enabled
        elif name == "toggle_taglogger": tag_logger_on = not tag_logger_on
        elif name == "toggle_antilogin": anti_login_enabled = not anti_login_enabled
        elif name == "toggle_afk":
            afk_mode = not afk_mode; afk_notified.clear()
        elif name == "toggle_signature": signature_on = not signature_on
        elif name == "toggle_autodel": auto_delete_seconds = 0 if auto_delete_seconds else 30
        elif name == "action_typing": action_settings["typing"] = not action_settings["typing"]
        elif name == "action_photo": action_settings["upload_photo"] = not action_settings["upload_photo"]
        elif name == "action_voice": action_settings["record_audio"] = not action_settings["record_audio"]
        elif name == "action_game": action_settings["playing"] = not action_settings["playing"]
        elif name == "action_reset":
            for k in action_settings: action_settings[k] = False
        elif name == "format_bold": format_settings["بولد"] = not format_settings["بولد"]
        elif name == "format_italic": format_settings["ایتالیک"] = not format_settings["ایتالیک"]
        elif name == "format_underline": format_settings["زیر خط"] = not format_settings["زیر خط"]
        elif name == "format_strike": format_settings["خط‌ خورده"] = not format_settings["خط‌ خورده"]
        elif name == "format_spoiler": format_settings["اسپویلر"] = not format_settings["اسپویلر"]
        elif name == "format_code": format_settings["کد"] = not format_settings["کد"]
        elif name == "format_reset":
            for k in format_settings: format_settings[k] = False
        elif name == "lock_all": lock_settings["همه"] = not lock_settings["همه"]
        elif name == "lock_media": lock_settings["مدیا"] = not lock_settings["مدیا"]
        elif name == "lock_sticker": lock_settings["استیکر"] = not lock_settings["استیکر"]
        elif name == "lock_forward": lock_settings["فوروارد"] = not lock_settings["فوروارد"]
        elif name == "lock_voice": lock_settings["ویس"] = not lock_settings["ویس"]
        elif name == "lock_text": lock_settings["پیام"] = not lock_settings["پیام"]
        elif name == "lock_file": lock_settings["فایل"] = not lock_settings["فایل"]
        elif name == "lock_reset":
            for k in lock_settings: lock_settings[k] = False
        elif name == "time_on":
            me = await app.get_me()
            user_time_status[me.id] = True
            user_original_names.setdefault(me.id, me.first_name or "")
            await app.update_profile(first_name=f"{user_original_names.get(me.id)} {fa_time_str(user_fonts.get(me.id, 1))}")
        elif name == "time_off":
            me = await app.get_me()
            user_time_status[me.id] = False
            if me.id in user_original_names:
                await app.update_profile(first_name=user_original_names[me.id])
    except Exception: pass
    await refresh_panel_state()

async def panel_actions_loop():
    while True:
        try:
            if os.path.exists(ACTIONS_FILE):
                with open(ACTIONS_FILE, "r", encoding="utf-8") as f:
                    raw = f.read().strip()
                items = json.loads(raw) if raw else []
                if items:
                    try: os.remove(ACTIONS_FILE)
                    except Exception: pass
                    for item in items:
                        if isinstance(item, dict):
                            await execute_panel_action(item)
        except Exception: pass
        await asyncio.sleep(0.7)

async def online_loop():
    while True:
        if always_online_enabled:
            try: await app.invoke(rawfn.account.UpdateStatus(offline=False))
            except Exception: pass
        await asyncio.sleep(25)

async def time_loop():
    while True:
        try:
            me = await app.get_me()
            if user_time_status.get(me.id):
                fid = user_fonts.get(me.id, 1)
                orig = user_original_names.get(me.id, me.first_name or "")
                await app.update_profile(first_name=f"{orig} {fa_time_str(fid)}")
        except Exception: pass
        await asyncio.sleep(60)

async def banner_loop():
    global last_banner
    while True:
        if banner_active and banner_active in banners and (time.time() - last_banner) >= max(60, banner_interval_min * 60):
            last_banner = time.time()
            text = banners[banner_active]
            async for d in app.get_dialogs(limit=200):
                if d.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
                    try:
                        await app.send_message(d.chat.id, text)
                        await asyncio.sleep(4)
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                    except Exception: pass
        await asyncio.sleep(20)

if __name__ == "__main__":
    print("🧩 Persian Gulf Self | build panel-banner-r7 |", os.path.abspath(__file__))
    if USER_ID: print(f"✅ Persian Gulf Self برای کاربر {USER_ID} در حال اجرا... (نسخه شاهکار v7.0)")
    else: print("⚠️ سلف‌بات در حالت معمولی اجرا شد")
    if not USER_ID and not os.path.exists("self.session"):
        print("❌ بدون آرگومان و بدون فایل self.session اجرا شد؛ این پروسه لازم نیست (سلف‌بات را هلپر اجرا می‌کند). خروج.")
        sys.exit(0)
    loop = asyncio.get_event_loop()
    app.start()
    print("🔗 سیستم پنل Persian Gulf Self فعال شد")
    try:
        loop.run_until_complete(asyncio.gather(
            panel_state_loop(), panel_actions_loop(),
            online_loop(), time_loop(), banner_loop()))
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()
