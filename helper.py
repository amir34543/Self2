# ==============================================================================
#  ربات هلپر و پنل مدیریت — Persian Gulf Self
#  نسخه: 7.0.0 «شاهکار» — حساب کاربری + تنظیمات کامل سلف + بنر عکس/اسم
# ==============================================================================

from pyrogram import Client, enums, filters
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                            InlineQueryResultArticle, InputTextMessageContent)
import logging, asyncio, json, os, time
from html import escape

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
TOKEN = os.environ.get("HELPER_BOT_TOKEN") or "8895709305:AAEUAYHr1nKKk46wpQaAzC98mWa3ChKUfis"
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
    # نام‌های state که دکمه‌های «تنظیمات زنده» استفاده می‌کنند (قبلاً نگاشت نداشتند و اعمال نمی‌شدند)
    "always_online": "toggle_online", "tag_logger": "toggle_taglogger",
    "anti_login": "toggle_antilogin", "auto_delete": "toggle_autodel",
    "upload_photo": "action_photo", "record_audio": "action_voice", "playing": "action_game",
    "time_on": "toggle_time",
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
    ts = time.time()
    items.append({"user_id": user_id, "action": action, "ts": ts})
    tmp = ACTIONS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)
    os.replace(tmp, ACTIONS_FILE)
    return ts

def state_online(state):
    return bool(state) and (time.time() - state.get("updated", 0)) < 90

async def wait_for_action(ts, timeout=4.0):
    """صبر می‌کند تا سلف دستور را اجرا کند و state تازه بنویسد (حداکثر چند ثانیه)"""
    end = time.time() + timeout
    while time.time() < end:
        st = load_self_state()
        if st and st.get("last_action_ts", 0) >= ts:
            return st
        await asyncio.sleep(0.2)
    return load_self_state()

# ------------------------- بنر پنل (عکس + اسم) -------------------------
# self.py بنر را به همین ربات (پیوی) می‌فرستد؛ هلپر file_id را ذخیره می‌کند
# و موقع باز شدن پنل بدون هیچ آپلودی از آن استفاده می‌کند (سریع و بدون تاخیر)
BRAND = "Persian Gulf Self"
BRAND_FOOTER = "\n\n💎 <i>" + BRAND + "</i>"
def brand(text): return text + BRAND_FOOTER

BANNER_FID_FILE = "panel_banner_fid.json"
_banner = {"fid": None, "owner": None, "sig": None}

def load_banner_cache():
    try:
        if os.path.exists(BANNER_FID_FILE):
            with open(BANNER_FID_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                _banner.update({k: d.get(k) for k in ("fid", "owner", "sig")})
    except Exception:
        pass

def save_banner_cache():
    try:
        tmp = BANNER_FID_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_banner, f)
        os.replace(tmp, BANNER_FID_FILE)
    except Exception:
        pass

load_banner_cache()

class CachedPhotoResult:
    """نتیجه اینلاین عکس با file_id — مستقل از نسخه/فورک Pyrogram (مستقیم با raw)"""
    def __init__(self, id, photo_file_id, caption, reply_markup=None):
        self.id = id
        self.photo_file_id = photo_file_id
        self.caption = caption
        self.reply_markup = reply_markup

    async def write(self, client):
        import inspect
        from pyrogram import raw
        from pyrogram.file_id import FileId
        f = FileId.decode(self.photo_file_id)
        photo = raw.types.InputPhoto(id=f.media_id, access_hash=f.access_hash,
                                     file_reference=f.file_reference)
        parsed = await client.parser.parse(self.caption, enums.ParseMode.HTML)
        rm = None
        if self.reply_markup:
            rm = self.reply_markup.write(client)
            if inspect.isawaitable(rm):
                rm = await rm
        return raw.types.InputBotInlineResultPhoto(
            id=self.id, type="photo", photo=photo,
            send_message=raw.types.InputBotInlineMessageMediaAuto(
                message=parsed["message"], entities=parsed.get("entities") or None,
                reply_markup=rm))

async def edit_view(client, cq, text, kb):
    """ویرایش پیام پنل؛ هم برای پیام متنی و هم برای پیام عکس‌دار (کپشن)"""
    text = brand(text)
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
        ("⏰ ساعت نام", "clock"), ("📥 دانلودر", "downloader"),
    ]
    rows = [[btn("⚡ تنظیمات زنده سلف", f"p:live:{uid}", S("s"))]]
    for i in range(0, len(c), 2):
        pair = c[i:i+2]
        rows.append([btn(t, f"p:cat:{uid}:{k}", S("p")) for t, k in pair])
    rows.append([btn("🎭 اکشن‌های چت", f"p:cat:{uid}:extra", S("s"))])
    rows += nav_rows(uid, 1)
    return InlineKeyboardMarkup(rows)


# ==============================================================================
# صفحه‌بندی پنل: صفحه ۱ (دسته‌های اصلی) / صفحه ۲ / صفحه ۳ (قابلیت‌های تازه)
# ==============================================================================
PAGE_NAMES = {1: "صفحه اول", 2: "صفحه دوم", 3: "صفحه سوم"}

def nav_rows(uid, page):
    """ردیف صفحه‌ها: [◀ قبلی] [• فعلی •] [بعدی ▶] و زیرش خانه/بستن پنل"""
    row = []
    if page > 1:
        row.append(btn(f"◀ {PAGE_NAMES[page - 1]}", f"p:pg:{uid}:{page - 1}", S("p")))
    row.append(btn(f"• {PAGE_NAMES[page]} •", f"p:pg:{uid}:{page}", S("s")))
    if page < 3:
        row.append(btn(f"{PAGE_NAMES[page + 1]} ▶", f"p:pg:{uid}:{page + 1}", S("p")))
    return [row, [btn("🏠 خانه", f"p:home:{uid}", S("p")), btn("❌ بستن پنل", f"p:close:{uid}", S("d"))]]

# چیدمان صفحه ۲ و ۳ مثل پنل مرجع: ردیف‌های دوتایی و تکی به‌صورت یک‌درمیان
PAGE_GRIDS = {
    2: [[("🔍 سرچ", "search"), ("🎲 تقلب", "cheat")],
        [("📸 اسکرین", "screenshot")],
        [("💬 کامنت اول", "firstcomment"), ("🚫 فیلتر کلمات", "wfilter")],
        [("📌 عضویت اجباری پیوی", "forcejoin")],
        [("📰 منشی", "secretary"), ("🏷 تگ", "tagall")],
        [("🗑 حذف", "delete"), ("ℹ️ اطلاعات", "info")],
        [("🤝 دوست", "friend"), ("📝 میمو", "memo")]],
    3: [[("🕵️ کپی پروفایل", "copyprofile"), ("🛡 نگهبان چت", "guard")],
        [("🎨 لوگو", "logo")],
        [("📝 محتوا", "content"), ("👁 سین خودکار", "autoseen")],
        [("🎬 انیمیشن", "anim")],
        [("⭐ استارزی", "stars"), ("💎 موجودی", "balance")],
        [("😍 ایموجی پریمیوم", "premoji"), ("🎥 ساخت ویدیو گرد", "roundvid")],
        [("⏳ ذخیره تایمدار", "timedsave")]],
}
# هر بخش به کدام صفحه برمی‌گردد (پیش‌فرض: صفحه ۱)
CAT_PAGE = {k: pg for pg, grid in PAGE_GRIDS.items() for row in grid for _, k in row}
CAT_PAGE.setdefault("clock", 1)
CAT_PAGE.setdefault("downloader", 1)
# صفحه‌هایی که باید به یک دسته برگردند (نه به شماره صفحه) — زیرصفحه‌های فونت
CAT_BACK_TO_CAT = {"fontclock": "clock", "fonttext": "clock"}

def get_page_keyboard(uid, page):
    if page == 1:
        return get_categories_keyboard(uid)
    rows = [[btn(t, f"p:cat:{uid}:{k}", S("p")) for t, k in row] for row in PAGE_GRIDS[page]]
    rows += nav_rows(uid, page)
    return InlineKeyboardMarkup(rows)

def page_view(uid, page):
    text = {1: CATS_TEXT, 2: PAGE2_TEXT, 3: PAGE3_TEXT}[page]
    return text, get_page_keyboard(uid, page)

def get_back_keyboard(uid, target="cats"):
    return InlineKeyboardMarkup([[btn("🔙 بازگشت", f"p:back:{uid}:{target}", S("p"))]])

def get_live_keyboard(uid, state):
    s = (state or {}).get("settings", {})
    def sw(key, label):
        on = bool(s.get(key))
        return [[btn(("✅ " if on else "☐ ") + label, f"p:tg:{uid}:{key}:live", style_on(on))]]
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
        return [[btn(("✅ " if on else "☐ ") + label, f"p:tg:{uid}:{ck}:actions", style_on(on))]]
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
        return [[btn(("✅ " if on else "☐ ") + label, f"p:tg:{uid}:{ck}:formats", style_on(on))]]
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
        return [[btn(("🔒 " if on else "🔓 ") + label, f"p:tg:{uid}:{ck}:locks", style_on(on))]]
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
MAIN_TEXT = ("🎛 <b>پنل مدیریت سلف Persian Gulf</b>\n\n"
             "👇 از دکمه‌های زیر استفاده کنید:\n"
             "• 👤 <b>حساب کاربری</b> — اطلاعات زنده اکانت شما\n"
             "• ⚙️ <b>تنظیمات سلف</b> — همه دستورات و تنظیمات")

CATS_TEXT = ("🤖 <b>Persian Gulf Self — پنل دستورات</b>\n\n"
             "💡 روی هر بخش بزنید تا دستوراتش باز شود\n"
             "📋 دستورات را کپی کنید و در چت خودتان بفرستید\n"
             "📄 <b>صفحه اول از ۳</b>")

PAGE2_TEXT = ("🤖 <b>Persian Gulf Self — قابلیت‌های تازه</b>\n\n"
              "💡 روی هر بخش بزنید تا دستوراتش باز شود\n"
              "📄 <b>صفحه دوم از ۳</b>")

PAGE3_TEXT = ("🤖 <b>Persian Gulf Self — قابلیت‌های تازه</b>\n\n"
              "💡 روی هر بخش بزنید تا دستوراتش باز شود\n"
              "📄 <b>صفحه سوم از ۳</b>")

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
👇 برای دانلودر اینستاگرام/تیک‌تاک/یوتیوب به بخش «📥 دانلودر» مراجعه کنید""",

"downloader": """📥 <b>دانلودر</b>

<b>دستورات قابل کپی:</b>
<code>اینستا لینک</code> — دانلود پست/ریلز اینستاگرام
مثال: <code>اینستا https://www.instagram.com/p/xxxx</code>

<code>تیکتاک لینک</code> — دانلود ویدیوی تیک‌تاک بدون واترمارک
مثال: <code>تیکتاک https://www.tiktok.com/@user/video/xxxx</code>

<code>یوتیوب لینک</code> — دانلود ویدیوی یوتیوب (تا ۲۰ دقیقه)
مثال: <code>یوتیوب https://youtu.be/xxxx</code>

⚠️ این دستورات مستقیماً داخل چت با خود سلف تایپ می‌شوند و فایل برای شما ارسال خواهد شد.""",

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
<code>فرمت وضعیت</code> / <code>فرمت ریست</code>""",

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
<code>شنود روشن</code> / <code>شنود خاموش</code> — اطلاع تگ شدن""",

"edit": """✏️ <b>ویرایش سریع</b>

<b>دستور قابل کپی:</b>
<code>ویرایش کلمه_قدیم به کلمه_جدید</code> (ریپلای روی پیام)

مثال: <code>ویرایش سلان به سلام</code>""",

"extra": """🎭 <b>اکشن‌های چت</b>

وقتی پیامی دریافت می‌کنید، اکشن انتخابی (تایپ، آپلود عکس، ضبط ویس، بازی) به طرف مقابل نمایش داده می‌شود.""",
}


CAT_TEXTS.update({
"search": """🔍 <b>سرچ</b>

<b>دستور قابل کپی:</b>
<code>سرچ عبارت</code> — جستجو در ویکی‌پدیا (فارسی، سپس انگلیسی) و ارسال خلاصه + لینک

مثال: <code>سرچ خلیج فارس</code>""",

"cheat": """🎲 <b>تقلب در بازی‌ها</b>

<b>دستورات قابل کپی:</b>
<code>تقلب تاس 6</code>
<code>تقلب دارت 6</code>
<code>تقلب بولینگ 6</code>
<code>تقلب بسکتبال 5</code>
<code>تقلب فوتبال 5</code>
<code>تقلب اسلات 64</code>

آنقدر ایموجی بازی می‌فرستد تا عدد دلخواه بیاید (حداکثر ۴۰ تلاش) و بقیه پاک می‌شوند""",

"screenshot": """📸 <b>اسکرین</b>

<b>دستور قابل کپی:</b>
<code>اسکرین example.com</code> — گرفتن اسکرین‌شات از یک سایت و ارسال عکس آن""",

"firstcomment": """💬 <b>کامنت اول</b>

<b>دستورات قابل کپی:</b>
<code>کامنت اول متن سلام، عالی بود</code> — متن کامنت
<code>کامنت اول افزودن @channel</code> — کانال هدف
<code>کامنت اول حذف @channel</code>
<code>کامنت اول لیست</code>
<code>کامنت اول روشن</code> / <code>کامنت اول خاموش</code>

با هر پست جدید کانال‌های لیست، اولین کامنت را می‌گذارد (باید عضو کانال باشید)""",

"wfilter": """🚫 <b>فیلتر کلمات</b>

<b>دستورات قابل کپی:</b>
<code>فیلتر افزودن کلمه</code>
<code>فیلتر حذف کلمه</code>
<code>فیلتر لیست</code> / <code>فیلتر پاکسازی</code>
<code>فیلتر روشن</code> / <code>فیلتر خاموش</code>
<code>فیلتر پیوی روشن</code> / <code>فیلتر پیوی خاموش</code>
<code>فیلتر گروه روشن</code> / <code>فیلتر گروه خاموش</code>

پیام‌های دریافتی شامل این کلمات در <b>پیوی</b> (حذف دو طرفه) و <b>گروه‌ها</b> (نیاز به دسترسی حذف) پاک می‌شوند؛ پیام ویرایش‌شده هم بررسی می‌شود""",

"forcejoin": """📌 <b>عضویت اجباری پیوی</b>

<b>دستورات قابل کپی:</b>
<code>عضویت اجباری کانال @channel</code>
<code>عضویت اجباری روشن</code> / <code>عضویت اجباری خاموش</code>

کسی که عضو کانال نباشد و در پیوی به شما پیام بدهد، پیامش حذف می‌شود و اعلان عضویت می‌گیرد (مخاطبین معاف‌اند)
⚠️ حساب شما باید ادمین آن کانال باشد""",

"secretary": """📰 <b>منشی</b>

<b>دستورات قابل کپی:</b>
<code>منشی متن سلام، بعداً پاسخ می‌دهم</code>
<code>منشی وضعیت</code>
<code>منشی روشن</code> / <code>منشی خاموش</code>

به اولین پیام هر نفر در پیوی پاسخ می‌دهد (هر ۶ ساعت یک‌بار برای هر نفر)""",

"tagall": """🏷 <b>تگ</b>

<b>دستورات قابل کپی:</b>
<code>تگ</code> — تگ اعضای گروه
<code>تگ متن دلخواه</code> — تگ با متن

حداکثر ۱۰۰ عضو، هر ۵ نفر در یک پیام (فقط داخل گروه)""",

"delete": """🗑 <b>حذف</b>

<b>دستورات قابل کپی:</b>
<code>حذف</code> — ریپلای روی یک پیام: همان پیام حذف می‌شود
<code>حذف پیام 20</code> — حذف ۲۰ پیام آخر خودتان
<code>حذف زمان‌دار 10</code> — حذف بعد از ۱۰ ثانیه""",

"info": """ℹ️ <b>اطلاعات</b>

<b>دستور قابل کپی:</b>
<code>اطلاعات</code> — اطلاعات خودتان یا کاربری که روی پیامش ریپلای کرده‌اید (همان دستور <code>ایدی</code>)""",

"friend": """🤝 <b>دوست</b>

<b>دستورات قابل کپی:</b>
<code>دوست</code> — افزودن (ریپلای)
<code>حذف دوست</code> (ریپلای)
<code>لیست دوست</code> / <code>دوستان</code>
<code>پاک کردن دوستان</code>

به پیام‌های دوستان ❤️ ریاکشن می‌دهد و گاهی جمله محبت‌آمیز می‌فرستد""",

"memo": """📝 <b>میمو</b>

<b>دستورات قابل کپی:</b>
<code>میمو متن یادداشت</code>
<code>میمو ها</code> — لیست
<code>میمو حذف شماره</code>

(همان یادداشت‌ها؛ هر دو نام کار می‌کنند)""",

"copyprofile": """🕵️ <b>کپی پروفایل</b>

<b>دستورات قابل کپی:</b>
<code>کپی پروفایل</code> — ریپلای روی پیام کاربر
<code>کپی پروفایل @user</code>
<code>بازگردانی پروفایل</code> — برگشت به پروفایل اصلی

نام، بیو و عکس کاربر را کپی می‌کند (پروفایل اصلی شما اول پشتیبان‌گیری می‌شود)""",

"guard": """🛡 <b>نگهبان چت</b>

<b>دستورات قابل کپی:</b>
<code>نگهبان روشن</code> / <code>نگهبان خاموش</code> — داخل گروه
<code>نگهبان پیوی روشن</code> / <code>نگهبان پیوی خاموش</code>
<code>نگهبان لینک روشن</code> / <code>نگهبان لینک خاموش</code>
<code>نگهبان وضعیت</code>

اسپم/فلود و (در صورت روشن بودن) لینک حذف می‌شود:
• در <b>گروه</b> از غیر ادمین‌ها (باید ادمین باشید)
• در <b>پیوی</b> از غیرمخاطبین، با حذف دو طرفه""",

"logo": """🎨 <b>لوگو</b>

<b>دستور قابل کپی:</b>
<code>لوگو Persian Gulf</code> — ساخت لوگوی طلایی از متن و ارسال به‌صورت عکس""",

"content": """📝 <b>محتوا</b>

<b>دستور قابل کپی:</b>
<code>محتوا</code> — ریپلای روی یک پیام: نوع، ابعاد، حجم، مدت و... را نشان می‌دهد""",

"autoseen": """👁 <b>سین خودکار</b>

<b>دستورات قابل کپی:</b>
<code>سین خودکار روشن</code> / <code>سین خودکار خاموش</code>

پیام‌های دریافتی خودکار «خوانده‌شده» می‌شوند""",

"anim": """🎬 <b>انیمیشن</b>

<b>دستورات قابل کپی:</b>
<code>انیمیشن متن دلخواه</code> — تایپ‌شونده
<code>انیمیشن ماه</code> / <code>قلب</code> / <code>ساعت</code> / <code>موج</code> / <code>آتش</code>""",

"stars": """⭐ <b>استارزی</b>

<b>دستور قابل کپی:</b>
<code>استارزی</code> — موجودی استارز تلگرام شما""",

"balance": """💎 <b>موجودی</b>

<b>دستور قابل کپی:</b>
<code>موجودی</code> — موجودی استارز و تون (TON) اکانت""",

"premoji": """😍 <b>ایموجی پریمیوم</b>

<b>دستورات قابل کپی:</b>
<code>ایموجی پریمیوم سلام ❤️🔥</code>
<code>ایموجی پریمیوم</code> — ریپلای روی یک پیام

ایموجی‌های متن را به ایموجی پریمیوم تبدیل می‌کند (فقط با اکانت پریمیوم)""",

"timedsave": """⏳ <b>ذخیره تایمدار</b>

<b>دستورات قابل کپی:</b>
<code>ذخیره تایمدار</code> — ریپلای روی عکس/ویدیو/ویس تایمدار
<code>ذخیره تایمدار روشن</code> / <code>ذخیره تایمدار خاموش</code> — ذخیره خودکار
<code>ذخیره تایمدار وضعیت</code>

عکس، ویدیو، ویس و ویدیو گرد تایمدار (خودتخریب‌شونده) به‌محض رسیدن در پیام‌های ذخیره‌شده ذخیره می‌شود
⚠️ بعد از باز شدن توسط شما، مدیا از تلگرام حذف می‌شود؛ پس حالت خودکار روشن بماند""",

"roundvid": """🎥 <b>ساخت ویدیو گرد</b>

<b>دستور قابل کپی:</b>
<code>ساخت ویدیو گرد</code> — ریپلای روی یک ویدیو یا گیف؛ به ویدیو گرد تلگرام تبدیل می‌شود (حداکثر ۶۰ ثانیه)""",
})

CAT_TEXTS.update({
"clock": """⏰ <b>ساعت نام</b>

نمایش ساعت به‌وقت تهران، کنار اسم شما در تلگرام (دائم به‌روزرسانی می‌شود)

<b>دستورات قابل کپی:</b>
<code>تایم روشن</code> / <code>تایم خاموش</code>
<code>ساعت نام روشن</code> / <code>ساعت نام خاموش</code> (دستور جایگزین، همان کار را می‌کند)
<code>لیست فونت</code> — پیش‌نمایش ۳۰ فونت ساعت
<code>تنظیم فونت 1</code> تا <code>تنظیم فونت 30</code>

ℹ️ همین قابلیت داخل بخش «🪄 پروفایل» هم هست؛ اینجا یک میان‌بر جداست""",

"fontclock": """🕐 <b>فونت‌های ساعت (۳۰ فونت)</b>

عدد فونت را با <code>تنظیم فونت شماره</code> ست کنید، مثلاً <code>تنظیم فونت 12</code>

1 - 𝟏𝟐:𝟑𝟒  (بولد)
2 - 𝟭𝟮:𝟯𝟰  (سنس‌بولد)
3 - １２:３４  (تمام‌عرض)
4 - 𝟣𝟤:𝟥𝟦  (سنس)
5 - 𝟙𝟚:𝟛𝟜  (دابل‌استراک)
6 - 12̴:̴34̴  (خط‌دار کلاسیک)
7 - 𝟷𝟸:𝟹𝟺  (مونو‌اسپیس)
8 - ¹²:³⁴  (بالانویس)
9 - ₁₂:₃₄  (پایین‌نویس)
10 - ①②:③④  (دایره‌ای)
11 - ❶❷:❸❹  (دایره پر)
12 - ⑴⑵:⑶⑷  (پرانتزی)
13 - ⒈⒉:⒊⒋  (نقطه‌دار)
14 - 1̲2̲:3̲4̲  (زیرخط)
15 - 1̳2̳:3̳4̳  (زیرخط دوبل)
16 - 1̶2̶:3̶4̶  (خط‌خورده)
17 - 1̅2̅:3̅4̅  (روخط)
18 - 1̿2̿:3̿4̿  (روخط دوبل)
19 - 1̃2̃:3̃4̃  (مواج)
20 - 1̂2̂:3̂4̂  (سقفی)
21 - 1̊2̊:3̊4̊  (حلقه‌دار)
22 - 1̇2̇:3̇4̇  (نقطه بالا)
23 - 1̣2̣:3̣4̣  (نقطه پایین)
24 - 1̄2̄:3̄4̄  (ماکرون)
25 - 1̱2̱:3̱4̱  (زیرخط ضخیم)
26 - 1̀2̀:3̀4̀  (گریو)
27 - 1́2́:3́4́  (آکوت)
28 - 1̈2̈:3̈4̈  (دیارز)
29 - 1̆2̆:3̆4̆  (بروه)
30 - 1̌2̌:3̌4̌  (کارون)""",

"fonttext": """🔤 <b>فونت‌های متن (۳۰ فونت)</b>

با <code>قلم شماره متن</code> استفاده کنید، مثلاً <code>قلم 9 سلام</code>

1. ꧁ 𝗣𝗲𝗿𝘀𝗶𝗮𝗻 ꧂
2. ✦ 𝘗𝘦𝘳𝘴𝘪𝘢𝘯 ✦
3. ༺ ℙ𝕖𝕣𝕤𝕚𝕒𝕟 ༻
4. 「 ᴘᴇʀsɪᴀɴ 」
5. ★ Ⓟⓔⓡⓢⓘⓐⓝ ★
6. 『 𝕻𝖊𝖗𝖘𝖎𝖆𝖓 』
7. ◈ 𝙋𝙚𝙧𝙨𝙞𝙖𝙣 ◈
8. ♦ 𝙿𝚎𝚛𝚜𝚒𝚊𝚗 ♦
9. ☾ 𝖯𝖾𝗋𝗌𝗂𝖺𝗇 ☽
10. ▧ 𝐏𝐞𝐫𝐬𝐢𝐚𝐧 ▧
11. ▣ 𝑃𝑒𝑟𝑠𝑖𝑎𝑛 ▣
12. ❖ 𝑷𝒆𝒓𝒔𝒊𝒂𝒏 ❖
13. ⟡ 𝒫ℯ𝓇𝓈𝒾𝒶𝓃 ⟡
14. ꒰ 𝓟𝓮𝓻𝓼𝓲𝓪𝓷 ꒱
15. ⚡ 𝔓𝔢𝔯𝔰𝔦𝔞𝔫 ⚡
16. 🔥 Ｐｅｒｓｉａｎ 🔥
17. ❁ P̲e̲r̲s̲i̲a̲n̲ ❁
18. ☆ P̳e̳r̳s̳i̳a̳n̳ ☆
19. ⌈ P̶e̶r̶s̶i̶a̶n̶ ⌉
20. » P̅e̅r̅s̅i̅a̅n̅ «
21. ⊰ P̃ẽr̃s̃ĩãñ ⊱
22. ◇ P̂êr̂ŝîân̂ ◇
23. ✧ P̊e̊r̊s̊i̊ån̊ ✧
24. ⋆ Ṗėṙṡi̇ȧṅ ⋆
25. ⟦ P̣ẹṛṣịạṇ ⟧
26. ☙ P̄ēr̄s̄īān̄ ❧
27. ➤ P̀èr̀s̀ìàǹ ➤
28. ⁘ Ṕéŕśíáń ⁘
29. ✵ P̈ër̈s̈ïän̈ ✵
30. ꧁P̆ĕr̆s̆ĭăn̆꧂""",
})

# ==============================================================================
# دکمه‌های شیشه‌ای (روشن/خاموش سریع) زیر دستورات هر بخش
# هر مورد: (برچسب، گروه در state، کلید در state، نام اکشن)
# ==============================================================================
GLASS = {
    "format": {"items": [
        ("بولد", "formats", "بولد", "format_bold"),
        ("ایتالیک", "formats", "ایتالیک", "format_italic"),
        ("زیر خط", "formats", "زیر خط", "format_underline"),
        ("خط‌خورده", "formats", "خط‌ خورده", "format_strike"),
        ("اسپویلر", "formats", "اسپویلر", "format_spoiler"),
        ("کد", "formats", "کد", "format_code")],
        "reset": ("format_reset", "🟢 ریست فرمت‌ها")},
    "lock": {"items": [
        ("همه", "locks", "همه", "lock_all"), ("مدیا", "locks", "مدیا", "lock_media"),
        ("استیکر", "locks", "استیکر", "lock_sticker"), ("فوروارد", "locks", "فوروارد", "lock_forward"),
        ("ویس", "locks", "ویس", "lock_voice"), ("پیام", "locks", "پیام", "lock_text"),
        ("فایل", "locks", "فایل", "lock_file")],
        "reset": ("lock_reset", "🟢 ریست قفل‌ها")},
    "protect": {"items": [
        ("آنلاین همیشگی", None, "always_online", "toggle_online"),
        ("شنود تگ", None, "tag_logger", "toggle_taglogger"),
        ("انتی‌لاگین", None, "anti_login", "toggle_antilogin")]},
    "afk": {"items": [
        ("حالت AFK", None, "afk", "toggle_afk"),
        ("امضای خودکار (منش)", None, "signature", "toggle_signature")]},
    "autodel": {"items": [
        ("حذف خودکار پیام‌ها", None, "auto_delete", "toggle_autodel")]},
    "profile": {"items": [
        ("ساعت در اسم", None, "time_on", "toggle_time")]},
    "clock": {"items": [("ساعت در اسم", None, "time_on", "toggle_time")]},
    "firstcomment": {"items": [("کامنت اول", None, "firstcomment_on", "toggle_firstcomment")]},
    "wfilter": {"items": [("فیلتر کلمات", None, "filter_on", "toggle_filter"),
                          ("پیوی", None, "filter_pv", "toggle_filterpv"),
                          ("گروه", None, "filter_groups", "toggle_filtergroups")]},
    "forcejoin": {"items": [("عضویت اجباری", None, "forcejoin_on", "toggle_forcejoin")]},
    "secretary": {"items": [("منشی", None, "secretary_on", "toggle_secretary")]},
    "guard": {"items": [("نگهبان گروه", None, "guard_on", "toggle_guard"),
                        ("نگهبان پیوی", None, "guard_pv", "toggle_guardpv"),
                        ("حذف لینک", None, "guard_links", "toggle_guardlinks")]},
    "timedsave": {"items": [("ذخیره تایمدار", None, "timed_save_on", "toggle_timedsave")]},
    "autoseen": {"items": [("سین خودکار", None, "seen_on", "toggle_seen")]},
    "extra": {"items": [
        ("تایپ", "actions", "typing", "action_typing"),
        ("آپلود عکس", "actions", "upload_photo", "action_photo"),
        ("ضبط ویس", "actions", "record_audio", "action_voice"),
        ("بازی", "actions", "playing", "action_game")],
        "reset": ("action_reset", "🔴 ریست اکشن‌ها")},
}
GLASS_HEADER = "\n\n👇 <b>روشن/خاموش سریع</b> (✅ روشن ❌ خاموش):"

def _glass_on(state, group, key):
    s = (state or {}).get("settings", {})
    if group:
        s = s.get(group, {})
    return bool(s.get(key))

def _glass_rows(uid, cat, state):
    """ردیف‌های دکمه‌های روشن/خاموش (بدون ردیف بازگشت)"""
    cfg = GLASS[cat]
    rows, row = [], []
    for label, group, key, action in cfg["items"]:
        on = _glass_on(state, group, key)
        row.append(btn(f"{label} {'✅' if on else '❌'}", f"p:tg:{uid}:{action}:c_{cat}", style_on(on)))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    if cfg.get("reset"):
        rows.append([btn(cfg["reset"][1], f"p:tg:{uid}:{cfg['reset'][0]}:c_{cat}", S("d"))])
    return rows

def get_glass_keyboard(uid, cat, state):
    rows = _glass_rows(uid, cat, state)
    rows.append([btn("🔙 بازگشت به پنل", f"p:pg:{uid}:{CAT_PAGE.get(cat, 1)}", S("p"))])
    return InlineKeyboardMarkup(rows)

CAT_EXTRA_NAV = {"clock": [("🕐 فونت ساعت", "fontclock"), ("🔤 فونت متن", "fonttext")]}

def _back_button(uid, cat):
    if cat in CAT_BACK_TO_CAT:
        return btn("🔙 بازگشت", f"p:cat:{uid}:{CAT_BACK_TO_CAT[cat]}", S("p"))
    return btn("🔙 بازگشت", f"p:pg:{uid}:{CAT_PAGE.get(cat, 1)}", S("p"))

def cat_view(uid, cat, state):
    """(متن، کیبورد) صفحه یک بخش؛ اگر دکمه شیشه‌ای دارد زیر دستورات می‌آید"""
    text = CAT_TEXTS.get(cat)
    if text is None:
        return None, None
    if cat in GLASS:
        rows = _glass_rows(uid, cat, state)   # قبلاً kb.rows بود که در Pyrogram وجود ندارد و کرش می‌کرد
        for label, target in CAT_EXTRA_NAV.get(cat, []):
            rows.append([btn(label, f"p:cat:{uid}:{target}", S("p"))])
        rows.append([_back_button(uid, cat)])
        return text + GLASS_HEADER, InlineKeyboardMarkup(rows)
    return text, InlineKeyboardMarkup([[_back_button(uid, cat)]])

def build_account_text(state):
    if not state_online(state):
        return ("⚠️ <b>سلف آفلاین است</b>\n\n"
                "ربات سلف (<code>self.py</code>) روشن نیست یا هنوز وضعیتی ارسال نکرده.\n"
                "هر دو فایل باید در <b>یک پوشه</b> اجرا شوند.")
    acc = state.get("account", {})
    s = state.get("settings", {})
    name = ((acc.get("first_name") or "") + " " + (acc.get("last_name") or "")).strip() or "—"
    lines = [
        "👤 <b>حساب کاربری — Persian Gulf Self</b>", "",
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
        head = "⚡ <b>تنظیمات زنده Persian Gulf Self</b>\n<i>روی دکمه‌ها بزنید تا فوراً روی اکانت اعمال شود</i>"
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
    await message.reply_text(brand(MAIN_TEXT), reply_markup=get_main_keyboard(message.from_user.id),
                             parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.private & filters.photo)
async def banner_receiver(client, message):
    """دریافت بنر از self.py (فقط از خود اکانت سلف پذیرفته می‌شود)"""
    cap = message.caption or ""
    if not cap.startswith("PANELBANNER|") or not message.from_user:
        return
    st = load_self_state()
    owner = ((st or {}).get("account") or {}).get("id")
    if not owner or message.from_user.id != owner:
        logging.warning("🖼 بنر رد شد: فرستنده مجاز نیست یا وضعیت سلف موجود نیست")
        return
    _banner.update(fid=message.photo.file_id, owner=owner, sig=cap.split("|", 1)[1])
    save_banner_cache()
    logging.info("🖼 بنر پنل دریافت و ذخیره شد")
    try: await message.delete()
    except Exception: pass

@app.on_inline_query()
async def inline_query_handler(client, inline_query):
    q = inline_query.query.strip().lower()
    uid = inline_query.from_user.id
    if q == "panel":
        article = InlineQueryResultArticle(
            id="1", title="🎛 پنل مدیریت Persian Gulf Self",
            description="حساب کاربری + تنظیمات کامل سلف",
            input_message_content=InputTextMessageContent(brand(MAIN_TEXT), parse_mode=enums.ParseMode.HTML),
            reply_markup=get_main_keyboard(uid))
        fid = _banner["fid"] if _banner.get("owner") == uid else None
        if fid:
            try:
                await inline_query.answer(
                    [CachedPhotoResult("1", fid, brand(MAIN_TEXT), get_main_keyboard(uid))],
                    cache_time=5, is_personal=True)
                return
            except Exception as e:
                logging.warning(f"پنل عکس‌دار ناموفق بود، پنل متنی ارسال می‌شود: {e!r}")
        else:
            logging.info("بنر هنوز آماده نیست (یا کاربر مالک نیست)؛ پنل متنی ارسال شد")
        await inline_query.answer([article], cache_time=5, is_personal=True)
    elif q == "settings":
        results = [InlineQueryResultArticle(
            id="2", title="⚙️ Persian Gulf Self — پنل دستورات",
            description="همه بخش‌ها و دستورات سلف",
            input_message_content=InputTextMessageContent(brand(CATS_TEXT), parse_mode=enums.ParseMode.HTML),
            reply_markup=get_categories_keyboard(uid))]
        await inline_query.answer(results, cache_time=5, is_personal=True)
    else:
        await inline_query.answer([], cache_time=5)

@app.on_callback_query()
async def callback_query_handler(client, cq):
    try:
        await _callback_query_handler(client, cq)
    except Exception as e:
        logging.exception("خطا در هندلر دکمه‌ها")
        try: await cq.answer(f"⚠️ خطا: {str(e)[:150]}", show_alert=True)
        except Exception: pass

async def _callback_query_handler(client, cq):
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

    if action in ("cats", "pg"):
        page = 1
        if action == "pg" and arg.isdigit() and 1 <= int(arg) <= 3:
            page = int(arg)
        text, kb = page_view(uid, page)
        await edit_view(client, cq, text, kb)
        await cq.answer()
        return

    if action == "cat":
        t, kb = cat_view(uid, arg, load_self_state())
        if t:
            await edit_view(client, cq, t, kb)
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
        st0 = load_self_state()
        owner = ((st0 or {}).get("account") or {}).get("id")
        if owner and owner != uid:
            await cq.answer("⛔ این پنل فقط برای صاحب سلف است", show_alert=True)
            return
        ts = queue_action(uid, TOGGLE_MAP.get(arg, arg))
        await cq.answer("✅ در حال اعمال روی سلف...")
        st = await wait_for_action(ts) if state_online(st0) else load_self_state()
        try:
            if extra.startswith("c_"):
                t, kb = cat_view(uid, extra[2:], st)
                if t:
                    await edit_view(client, cq, t, kb)
            else:
                parent = extra if extra in SUB_PAGES else "live"
                text_fn, kb_fn = SUB_PAGES[parent]
                await edit_view(client, cq, text_fn(st), kb_fn(uid, st))
        except Exception:
            pass
        return

    await cq.answer("داده نامعتبر!", show_alert=True)

if __name__ == "__main__":
    print("🤖 ربات هلپر Persian Gulf Self (Pyrogram) اجرا شد — پنل شاهکار v7.0")
    app.run()
