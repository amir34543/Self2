# ==============================================================================
#  ربات هلپر و پنل مدیریت سلف بات — PersianGulf Helper
#  نسخه: 7.0.0 «شاهکار» — حساب کاربری + تنظیمات کامل سلف + بنر عکس/اسم
# ==============================================================================

from pyrogram import Client, enums, filters
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                            InlineQueryResultArticle, InputTextMessageContent)
import logging, asyncio, json, os, time
from html import escape

try:
    from pyrogram.types import InlineQueryResultCachedPhoto
    HAS_CACHED_PHOTO = True
except ImportError:
    HAS_CACHED_PHOTO = False

try:
    from pyrogram.errors import MessageNotModified
except ImportError:
    class MessageNotModified(Exception): pass

try:
    from pyrogram.types import KeyboardButtonStyle
    HAS_STYLE = True
except ImportError:
    HAS_STYLE = False
    class KeyboardButtonStyle:
        def __init__(self, **kw): pass

# توکن را در Railway → Variables با نام HELPER_BOT_TOKEN بگذار (پیشنهادی)
# یا مستقیم به‌جای PUT_TOKEN_HERE بنویس
TOKEN = os.environ.get("8895709305:AAEUAYHr1nKKk46wpQaAzC98mWa3ChKUfis") or "PUT_TOKEN_HERE"
API_ID = 35656061
API_HASH = "b37f2596516bc0439bf505d1d230395c"

logging.basicConfig(level=logging.INFO)
if TOKEN == "PUT_TOKEN_HERE":
    raise SystemExit("❌ توکن ربات هلپر تنظیم نشده (متغیر HELPER_BOT_TOKEN یا خط TOKEN)")
app = Client("helper_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

STATE_FILE = "selfbot_state.json"
ACTIONS_FILE = "panel_actions.json"
BANNER_FILE = "panel_banner.png"   # توسط self.py ساخته می‌شود

TOGGLE_MAP = {
    "online": "toggle_online", "taglogger": "toggle_taglogger",
    "antilogin": "toggle_antilogin", "afk": "toggle_afk",
    "signature": "toggle_signature", "autodel": "toggle_autodel",
    "typing": "action_typing", "photo": "action_photo",
    "voice": "action_voice", "game": "action_game", "act_reset": "action_reset",
    "bold": "format_bold", "italic": "format_italic", "underline": "format_underline",
    "strike": "format_strike", "spoiler": "format_spoiler", "code": "format_code",
    "fmt_reset": "format_reset",
    "lock_all": "lock_all", "lock_media": "lock_media", "lock_sticker": "lock_sticker",
    "lock_forward": "lock_forward", "lock_voice": "lock_voice",
    "lock_text": "lock_text", "lock_file": "lock_file", "lock_reset": "lock_reset",
}

# ------------------------- ابزار فایل -------------------------
def load_self_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def queue_action(user_id, action):
    items = []
    try:
        if os.path.exists(ACTIONS_FILE):
            with open(ACTIONS_FILE, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            items = json.loads(raw) if raw else []
            if not isinstance(items, list): items = []
    except Exception:
        items = []
    items.append({"user_id": user_id, "action": action, "ts": time.time()})
    tmp = ACTIONS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)
    os.replace(tmp, ACTIONS_FILE)

def state_online(state):
    return bool(state) and (time.time() - state.get("updated", 0)) < 90

# ------------------------- بنر پنل (عکس + اسم) -------------------------
_banner_cache = {"mtime": None, "fid": None}
_banner_lock = asyncio.Lock()

def banner_path(state):
    for p in ((state or {}).get("banner"), BANNER_FILE):
        if p and os.path.exists(p):
            return p
    return None

async def get_banner_file_id(client, owner_id, state):
    """بنر را یک‌بار برای خود مالک آپلود می‌کند تا file_id بگیرد و بلافاصله پاکش می‌کند"""
    path = banner_path(state)
    if not path:
        return None
    mt = os.path.getmtime(path)
    async with _banner_lock:
        if _banner_cache["fid"] and _banner_cache["mtime"] == mt:
            return _banner_cache["fid"]
        try:
            msg = await client.send_photo(owner_id, path, disable_notification=True)
            fid = msg.photo.file_id
            _banner_cache.update(mtime=mt, fid=fid)
            try: await msg.delete()
            except Exception: pass
            return fid
        except Exception as e:
            logging.warning(f"آپلود بنر ناموفق بود (آیا هلپر را /start کرده‌ای؟): {e}")
            return None

async def edit_view(client, cq, text, kb):
    """ویرایش پیام پنل؛ هم برای پیام متنی و هم برای پیام عکس‌دار (کپشن)"""
    try:
        if cq.inline_message_id:
            fn = getattr(client, "edit_inline_caption", None) or client.edit_inline_text
            await fn(cq.inline_message_id, text, parse_mode=enums.ParseMode.HTML, reply_markup=kb)
        else:
            await cq.edit_message_text(text, reply_markup=kb, parse_mode=enums.ParseMode.HTML)
    except MessageNotModified:
        pass
    except Exception as e:
        if "MESSAGE_NOT_MODIFIED" in str(e):
            return
        raise

# ------------------------- دکمه‌ها -------------------------
def btn(text, cb, style=None):
    if style is not None and HAS_STYLE:
        return InlineKeyboardButton(text, callback_data=cb, style=style)
    return InlineKeyboardButton(text, callback_data=cb)

def style_on(on):
    if not HAS_STYLE: return None
    return KeyboardButtonStyle(bg_success=True) if on else KeyboardButtonStyle(bg_primary=True)

def S(kind):
    if not HAS_STYLE: return None
    return {"p": KeyboardButtonStyle(bg_primary=True),
            "s": KeyboardButtonStyle(bg_success=True),
            "d": KeyboardButtonStyle(bg_danger=True)}[kind]

# ==============================================================================
# کیبوردها
# ==============================================================================
def get_main_keyboard(uid):
    return InlineKeyboardMarkup([
        [btn("👤 حساب کاربری", f"p:account:{uid}", S("p")),
         btn("⚙️ تنظیمات سلف", f"p:cats:{uid}", S("p"))],
        [btn("❌ بستن پنل", f"p:close:{uid}", S("d"))]
    ])

def get_account_keyboard(uid):
    return InlineKeyboardMarkup([
        [btn("🔄 تازه‌سازی", f"p:account:{uid}", S("s")),
         btn("⚙️ تنظیمات سلف", f"p:cats:{uid}", S("p"))],
        [btn("🔙 صفحه اول", f"p:home:{uid}", S("p"))]
    ])

def get_categories_keyboard(uid):
    c = [
        ("🪄 پروفایل", "profile"), ("👥 گروه", "group"),
        ("🤝 دعوت و لمس", "invite"), ("🔇 سکوت و بلاک", "block"),
        ("😏 منش و AFK", "afk"), ("🗑 پاک‌سازی خودکار", "autodel"),
        ("🚀 سندر", "sender"), ("🧹 تمیز", "clean"),
        ("📨 اسپم", "spam"), ("💭 پاسخ خودکار", "autoreply"),
        ("🛠 ابزار", "tools"), ("💾 ذخیره‌ساز", "saver"),
        ("🎵 موسیقی و صدا", "music"), ("📊 سیستم", "system"),
        ("❤️ سلامت اکانت", "health"), ("👀 فضول یاب", "finder"),
        ("🎩 ترفند", "trick"), ("🎲 سرگرمی", "fun"),
        ("🎨 فرمت متن", "format"), ("🔒 قفل پیوی", "lock"),
        ("🛡 حفاظت", "protect"), ("✏️ ویرایش", "edit"),
    ]
    rows = [[btn("⚡ تنظیمات زنده سلف", f"p:live:{uid}", S("s"))]]
    for i in range(0, len(c), 2):
        pair = c[i:i+2]
        rows.append([btn(t, f"p:cat:{uid}:{k}", S("p")) for t, k in pair])
    rows.append([btn("✨ منوهای شیشه‌ای", f"p:cat:{uid}:extra", S("s"))])
    rows.append([btn("🔙 صفحه اول", f"p:home:{uid}", S("p")),
                 btn("❌ بستن", f"p:close:{uid}", S("d"))])
    return InlineKeyboardMarkup(rows)

def get_back_keyboard(uid, target="cats"):
    return InlineKeyboardMarkup([[btn("🔙 بازگشت", f"p:back:{uid}:{target}", S("p"))]])

def get_live_keyboard(uid, state):
    s = (state or {}).get("settings", {})
    def sw(key, label):
        on = bool(s.get(key))
        return [btn(("✅ " if on else "☐ ") + label, f"p:tg:{uid}:{key}:live", style_on(on))]
    rows = (sw("always_online", "🌐 همیشه آنلاین") +
            sw("tag_logger", "👂 شنود تگ") +
            sw("anti_login", "🛡️ انتی‌لاگین") +
            sw("afk", "😏 حالت AFK") +
            sw("signature", "✍️ امضای خودکار") +
            sw("auto_delete", "🗑 حذف خودکار پیام‌ها") +
            [[btn("🎭 اکشن‌ها ←", f"p:actions:{uid}", S("p")),
              btn("🎨 فرمت‌ها ←", f"p:formats:{uid}", S("p"))],
             [btn("🔒 قفل‌ها ←", f"p:locks:{uid}", S("p")),
              btn("🔄 تازه‌سازی", f"p:live:{uid}", S("s"))],
             [btn("🔙 بازگشت", f"p:cats:{uid}", S("p"))]])
    return InlineKeyboardMarkup(rows)

def get_actions_keyboard(uid, state):
    a = (state or {}).get("settings", {}).get("actions", {})
    def sw(ck, label):
        on = bool(a.get(ck))
        return [btn(("✅ " if on else "☐ ") + label, f"p:tg:{uid}:{ck}:actions", style_on(on))]
    return InlineKeyboardMarkup(
        sw("typing", "⌨️ تایپ") + sw("upload_photo", "📤 آپلود عکس") +
        sw("record_audio", "🎙 ضبط ویس") + sw("playing", "🎮 بازی") +
        [[btn("🔴 ریست اکشن‌ها", f"p:tg:{uid}:act_reset:actions", S("d")),
          btn("🔄 تازه‌سازی", f"p:actions:{uid}", S("s"))],
         [btn("🔙 بازگشت", f"p:live:{uid}", S("p"))]])

def get_formats_keyboard(uid, state):
    fm = (state or {}).get("settings", {}).get("formats", {})
    def sw(pk, label, ck):
        on = bool(fm.get(pk))
        return [btn(("✅ " if on else "☐ ") + label, f"p:tg:{uid}:{ck}:formats", style_on(on))]
    return InlineKeyboardMarkup(
        sw("بولد", "🅱 بولد", "bold") + sw("ایتالیک", "🅸 ایتالیک", "italic") +
        sw("زیر خط", "🅄 زیر خط", "underline") + sw("خط‌ خورده", "🅂 خط‌خورده", "strike") +
        sw("اسپویلر", "🆂 اسپویلر", "spoiler") + sw("کد", "🅲 کد", "code") +
        [[btn("🟢 ریست فرمت‌ها", f"p:tg:{uid}:fmt_reset:formats", S("d")),
          btn("🔄 تازه‌سازی", f"p:formats:{uid}", S("s"))],
         [btn("🔙 بازگشت", f"p:live:{uid}", S("p"))]])

def get_locks_keyboard(uid, state):
    lk = (state or {}).get("settings", {}).get("locks", {})
    def sw(pk, label, ck):
        on = bool(lk.get(pk))
        return [btn(("🔒 " if on else "🔓 ") + label, f"p:tg:{uid}:{ck}:locks", style_on(on))]
    return InlineKeyboardMarkup(
        sw("همه", "همه", "lock_all") + sw("مدیا", "مدیا", "lock_media") +
        sw("استیکر", "استیکر", "lock_sticker") + sw("فوروارد", "فوروارد", "lock_forward") +
        sw("ویس", "ویس", "lock_voice") + sw("پیام", "پیام", "lock_text") +
        sw("فایل", "فایل", "lock_file") +
        [[btn("🟢 ریست قفل‌ها", f"p:tg:{uid}:lock_reset:locks", S("d")),
          btn("🔄 تازه‌سازی", f"p:locks:{uid}", S("s"))],
         [btn("🔙 بازگشت", f"p:live:{uid}", S("p"))]])

# ==============================================================================
# متن صفحات
# ==============================================================================
MAIN_TEXT = ("🎛 <b>پنل مدیریت سلف</b>\n\n"
             "👇 از دکمه‌های زیر استفاده کنید:\n"
             "• 👤 <b>حساب کاربری</b> — اطلاعات زنده اکانت شما\n"
             "• ⚙️ <b>تنظیمات سلف</b> — همه دستورات و تنظیمات")

CATS_TEXT = ("🤖 <b>NitroSelf — پنل دستورات</b>\n\n"
             "💡 روی هر بخش بزنید تا دستوراتش باز شود\n"
             "📋 دستورات را کپی کنید و در چت خودتان بفرستید")

CAT_TEXTS = {
"profile": """🪄 <b>مدیریت پروفایل</b>

<b>دستورات قابل کپی:</b>
<code>پروفایل</code> — تغییر عکس (ریپلای روی عکس)
<code>حذف عکس</code> — حذف آخرین عکس پروفایل
<code>حذف همه عکس</code> — حذف تمام عکس‌ها
<code>بایو متن جدید</code> — تغییر بیوگرافی
<code>یوزر آیدی_جدید</code> — تغییر آیدی
<code>نام جدید</code> — تغییر نام
<code>نام کامل نام فامیلی</code> — نام + فامیل
<code>تایم روشن</code> / <code>تایم خاموش</code> — ساعت در اسم
<code>لیست فونت</code> — مشاهده فونت‌های زمان
<code>تنظیم فونت 1</code> تا <code>تنظیم فونت 6</code>""",

"group": """👥 <b>ابزار گروه</b>

<b>دستورات قابل کپی:</b>
<code>ساخت گروه نام</code> — ساخت گروه جدید
<code>قفل گروه</code> / <code>بازکردن گروه</code>
<code>پین</code> — پین پیام (ریپلای)
<code>آنپین</code> — برداشتن پین آخر
<code>کیک</code> — اخراج کاربر (ریپلای)
<code>بن</code> — مسدودسازی (ریپلای)
<code>آنبن</code> — رفع مسدودی (ریپلای)
<code>تعداد کانال ها</code> / <code>تعداد گروه ها</code>
<code>خروج همه کانال</code> / <code>خروج همه گروه</code>""",

"invite": """🤝 <b>دعوت و مخاطب</b>

<b>دستورات قابل کپی:</b>
<code>افزودن @user</code> — افزودن عضو به گروه فعلی
<code>مخاطب 09123456789 نام</code> — ارسال مخاطب
<code>شماره من</code> — ارسال شماره خودتان""",

"block": """🔇 <b>سکوت و بلاک</b>

<b>دستورات قابل کپی:</b>
<code>سکوت</code> — ساکت کردن کاربر در گروه (ریپلای)
<code>رفع سکوت</code> (ریپلای)
<code>بلاک @user</code> یا ریپلای — بلاک کردن
<code>آنبلاک @user</code> یا ریپلای""",

"afk": """😏 <b>منش و AFK</b>

<b>دستورات قابل کپی:</b>
<code>افک روشن دلیل</code> — حالت دور از دسترس (پاسخ خودکار میدهد)
<code>افک خاموش</code>
<code>منش روشن</code> — امضای خودکار زیر پیام‌هایت
<code>منش خاموش</code>
<code>امضا متن شما</code> — تنظیم متن امضا
<code>ریکت ❤️</code> — ریکشن خودکار به کاربر (ریپلای)
<code>حذف ریکت</code> (ریپلای)
<code>لیست ریکت</code> / <code>پاکسازی ریکت</code>""",

"autodel": """🗑 <b>پاک‌سازی خودکار</b>

<b>دستورات قابل کپی:</b>
<code>حذف خودکار روشن 30</code> — پیام‌های شما بعد از ۳۰ ثانیه حذف شود
<code>حذف خودکار خاموش</code>
<code>حذف زمان‌دار 10</code> — حذف پیام ریپلای‌شده بعد از ۱۰ ثانیه""",

"sender": """🚀 <b>سندر (ارسال همگانی)</b>

<b>دستورات قابل کپی:</b>
<code>همگانی گروه متن</code>
<code>همگانی پیوی متن</code>
<code>همگانی کانال متن</code>
<code>همگانی همه متن</code>

📢 <b>سیستم بنر:</b>
<code>تنظیم بنر</code> — ثبت بنر (ریپلای)
<code>لیست بنرها</code>
<code>بنر همگانی 1</code> — ارسال خودکار دوره‌ای
<code>بنر همگانی خاموش</code>
<code>بنر ارسال 1</code> — ارسال فوری
<code>زمان بنر 5</code> — فاصله ارسال (دقیقه)""",

"clean": """🧹 <b>تمیزکاری</b>

<b>دستورات قابل کپی:</b>
<code>پاکسازی</code> — پاک کردن تاریخچه چت فعلی
<code>حذف پیام 20</code> — حذف ۲۰ پیام آخر خودتان
<code>حذف همه عکس</code> — حذف عکس‌های پروفایل""",

"spam": """📨 <b>اسپم</b>

<b>دستور قابل کپی:</b>
<code>اسپم 10 متن</code>

حداکثر ۵۰ پیام در هر دستور""",

"autoreply": """💭 <b>پاسخ خودکار</b>

<b>دستورات قابل کپی:</b>
<code>پاسخ افزودن سلام|سلام چطوری؟</code>
<code>پاسخ حذف سلام</code>
<code>پاسخ لیست</code>

هر کسی کلمه را بفرستد، پاسخ خودکار می‌گیرد""",

"tools": """🛠 <b>ابزارها</b>

<b>دستورات قابل کپی:</b>
<code>ایدی</code> — اطلاعات آیدی (با ریپلای هم کار می‌کند)
<code>ترجمه متن</code> یا ریپلای — ترجمه به فارسی
<code>آب و هوا تهران</code>
<code>بارکد متن</code> — ساخت QR Code
<code>حساب 25*4+10</code> — ماشین حساب
<code>قیمت BTC</code> — قیمت ارز (فارسی هم میشود)
<code>دانلود لینک_پست_تلگرام</code>
<code>اینستا لینک_پست</code> — دانلود اینستاگرام""",

"saver": """💾 <b>ذخیره‌ساز</b>

<b>دستورات قابل کپی:</b>
<code>سیو</code> (ریپلای) — ذخیره در پیام‌های ذخیره‌شده
<code>سیو @user</code> — بکاپ کامل چت به صورت فایل
<code>عکس سیو</code> (ریپلای روی عکس)
<code>یادداشت متن</code> — ثبت یادداشت
<code>یادداشت‌ها</code> — مشاهده یادداشت‌ها
<code>یادداشت حذف شماره</code>""",

"music": """🎵 <b>موسیقی و صدا</b>

<b>دستورات قابل کپی:</b>
<code>ویس سلام خوبی</code> — تبدیل متن به ویس
<code>ویس کن</code> (ریپلای روی متن)""",

"system": """📊 <b>سیستم و اطلاعات</b>

<b>دستورات قابل کپی:</b>
<code>پینگ</code> — سرعت پاسخ سلف
<code>آمار</code> — CPU / RAM / آپتایم / آمار چت‌ها""",

"health": """❤️ <b>سلامت اکانت</b>

<b>دستورات قابل کپی:</b>
<code>سلامت</code> — گزارش کلی سلامت اکانت
<code>سشن‌ها</code> — لیست نشست‌های فعال
<code>خروج سشن 123456</code> — خروج از یک نشست (هش از لیست سشن‌ها)""",

"finder": """👀 <b>فضول یاب</b>

<b>دستورات قابل کپی:</b>
<code>فضول</code> (ریپلای روی پیام کاربر) — گروه‌های مشترک با آن کاربر
<code>ویوئر لینک استوری</code> — بینندگان استوری
مثال: <code>ویوئر https://t.me/user/s/123</code>""",

"trick": """🎩 <b>ترفندها</b>

<b>دستور قابل کپی:</b>
<code>قلم 1 متن</code> تا <code>قلم 6 متن</code>

۶ فونت فانتزی زیبا برای متن انگلیسی
مثال: <code>قلم 2 Hello World</code>""",

"fun": """🎲 <b>سرگرمی</b>

<b>دستورات قابل کپی:</b>
<code>تاس</code> / <code>ریسه</code> / <code>بسکتبال</code> / <code>دارت</code> / <code>بولینگ</code>
<code>شانس 1 100</code> — عدد شانس
<code>جک</code> — جک رندوم""",

"format": """🎨 <b>فرمت خودکار متن</b>

<b>دستورات قابل کپی:</b>
<code>فرمت بولد روشن</code> / <code>فرمت بولد خاموش</code>
<code>فرمت ایتالیک روشن</code> / <code>فرمت ایتالیک خاموش</code>
<code>فرمت زیر خط روشن</code> / <code>فرمت زیر خط خاموش</code>
<code>فرمت خط‌خورده روشن</code> / <code>فرمت خط‌خورده خاموش</code>
<code>فرمت اسپویلر روشن</code> / <code>فرمت اسپویلر خاموش</code>
<code>فرمت کد روشن</code> / <code>فرمت کد خاموش</code>
<code>فرمت وضعیت</code> / <code>فرمت ریست</code>
<code>منوی متن</code> — منوی شیشه‌ای سریع""",

"lock": """🔒 <b>قفل پیوی</b>

<b>دستورات قابل کپی:</b>
<code>همه روشن</code> / <code>همه خاموش</code>
<code>مدیا روشن</code> / <code>مدیا خاموش</code>
<code>استیکر روشن</code> / <code>استیکر خاموش</code>
<code>فوروارد روشن</code> / <code>فوروارد خاموش</code>
<code>ویس روشن</code> / <code>ویس خاموش</code>
<code>پیام روشن</code> / <code>پیام خاموش</code>
<code>فایل روشن</code> / <code>فایل خاموش</code>
<code>وضعیت قفل</code> / <code>ریست قفل</code>""",

"protect": """🛡 <b>حفاظت و وضعیت</b>

<b>دستورات قابل کپی:</b>
<code>آنلاین روشن</code> / <code>آنلاین خاموش</code>
<code>انتی لاگین روشن</code> / <code>انتی لاگین خاموش</code>
<code>شنود روشن</code> / <code>شنود خاموش</code> — اطلاع تگ شدن
<code>منوی تنظیمات</code> — منوی شیشه‌ای سریع""",

"edit": """✏️ <b>ویرایش سریع</b>

<b>دستور قابل کپی:</b>
<code>ویرایش کلمه_قدیم به کلمه_جدید</code> (ریپلای روی پیام)

مثال: <code>ویرایش سلان به سلام</code>""",

"extra": """✨ <b>منوهای شیشه‌ای (Glass)</b>

<b>دستورات:</b>
<code>منوی متن</code> — دکمه‌های تیک‌دار بولد/ایتالیک/...
<code>منوی اکشن</code> — تایپ، آپلود عکس، ضبط ویس، بازی
<code>منوی تنظیمات</code> — آنلاین، شنود، انتی‌لاگین

با کلیک روی دکمه‌ها تیک ✅ می‌خورد و با کلیک مجدد برداشته می‌شود""",
}

def build_account_text(state):
    if not state_online(state):
        return ("⚠️ <b>سلف آفلاین است</b>\n\n"
                "ربات سلف (<code>self.py</code>) روشن نیست یا هنوز وضعیتی ارسال نکرده.\n"
                "هر دو فایل باید در <b>یک پوشه</b> اجرا شوند.")
    acc = state.get("account", {})
    s = state.get("settings", {})
    name = ((acc.get("first_name") or "") + " " + (acc.get("last_name") or "")).strip() or "—"
    lines = [
        "👤 <b>حساب کاربری سلف</b>", "",
        f"🪪 نام: <b>{escape(name)}</b>",
        f"🔗 یوزرنیم: @{escape(acc.get('username') or 'ندارد')}",
        f"🆔 آیدی: <code>{acc.get('id', '—')}</code>",
        f"💎 پریمیوم: {'✅ فعال' if acc.get('premium') else '❌ غیرفعال'}",
        f"📱 شماره: <code>{escape(acc.get('phone') or '—')}</code>",
    ]
    if acc.get("bio"):
        lines.append(f"📝 بیو: <i>{escape(acc['bio'][:200])}</i>")
    lines += [
        "", "📊 <b>آمار سلف</b>",
        f"👿 دشمنان: <code>{s.get('enemies_count', 0)}</code>",
        f"🎭 ریکشن‌ها: <code>{s.get('reactions_count', 0)}</code>",
        f"💭 پاسخ‌های خودکار: <code>{s.get('replies_count', 0)}</code>",
        f"📝 یادداشت‌ها: <code>{s.get('notes_count', 0)}</code>",
        f"⏰ آپدیت: <code>{time.strftime('%H:%M:%S', time.localtime(state.get('updated', 0)))}</code>",
    ]
    return "\n".join(lines)

def settings_page_text(state):
    if state_online(state):
        head = "⚡ <b>تنظیمات زنده سلف</b>\n<i>روی دکمه‌ها بزنید تا فوراً روی اکانت اعمال شود</i>"
    else:
        head = "⚠️ <b>سلف آفلاین است</b>\n<i>دستورات در صف می‌مانند و با روشن شدن سلف اعمال می‌شوند</i>"
    s = (state or {}).get("settings", {})
    def on(k): return "🟢" if s.get(k) else "🔴"
    return (head + "\n\n"
            f"🌐 آنلاین: {on('always_online')}\n"
            f"👂 شنود تگ: {on('tag_logger')}\n"
            f"🛡️ انتی‌لاگین: {on('anti_login')}\n"
            f"😏 AFK: {on('afk')}\n"
            f"✍️ امضا: {on('signature')}\n"
            f"🗑 حذف خودکار: {on('auto_delete')}\n"
            f"⏰ تایم در اسم: {on('time_on')}\n\n"
            "💡 سایر بخش‌ها: اکشن‌ها / فرمت‌ها / قفل‌ها")

def actions_page_text(state):
    head = "🎭 <b>مدیریت اکشن‌های چت</b>" if state_online(state) else "⚠️ <b>سلف آفلاین است</b>"
    a = (state or {}).get("settings", {}).get("actions", {})
    def on(k): return "🟢" if a.get(k) else "🔴"
    return (head + "\n\n"
            f"⌨️ تایپ: {on('typing')}\n📤 آپلود عکس: {on('upload_photo')}\n"
            f"🎙 ضبط ویس: {on('record_audio')}\n🎮 بازی: {on('playing')}\n\n"
            "هنگام دریافت پیام، اکشن انتخابی به طرف مقابل نمایش داده می‌شود.")

def formats_page_text(state):
    head = "🎨 <b>فرمت خودکار پیام‌ها</b>" if state_online(state) else "⚠️ <b>سلف آفلاین است</b>"
    fm = (state or {}).get("settings", {}).get("formats", {})
    def on(k): return "🟢" if fm.get(k) else "🔴"
    return (head + "\n\n"
            f"🅱 بولد: {on('بولد')}\n🅸 ایتالیک: {on('ایتالیک')}\n🅄 زیر خط: {on('زیر خط')}\n"
            f"🅂 خط‌خورده: {on('خط‌ خورده')}\n🆂 اسپویلر: {on('اسپویلر')}\n🅲 کد: {on('کد')}\n\n"
            "هر فرمتی که 🟢 باشد روی پیام‌های عادی شما اعمال می‌شود.")

def locks_page_text(state):
    head = "🔒 <b>قفل‌های پیوی</b>" if state_online(state) else "⚠️ <b>سلف آفلاین است</b>"
    lk = (state or {}).get("settings", {}).get("locks", {})
    def on(k): return "🔒" if lk.get(k) else "🔓"
    return (head + "\n\n"
            f"همه: {on('همه')}\nمدیا: {on('مدیا')}\nاستیکر: {on('استیکر')}\n"
            f"فوروارد: {on('فوروارد')}\nویس: {on('ویس')}\nپیام: {on('پیام')}\nفایل: {on('فایل')}\n\n"
            "پیام‌های قفل‌شده در پیوی به‌صورت خودکار حذف می‌شوند.")

SUB_PAGES = {
    "live": (settings_page_text, get_live_keyboard),
    "actions": (actions_page_text, get_actions_keyboard),
    "formats": (formats_page_text, get_formats_keyboard),
    "locks": (locks_page_text, get_locks_keyboard),
}

# ==============================================================================
# هندلرها
# ==============================================================================
@app.on_message(filters.command("start") & filters.private)
async def show_menu(client, message):
    await message.reply_text(MAIN_TEXT, reply_markup=get_main_keyboard(message.from_user.id),
                             parse_mode=enums.ParseMode.HTML)

@app.on_inline_query()
async def inline_query_handler(client, inline_query):
    q = inline_query.query.strip().lower()
    uid = inline_query.from_user.id
    if q == "panel":
        # بنر (عکس پروفایل + اسم) فقط برای صاحب سلف ساخته می‌شود
        fid = None
        state = load_self_state()
        if HAS_CACHED_PHOTO and state_online(state) and (state.get("account", {}).get("id") == uid):
            fid = await get_banner_file_id(client, uid, state)
        if fid:
            results = [InlineQueryResultCachedPhoto(
                id="1", photo_file_id=fid, title="🎛 پنل مدیریت سلف",
                description="حساب کاربری + تنظیمات کامل سلف",
                caption=MAIN_TEXT, parse_mode=enums.ParseMode.HTML,
                reply_markup=get_main_keyboard(uid))]
        else:
            results = [InlineQueryResultArticle(
                id="1", title="🎛 پنل مدیریت سلف",
                description="حساب کاربری + تنظیمات کامل سلف",
                input_message_content=InputTextMessageContent(MAIN_TEXT, parse_mode=enums.ParseMode.HTML),
                reply_markup=get_main_keyboard(uid))]
        await inline_query.answer(results, cache_time=5, is_personal=True)
    elif q == "settings":
        results = [InlineQueryResultArticle(
            id="2", title="⚙️ تنظیمات سلف — پنل دستورات",
            description="همه بخش‌ها و دستورات سلف",
            input_message_content=InputTextMessageContent(CATS_TEXT, parse_mode=enums.ParseMode.HTML),
            reply_markup=get_categories_keyboard(uid))]
        await inline_query.answer(results, cache_time=5, is_personal=True)
    else:
        await inline_query.answer([], cache_time=5)

@app.on_callback_query()
async def callback_query_handler(client, cq):
    data = cq.data or ""
    parts = data.split(":")
    if len(parts) < 3 or parts[0] != "p" or parts[2] != str(cq.from_user.id):
        await cq.answer("⛔ دسترسی ندارید!", show_alert=True)
        return
    action = parts[1]
    uid = int(parts[2])
    arg = parts[3] if len(parts) > 3 else ""
    extra = parts[4] if len(parts) > 4 else ""

    if action == "close":
        try:
            await edit_view(client, cq,
                "✅ <b>پنل بسته شد</b>\n\n💡 برای باز کردن: <code>/start</code>",
                InlineKeyboardMarkup([[btn("🔄 بازکردن پنل", f"p:home:{uid}", S("s"))]]))
        except Exception:
            pass
        await cq.answer()
        return

    if action in ("home", "reopen"):
        await edit_view(client, cq, MAIN_TEXT, get_main_keyboard(uid))
        await cq.answer()
        return

    if action == "back":
        target = arg if arg in ("cats", "home", "live") else "cats"
        if target == "home":
            await edit_view(client, cq, MAIN_TEXT, get_main_keyboard(uid))
        elif target == "live":
            st = load_self_state()
            await edit_view(client, cq, settings_page_text(st), get_live_keyboard(uid, st))
        else:
            await edit_view(client, cq, CATS_TEXT, get_categories_keyboard(uid))
        await cq.answer()
        return

    if action == "cats":
        await edit_view(client, cq, CATS_TEXT, get_categories_keyboard(uid))
        await cq.answer()
        return

    if action == "cat":
        t = CAT_TEXTS.get(arg)
        if t:
            await edit_view(client, cq, t, get_back_keyboard(uid, "cats"))
            await cq.answer()
        else:
            await cq.answer("این بخش آماده نیست!", show_alert=True)
        return

    if action == "account":
        st = load_self_state()
        await edit_view(client, cq, build_account_text(st), get_account_keyboard(uid))
        await cq.answer()
        return

    if action in SUB_PAGES:
        st = load_self_state()
        text_fn, kb_fn = SUB_PAGES[action]
        await edit_view(client, cq, text_fn(st), kb_fn(uid, st))
        await cq.answer()
        return

    if action == "tg":
        key = arg
        queue_action(uid, TOGGLE_MAP.get(key, key))
        await cq.answer("✅ در حال اعمال روی سلف...")
        await asyncio.sleep(1.2)
        st = load_self_state()
        parent = extra if extra in SUB_PAGES else "live"
        text_fn, kb_fn = SUB_PAGES[parent]
        try:
            await edit_view(client, cq, text_fn(st), kb_fn(uid, st))
        except Exception:
            pass
        return

    await cq.answer("داده نامعتبر!", show_alert=True)

if __name__ == "__main__":
    print("🤖 ربات هلپر (Pyrogram) اجرا شد — پنل شاهکار v7.0")
    app.run()
