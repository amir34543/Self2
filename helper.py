# ==============================================================================
# ربات هلپر و مدیریت پنل سلف بات (PersianGulf Helper Bot)
# نسخه: 6.0.0 - پنل پیشرفته: حساب کاربری + تنظیمات زنده سلف (دکمه واقعی)
# ==============================================================================

from pyrogram import Client
from pyrogram import enums
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.types import InlineKeyboardButton
from pyrogram.types import InlineQueryResultArticle
from pyrogram.types import InputTextMessageContent
from pyrogram.types import KeyboardButtonStyle
import logging

# ==============================================================================
# تنظیمات ربات هلپر
# ==============================================================================

TOKEN = "8895709305:AAEUAYHr1nKKk46wpQaAzC98mWa3ChKUfis" # توکن ربات هلپر
API_ID = 35656061
API_HASH = "b37f2596516bc0439bf505d1d230395c"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client("helper_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

# ==============================================================================
# متون راهنمای پنل (HELP_TEXTS)
# ==============================================================================

HELP_TEXTS = {
    "time": """
⏰ <b>مدیریت تایم</b>

<b>دستورات قابل کپی:</b>
<code>تایم روشن</code>
<code>تایم خاموش</code>

<b>کاربرد:</b>
نمایش زمان کنار نام کاربری
آپدیت خودکار هر دقیقه
فونت‌های مختلف برای زمان

<b>فونت‌های موجود:</b>
𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗 - فونت 1
𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵 - فونت 2  
０１２３４５６７８９ - فونت 3
𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫 - فونت 4
𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡 - فونت 5
0҉1҉2҉3҉4҉5҉6҉7҉8҉9҉ - فونت 6
""",

    "instagram": """
📥 <b>دانلودر اینستاگرام</b>

<b>دستور قابل کپی:</b>
<code>اینستا لینک_پست</code>

<b>مثال‌ها:</b>
<code>اینستا https://www.instagram.com/reel/DOkym3fCFqg/</code>
<code>اینستا https://www.instagram.com/p/CzuF4KQqJ7q/</code>

<b>کاربرد:</b>
• دانلود پست‌های اینستاگرام
• دانلود ریل‌ ها و ویدیو ها
• دانلود عکس‌های پست

<b>قابلیت‌ها:</b>
✅ دانلود با کیفیت اصلی
✅ نمایش توضیحات پست
✅ نمایش اطلاعات کاربر
✅ آپلود در همان چت
""",

    "id": """
🆔 <b>سیستم آیدی پیشرفته</b>

<b>دستور قابل کپی:</b>
<code>ایدی</code>

<b>دو حالت استفاده:</b>

1️⃣ <b>بدون ریپلای:</b>
<code>ایدی</code>
• نمایش اطلاعات خودتان
• نمایش اطلاعات چت فعلی
• نمایش آیدی عددی

2️⃣ <b>با ریپلای:</b>
<code>ایدی</code> (روی پیام کاربر ریپلای)
• نمایش اطلاعات کامل کاربر
• نمایش گروه‌های مشترک  
• نمایش آیدی و یوزرنیم

<b>اطلاعات نمایش داده شده:</b>
✅ آیدی عددی کاربر
✅ یوزرنیم و نام کامل
✅ وضعیت پریمیوم
✅ تعداد عکس‌های پروفایل
✅ آیدی چت و عنوان
✅ تعداد اعضا (در گروه)
✅ گروه‌های مشترک (در صورت وجود)
""",

    "photo": """
📸 <b>ذخیره عکس تایمدار</b>

<b>دستور قابل کپی:</b>
<code>عکس سیو</code> (ریپلای روی عکس)

<b>کاربرد:</b>
ذخیره دستی عکس‌های تایمدار
ارسال اطلاعات کامل کاربر

<b>نکته:</b>
فقط روی عکس‌های تایمدار کار می‌کند
عکس معمولی قابل ذخیره نیست
""",

    "backup": """
💾 <b>پشتیبان‌گیری</b>

<b>دستور قابل کپی:</b>
<code>سیو @یوزرنیم</code>

<b>مثال:</b>
<code>سیو @username</code>

<b>کاربرد:</b>
ذخیره تاریخچه چت در فایل متنی
ارسال فایل به پیام‌های ذخیره شده
""",

    "font": """
🔤 <b>مدیریت فونت</b>

<b>دستورات قابل کپی:</b>
<code>لیست فونت</code>
<code>تنظیم فونت 1</code> تا <code>تنظیم فونت 6</code>

<b>کاربرد:</b>
تغییر فونت نمایش زمان
پیش‌نمایش فونت‌های مختلف
اعمال فونت روی زمان به صورت زنده
""",

    "price": """
💱 <b>قیمت ارز</b>

<b>دستور قابل کپی:</b>
<code>قیمت ارز</code>

<b>مثال‌ها:</b>
<code>قیمت BTC</code>
<code>قیمت ETH</code>
<code>قیمت TON</code>

<b>کاربرد:</b>
نمایش قیمت لحظه‌ای ارزهای دیجیتال
نمایش قیمت تومانی و دلاری
نمایش تغییرات 24 ساعته
میتوانید اسم ارزو رو به فارسی بزارید
""",

    "spam": """
🔁 <b>ارسال اسپم</b>

<b>دستور قابل کپی:</b>
<code>اسپم تعداد متن</code>

<b>مثال‌ها:</b>
<code>اسپم 10 سلام</code>
<code>اسپم 5 تست</code>

<b>کاربرد:</b>
ارسال پیام تکراری
حداکثر 50 پیام در یک دستور
قابلیت ریپلای روی پیام
""",

    "format": """
🎨 <b>سیستم فرمت خودکار HTML</b>

<b>دستورات قابل کپی:</b>
<code>فرمت بولد روشن</code>
<code>فرمت بولد خاموش</code>
<code>فرمت ایتالیک روشن</code>
<code>فرمت ایتالیک خاموش</code>
<code>فرمت زیرخط روشن</code>
<code>فرمت زیرخط خاموش</code>
<code>فرمت خط‌خورده روشن</code>
<code>فرمت خط‌خورده خاموش</code>
<code>فرمت اسپویلر روشن</code>
<code>فرمت اسپویلر خاموش</code>
<code>فرمت کد روشن</code>
<code>فرمت کد خاموش</code>
<code>فرمت وضعیت</code>
<code>فرمت ریست</code>

<b>کاربرد:</b>
تبدیل خودکار پیام‌ ها به فرمت‌ های مختلف
پشتیبانی از تمام تگ‌های HTML تلگرام
امکان استفاده همزمان از چندین فرمت
""",

    "enemy": """
👿 <b>مدیریت دشمنان</b>

<b>دستورات قابل کپی:</b>
<code>دشمن</code> (ریپلای روی پیام کاربر)
<code>حذف دشمن</code> (ریپلای روی پیام کاربر)
<code>لیست دشمن</code>
<code>دشمنان</code>
<code>پاک کردن دشمنان</code>

<b>کاربرد:</b>
افزودن کاربر به لیست دشمنان
ارسال خودکار فحش رندوم به دشمنان
مدیریت لیست دشمنان
نمایش اطلاعات کامل دشمنان
حذف دشمن از لیست
""",

    "autoreply": """
🤖 <b>پاسخ خودکار</b>

<b>دستورات قابل کپی:</b>
<code>پاسخ افزودن سلام|سلام چطوری</code>
<code>پاسخ حذف سلام</code>
<code>پاسخ لیست</code>

<b>مثال‌ها:</b>
<code>پاسخ افزودن سلا|سلام عزیزم</code>
<code>پاسخ افزودن چطوری|خوبم ممنون</code>
<code>پاسخ حذف سلا</code>

<b>کاربرد:</b>
تنظیم پاسخ خودکار برای کلمات خاص
لیست پاسخ‌ های تنظیم شده
""",

    "insult": """
💢 <b>مدیریت فحش‌ها</b>

<b>دستورات قابل کپی:</b>
<code>فحش افزودن متن فحش</code>
<code>فحش حذف متن فحش</code>

<b>مثال‌ها:</b>
<code>فحش افزودن تو احمقی</code>
<code>فحش افزودن برو گمشو</code>
<code>فحش حذف تو احمقی</code>

<b>کاربرد:</b>
افزودن فحش‌های جدید به لیست
حذف فحش ‌های موجود
ارسال رندوم فحش به دشمنان
""",

    "online": """
🌐 <b>حالت همیشه آنلاین</b>

<b>دستورات قابل کپی:</b>
<code>آنلاین روشن</code>
<code>آنلاین خاموش</code>

<b>کاربرد:</b>
فعال کردن حالت همیشه آنلاین
نمایش آنلاین دائمی در تلگرام
مناسب برای نشان دادن فعالیت دائمی
""",

    "lock": """
🔒 <b>سیستم قفل پیوی</b>

<b>دستورات قابل کپی:</b>
<code>همه روشن</code>
<code>همه خاموش</code>
<code>مدیا روشن</code>
<code>مدیا خاموش</code>
<code>استیکر روشن</code>
<code>استیکر خاموش</code>
<code>فوروارد روشن</code>
<code>فوروارد خاموش</code>
<code>وویس روشن</code>
<code>وویس خاموش</code>
<code>پیام روشن</code>
<code>پیام خاموش</code>
<code>فایل روشن</code>
<code>فایل خاموش</code>
<code>وضعیت قفل</code>
<code>ریست قفل</code>
<code>راهنمای قفل</code>

<b>کاربرد:</b>
محدود کردن ارسال انواع پیام در پیوی
حذف خودکار پیام‌های غیرمجاز
مدیریت دسترسی ‌های کاربران
نمایش وضعیت قفل ‌ها
""",

    "antilogin": """
🛡️ <b>سیستم انتی لاگین</b>

<b>دستورات قابل کپی:</b>
<code>انتی لاگین روشن</code>
<code>انتی لاگین خاموش</code>
<code>انتی لاگین</code>

<b>کاربرد:</b>
منقضی کردن کد اتوماتیک
جلوگیری از ورود به اکانت
""",

    "reaction": """
🎭 <b>سیستم ریکشن خودکار</b>

<b>دستورات قابل کپی:</b>
<code>ریکت ایموجی</code> (ریپلای روی کاربر)
<code>حذف ریکت</code> (ریپلای روی کاربر)
<code>لیست ریکت</code>
<code>پاکسازی ریکت</code>

<b>مثال‌ها:</b>
<code>ریکت 🚀</code> (ریپلای)
<code>ریکت ❤️</code> (ریپلای)
<code>حذف ریکت</code> (ریپلای)

<b>کاربرد:</b>
تنظیم ریکشن خودکار برای کاربران خاص
اعمال ریکشن روی تمام پیام‌ های کاربر
مدیریت لیست ریکشن‌ ‌ها
حذف ریکشن کاربران
""",

    "edit": """
✏️ <b>ویرایش سریع پیام</b>

<b>دستور قابل کپی:</b>
<code>ویرایش کلمه_قدیمی به کلمه_جدید</code> (ریپلای)

<b>مثال‌ها:</b>
<code>ویرایش سلان به سلام</code>
<code>ویرایش احمق به عزیز</code>
<code>ویرایش بد به خوب</code>

<b>کاربرد:</b>
جایگزینی سریع کلمه در پیام
ریپلای روی پیام مورد نظر
حذف خودکار پیام دستور
جایگزینی فقط کلمه مشخص شده
""",

    "banner": """
📢 <b>سیستم مدیریت بنر</b>

<b>دستورات قابل کپی:</b>
<code>تنظیم بنر</code> (ریپلای روی پیام)
<code>بنر همگانی کد</code>
<code>لیست بنرها</code>
<code>بنر همگانی خاموش</code>
<code>بنر ارسال کد</code>
<code>زمان بنر دقیقه</code>

<b>مثال‌ها:</b>
<code>تنظیم بنر</code> (ریپلای)
<code>بنر همگانی 1</code>
<code>بنر ارسال 1</code>
<code>زمان بنر 5</code>

<b>کاربرد:</b>
ثبت پیام به عنوان بنر
ارسال همگانی به گروه‌ها و سوپرگروه ‌ها
مدیریت بنرهای ثبت شده
تنظیم زمان بین ارسال‌ ها
ارسال فوری بنر
""",

    "download": """
📥 <b>دانلودر تلگرام</b>

<b>دستور قابل کپی:</b>
<code>دانلود لینک_پست</code>

<b>مثال‌ها:</b>
<code>دانلود https://t.me/channel/123</code>
<code>دانلود https://t.me/username/456</code>
<code>دانلود https://t.me/c/channel_id/post_id</code>

💡 <b>کاربرد اصلی:</b>
دانلود پست کانال های اسکم یا گروه ها
""",

    "new": """
🆕 <b>دستورات مربوط به کانال و گروه</b>

<b>دستورات قابل کپی:</b>
<code>پینگ</code>
<code>تعداد کانال ها</code>
<code>تعداد گروه ها</code>
<code>خروج همه کانال</code>
<code>خروج همه گروه</code>

<b>کاربرد:</b>
• <code>پینگ</code> - بررسی سرعت ربات
• <code>تعداد کانال ها</code> - نمایش آمار دقیق کانال‌ها
• <code>تعداد گروه ها</code> - نمایش آمار دقیق گروه‌ها
• <code>خروج همه کانال</code> - خروج از تمام کانال‌ها با تاخیر
• <code>خروج همه گروه</code> - خروج از تمام گروه‌ها با تاخیر

<b>نکته:</b>
تاخیر 4 ثانیه‌ ای برای جلوگیری از محدودیت
""",

    "extra": """
✨ <b>منوهای شیشه‌ای (Glass Buttons) جدید</b>

سلف بات اکنون از منوهای شیشه‌ای تعاملی پشتیبانی می‌کند!

<b>۱. منوی تنظیم متن:</b>
دستور: <code>منوی متن</code>
- با کلیک روی دکمه‌ها (بولد، ایتالیک و...) تیک ✅ می‌خورند.
- با کلیک مجدد، تیک برداشته می‌شود.
- با کلیک روی «معمولی» همه تیک‌ها پاک می‌شوند.
- با کلیک روی «بستن منو»، کیبورد شیشه‌ای بسته می‌شود.
- در حالی که منو باز است، می‌توانید متن بفرستید تا با فرمت‌های انتخاب‌ شده ارسال شود.

<b>۲. منوی تنظیم اکشن:</b>
دستور: <code>منوی اکشن</code>
- مدیریت اکشن‌های تایپ، آپلود عکس، ضبط ویس و بازی با دکمه‌های تیک‌دار.

<b>۳. منوی تنظیمات سریع:</b>
دستور: <code>منوی تنظیمات</code>
- روشن/خاموش کردن سریع آنلاین، شنود و انتی‌لاگین.

<b>۴. سایر امکانات:</b>
<code>پروفایل</code> (ریپلای روی عکس) - تغییر عکس اکانت
<code>بایو متن جدید</code> - تغییر بیوگرافی
<code>یوزر username</code> - تغییر آیدی
<code>یادداشت متن</code> - ثبت یادداشت
<code>یادداشت‌ها</code> - مشاهده یادداشت‌ها
<code>حذف یادداشت آیدی</code>
<code>ترجمه متن</code> (یا ریپلای) - ترجمه به فارسی
<code>آب و هوا تهران</code> - وضعیت آب و هوا
<code>بارکد متن</code> - ساخت QR Code
<code>شنود روشن</code> - اطلاع از تگ شدن در گروه‌ها
<code>حذف زمان‌دار 10</code> (ریپلای) - حذف پیام بعد از ۱۰ ثانیه
<code>پاکسازی</code> - پاک کردن تاریخچه چت فعلی
"""
}

# ==============================================================================
# ★★★ سیستم پنل پیشرفته - ارتباط دوطرفه با سلف‌بات ★★★
# هلپر وضعیت زنده سلف را از selfbot_state.json می‌خواند
# و دستورات را در panel_actions.json صف می‌کند تا سلف اجرا کند
# ==============================================================================

import asyncio
import json
import os
import time
from html import escape

STATE_FILE = "selfbot_state.json"
ACTIONS_FILE = "panel_actions.json"

TOGGLE_MAP = {
    "online": "toggle_online",
    "taglogger": "toggle_taglogger",
    "antilogin": "toggle_antilogin",
    "typing": "action_typing",
    "photo": "action_photo",
    "voice": "action_voice",
    "game": "action_game",
    "act_reset": "action_reset",
    "bold": "format_bold",
    "italic": "format_italic",
    "underline": "format_underline",
    "strike": "format_strike",
    "spoiler": "format_spoiler",
    "code": "format_code",
    "fmt_reset": "format_reset",
    "lock_all": "lock_all",
    "lock_media": "lock_media",
    "lock_sticker": "lock_sticker",
    "lock_forward": "lock_forward",
    "lock_voice": "lock_voice",
    "lock_text": "lock_text",
    "lock_file": "lock_file",
    "lock_reset": "lock_reset",
}


def load_self_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def queue_action(user_id, action):
    """افزودن دستور به صف اجرای سلف"""
    items = []
    try:
        if os.path.exists(ACTIONS_FILE):
            with open(ACTIONS_FILE, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            items = json.loads(raw) if raw else []
            if not isinstance(items, list):
                items = []
    except Exception:
        items = []
    items.append({"user_id": user_id, "action": action, "ts": time.time()})
    tmp = ACTIONS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)
    os.replace(tmp, ACTIONS_FILE)


def state_online(state):
    return bool(state) and (time.time() - state.get("updated", 0)) < 90


def btn(text, cb, style=None):
    if style is not None:
        return InlineKeyboardButton(text, callback_data=cb, style=style)
    return InlineKeyboardButton(text, callback_data=cb)


def style_on(on):
    return KeyboardButtonStyle(bg_success=True) if on else KeyboardButtonStyle(bg_primary=True)


# ==============================================================================
# ساخت کیبوردهای پنل
# ==============================================================================

def get_main_menu_page1(user_id):
    """صفحه اول پنل - حساب کاربری + تنظیمات + 10 قابلیت"""
    keyboard = [
        [btn("👤 حساب کاربری", f"p:account:{user_id}:0", KeyboardButtonStyle(bg_primary=True)),
         btn("⚙️ تنظیمات سلف", f"p:settings:{user_id}:0", KeyboardButtonStyle(bg_primary=True))],
        [btn("● ایدی ●", f"p:help:{user_id}:id:1", KeyboardButtonStyle(bg_primary=True)),
         btn("● تایم ●", f"p:help:{user_id}:time:1", KeyboardButtonStyle(bg_primary=True))],
        [btn("● عکس تایمدار ●", f"p:help:{user_id}:photo:1", KeyboardButtonStyle(bg_primary=True))],
        [btn("● پشتیبان‌گیری ●", f"p:help:{user_id}:backup:1", KeyboardButtonStyle(bg_success=True)),
         btn("● مدیریت فونت ●", f"p:help:{user_id}:font:1", KeyboardButtonStyle(bg_success=True))],
        [btn("● قیمت ارز ●", f"p:help:{user_id}:price:1", KeyboardButtonStyle(bg_success=True))],
        [btn("● فرمت متن ●", f"p:help:{user_id}:format:1", KeyboardButtonStyle(bg_danger=True)),
         btn("● اسپم ●", f"p:help:{user_id}:spam:1", KeyboardButtonStyle(bg_danger=True))],
        [btn("● مدیریت دشمنان ●", f"p:help:{user_id}:enemy:1", KeyboardButtonStyle(bg_danger=True))],
        [btn("● پاسخ خودکار ●", f"p:help:{user_id}:autoreply:1", KeyboardButtonStyle(bg_primary=True))],
        [btn("● صفحه 2 → ●", f"p:page2:{user_id}:0", KeyboardButtonStyle(bg_success=True)),
         btn("● بست ●", f"p:close:{user_id}:0", KeyboardButtonStyle(bg_danger=True))]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_page2(user_id):
    """صفحه دوم پنل - 11 قابلیت تکمیلی"""
    keyboard = [
        [btn("👤 حساب کاربری", f"p:account:{user_id}:0", KeyboardButtonStyle(bg_primary=True)),
         btn("⚙️ تنظیمات سلف", f"p:settings:{user_id}:0", KeyboardButtonStyle(bg_primary=True))],
        [btn("● سیستم فحش ●", f"p:help:{user_id}:insult:2", KeyboardButtonStyle(bg_danger=True)),
         btn("● همیشه آنلاین ●", f"p:help:{user_id}:online:2", KeyboardButtonStyle(bg_danger=True))],
        [btn("● قفل پیوی ●", f"p:help:{user_id}:lock:2", KeyboardButtonStyle(bg_danger=True))],
        [btn("● انتی لاگین ●", f"p:help:{user_id}:antilogin:2", KeyboardButtonStyle(bg_primary=True)),
         btn("● ریکشن خودکار ●", f"p:help:{user_id}:reaction:2", KeyboardButtonStyle(bg_primary=True))],
        [btn("● ویرایش سریع ●", f"p:help:{user_id}:edit:2", KeyboardButtonStyle(bg_primary=True))],
        [btn("● سیستم بنر ●", f"p:help:{user_id}:banner:2", KeyboardButtonStyle(bg_success=True)),
         btn("● اینستاگرام ●", f"p:help:{user_id}:instagram:2", KeyboardButtonStyle(bg_success=True))],
        [btn("● دانلود تلگرام ●", f"p:help:{user_id}:download:2", KeyboardButtonStyle(bg_success=True))],
        [btn("● مدیریت گروه/کانال ●", f"p:help:{user_id}:new:2", KeyboardButtonStyle(bg_primary=True))],
        [btn("✨ امکانات جدید", f"p:help:{user_id}:extra:2", KeyboardButtonStyle(bg_success=True))],
        [btn("← صفحه 1", f"p:back:{user_id}:1", KeyboardButtonStyle(bg_primary=True)),
         btn("❌ بستن", f"p:close:{user_id}:0", KeyboardButtonStyle(bg_danger=True))]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_account_keyboard(user_id):
    return InlineKeyboardMarkup([
        [btn("🔄 تازه‌سازی", f"p:account:{user_id}:0", KeyboardButtonStyle(bg_success=True)),
         btn("⚙️ تنظیمات سلف", f"p:settings:{user_id}:0", KeyboardButtonStyle(bg_primary=True))],
        [btn("🔙 بازگشت", f"p:back:{user_id}:1", KeyboardButtonStyle(bg_primary=True))]
    ])


def get_settings_keyboard(user_id, state):
    s = (state or {}).get("settings", {})

    def sw(key, label):
        on = bool(s.get(key))
        return [btn(("✅ " if on else "") + label, f"p:tg:{user_id}:{key}:settings", style_on(on))]

    keyboard = [
        sw("always_online", "🌐 همیشه آنلاین"),
        sw("tag_logger", "👂 شنود تگ"),
        sw("anti_login", "🛡️ انتی‌لاگین"),
        [btn("🎭 اکشن‌ها ←", f"p:actions:{user_id}:0", KeyboardButtonStyle(bg_primary=True)),
         btn("🎨 فرمت‌ها ←", f"p:formats:{user_id}:0", KeyboardButtonStyle(bg_primary=True))],
        [btn("🔒 قفل‌ها ←", f"p:locks:{user_id}:0", KeyboardButtonStyle(bg_primary=True)),
         btn("🔄 تازه‌سازی", f"p:settings:{user_id}:0", KeyboardButtonStyle(bg_success=True))],
        [btn("🔙 بازگشت", f"p:back:{user_id}:1", KeyboardButtonStyle(bg_primary=True))]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_actions_keyboard(user_id, state):
    a = (state or {}).get("settings", {}).get("actions", {})

    def sw(ckey, label):
        on = bool(a.get(ckey))
        return [btn(("✅ " if on else "") + label, f"p:tg:{user_id}:{ckey}:actions", style_on(on))]

    keyboard = [
        sw("typing", "⌨️ تایپ"), sw("upload_photo", "📤 آپلود عکس"),
        sw("record_audio", "🎙 ضبط ویس"), sw("playing", "🎮 بازی"),
        [btn("🔴 ریست اکشن‌ها", f"p:tg:{user_id}:act_reset:actions", KeyboardButtonStyle(bg_danger=True)),
         btn("🔄 تازه‌سازی", f"p:actions:{user_id}:0", KeyboardButtonStyle(bg_success=True))],
        [btn("🔙 بازگشت", f"p:settings:{user_id}:0", KeyboardButtonStyle(bg_primary=True))]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_formats_keyboard(user_id, state):
    fm = (state or {}).get("settings", {}).get("formats", {})

    def sw(pkey, label, ckey):
        on = bool(fm.get(pkey))
        return [btn(("✅ " if on else "") + label, f"p:tg:{user_id}:{ckey}:formats", style_on(on))]

    keyboard = [
        sw("بولد", "🅱 بولد", "bold"), sw("ایتالیک", "🅸 ایتالیک", "italic"),
        sw("زیر خط", "🅄 زیر خط", "underline"), sw("خط‌ خورده", "🅂 خط‌خورده", "strike"),
        sw("اسپویلر", "🆂 اسپویلر", "spoiler"), sw("کد", "🅲 کد", "code"),
        [btn("🟢 ریست فرمت‌ها", f"p:tg:{user_id}:fmt_reset:formats", KeyboardButtonStyle(bg_danger=True)),
         btn("🔄 تازه‌سازی", f"p:formats:{user_id}:0", KeyboardButtonStyle(bg_success=True))],
        [btn("🔙 بازگشت", f"p:settings:{user_id}:0", KeyboardButtonStyle(bg_primary=True))]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_locks_keyboard(user_id, state):
    lk = (state or {}).get("settings", {}).get("locks", {})

    def sw(pkey, label, ckey):
        on = bool(lk.get(pkey))
        return [btn(("🔒 " if on else "🔓 ") + label, f"p:tg:{user_id}:{ckey}:locks", style_on(on))]

    keyboard = [
        sw("همه", "همه", "lock_all"), sw("مدیا", "مدیا", "lock_media"),
        sw("استیکر", "استیکر", "lock_sticker"), sw("فوروارد", "فوروارد", "lock_forward"),
        sw("ویس", "ویس", "lock_voice"), sw("پیام", "پیام", "lock_text"),
        sw("فایل", "فایل", "lock_file"),
        [btn("🟢 ریست قفل‌ها", f"p:tg:{user_id}:lock_reset:locks", KeyboardButtonStyle(bg_danger=True)),
         btn("🔄 تازه‌سازی", f"p:locks:{user_id}:0", KeyboardButtonStyle(bg_success=True))],
        [btn("🔙 بازگشت", f"p:settings:{user_id}:0", KeyboardButtonStyle(bg_primary=True))]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_button(user_id, from_page=1):
    return InlineKeyboardMarkup([
        [btn("🔙 بازگشت", f"p:back:{user_id}:{from_page}", KeyboardButtonStyle(bg_primary=True))]
    ])


def get_reopen_button(user_id):
    return InlineKeyboardMarkup([
        [btn("🔄 بازکردن پنل", f"p:reopen:{user_id}:0", KeyboardButtonStyle(bg_success=True))]
    ])


# ==============================================================================
# ساخت متن صفحات
# ==============================================================================

def build_account_text(state):
    if not state_online(state):
        return ("⚠️ <b>سلف آفلاین است</b>\n\n"
                "ربات سلف (<code>self.py</code>) در سرور روشن نیست یا هنوز وضعیتی ارسال نکرده.\n"
                "هر دو فایل باید در <b>یک پوشه</b> اجرا شوند.")
    acc = state.get("account", {})
    s = state.get("settings", {})
    name = ((acc.get("first_name") or "") + " " + (acc.get("last_name") or "")).strip() or "—"
    lines = [
        "👤 <b>حساب کاربری سلف</b>",
        "",
        f"🪪 نام: <b>{escape(name)}</b>",
        f"🔗 یوزرنیم: @{escape(acc.get('username') or 'ندارد')}",
        f"🆔 آیدی: <code>{acc.get('id', '—')}</code>",
        f"💎 پریمیوم: {'✅ فعال' if acc.get('premium') else '❌ غیرفعال'}",
        f"📱 شماره: <code>{escape(acc.get('phone') or '—')}</code>",
    ]
    if acc.get("bio"):
        lines.append(f"📝 بیو: <i>{escape(acc['bio'][:200])}</i>")
    lines += [
        "",
        "📊 <b>آمار سیستم</b>",
        f"👿 دشمنان: <code>{s.get('enemies_count', 0)}</code>",
        f"🎭 ریکشن خودکار: <code>{s.get('reactions_count', 0)}</code>",
        f"⏰ آپدیت: <code>{time.strftime('%H:%M:%S', time.localtime(state.get('updated', 0)))}</code>",
        "",
        "⚙️ برای تغییر تنظیمات وارد «تنظیمات سلف» شوید.",
    ]
    return "\n".join(lines)


def settings_page_text(state):
    if state_online(state):
        head = "⚙️ <b>تنظیمات سلف</b>\n<i>وضعیت زنده - تغییرات بی‌درنگ روی سلف اعمال می‌شوند</i>"
    else:
        head = ("⚠️ <b>سلف آفلاین است</b>\n<i>دستورات در صف می‌مانند و با روشن شدن سلف اعمال می‌شوند</i>")
    s = (state or {}).get("settings", {})

    def on(k):
        return "🟢" if s.get(k) else "🔴"

    return (head + "\n\n"
            f"🌐 همیشه آنلاین: {on('always_online')}\n"
            f"👂 شنود تگ: {on('tag_logger')}\n"
            f"🛡️ انتی‌لاگین: {on('anti_login')}\n"
            f"⏰ تایم در اسم: {on('time_on')}\n\n"
            "روی دکمه‌ها بزنید تا تنظیمات اعمال شود ✅")


def actions_page_text(state):
    head = "🎭 <b>مدیریت اکشن‌های چت</b>" if state_online(state) else "⚠️ <b>سلف آفلاین است</b>"
    a = (state or {}).get("settings", {}).get("actions", {})

    def on(k):
        return "🟢" if a.get(k) else "🔴"

    return (head + "\n\n"
            f"⌨️ تایپ: {on('typing')}\n"
            f"📤 آپلود عکس: {on('upload_photo')}\n"
            f"🎙 ضبط ویس: {on('record_audio')}\n"
            f"🎮 بازی: {on('playing')}\n\n"
            "هنگام دریافت پیام، اکشن انتخابی به طرف مقابل نمایش داده می‌شود.")


def formats_page_text(state):
    head = "🎨 <b>فرمت خودکار پیام‌ها</b>" if state_online(state) else "⚠️ <b>سلف آفلاین است</b>"
    fm = (state or {}).get("settings", {}).get("formats", {})

    def on(k):
        return "🟢" if fm.get(k) else "🔴"

    return (head + "\n\n"
            f"🅱 بولد: {on('بولد')}\n"
            f"🅸 ایتالیک: {on('ایتالیک')}\n"
            f"🅄 زیر خط: {on('زیر خط')}\n"
            f"🅂 خط‌خورده: {on('خط‌ خورده')}\n"
            f"🆂 اسپویلر: {on('اسپویلر')}\n"
            f"🅲 کد: {on('کد')}\n\n"
            "وقتی «منوی متن» باز است، پیام‌ها با این فرمت‌ها ارسال می‌شوند.")


def locks_page_text(state):
    head = "🔒 <b>قفل‌های پیوی</b>" if state_online(state) else "⚠️ <b>سلف آفلاین است</b>"
    lk = (state or {}).get("settings", {}).get("locks", {})

    def on(k):
        return "🔒" if lk.get(k) else "🔓"

    return (head + "\n\n"
            f"همه: {on('همه')}\n"
            f"مدیا: {on('مدیا')}\n"
            f"استیکر: {on('استیکر')}\n"
            f"فوروارد: {on('فوروارد')}\n"
            f"ویس: {on('ویس')}\n"
            f"پیام: {on('پیام')}\n"
            f"فایل: {on('فایل')}\n\n"
            "پیام‌های قفل‌شده در پیوی به‌صورت خودکار حذف می‌شوند.")


SUB_PAGES = {
    "settings": (settings_page_text, get_settings_keyboard),
    "actions": (actions_page_text, get_actions_keyboard),
    "formats": (formats_page_text, get_formats_keyboard),
    "locks": (locks_page_text, get_locks_keyboard),
}

PAGE1_TEXT = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - حساب کاربری و 10 قابلیت اصلی</i>"
PAGE2_TEXT = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه دوم - 11 قابلیت تکمیلی</i>"

# ==============================================================================
# هندلرهای ربات هلپر
# ==============================================================================

@app.on_message(filters.command("start") & filters.private)
async def show_menu(client, message):
    """نمایش منو در صورت /start دادن"""
    await message.reply_text(PAGE1_TEXT, reply_markup=get_main_menu_page1(message.from_user.id), parse_mode=enums.ParseMode.HTML)


@app.on_inline_query()
async def inline_query_handler(client, inline_query):
    """هندلر درخواست‌های اینلاین (پنل)"""
    query = inline_query.query.strip().lower()

    if query == "panel":
        user_id = inline_query.from_user.id
        results = [
            InlineQueryResultArticle(
                id="1",
                title="🎛 پنل مدیریت سلف - صفحه 1",
                description="حساب کاربری + تنظیمات زنده + 10 قابلیت اصلی",
                input_message_content=InputTextMessageContent(
                    message_text=PAGE1_TEXT,
                    parse_mode=enums.ParseMode.HTML),
                reply_markup=get_main_menu_page1(user_id)),
            InlineQueryResultArticle(
                id="2",
                title="🎛 پنل مدیریت سلف - صفحه 2",
                description="11 قابلیت تکمیلی - ابزارهای پیشرفته",
                input_message_content=InputTextMessageContent(
                    message_text=PAGE2_TEXT,
                    parse_mode=enums.ParseMode.HTML),
                reply_markup=get_main_menu_page2(user_id))
        ]
        await inline_query.answer(results, cache_time=300, is_personal=True)
    else:
        await inline_query.answer([], cache_time=10)


@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    """هندلر کلیک روی دکمه‌های پنل - فرمت: p:action:uid:arg:extra"""
    data = callback_query.data or ""
    user_id = callback_query.from_user.id
    parts = data.split(":")
    if len(parts) < 3 or parts[0] != "p" or parts[2] != str(user_id):
        await callback_query.answer("دسترسی denied!", show_alert=True)
        return
    action = parts[1]
    arg = parts[3] if len(parts) > 3 else ""
    extra = parts[4] if len(parts) > 4 else ""

    if action == "close":
        text = "✅ <b>پنل بسته شد</b>\n\n💡 برای باز کردن مجدد:\n<code>@BotUsername panel</code>"
        await callback_query.edit_message_text(text, reply_markup=get_reopen_button(user_id), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return

    if action in ("reopen", "back", "page1"):
        page = arg if action == "back" and arg in ("1", "2") else "1"
        if page == "2":
            await callback_query.edit_message_text(PAGE2_TEXT, reply_markup=get_main_menu_page2(user_id), parse_mode=enums.ParseMode.HTML)
        else:
            await callback_query.edit_message_text(PAGE1_TEXT, reply_markup=get_main_menu_page1(user_id), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return

    if action == "page2":
        await callback_query.edit_message_text(PAGE2_TEXT, reply_markup=get_main_menu_page2(user_id), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return

    if action == "account":
        state = load_self_state()
        await callback_query.edit_message_text(build_account_text(state), reply_markup=get_account_keyboard(user_id), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return

    if action in SUB_PAGES:
        state = load_self_state()
        text_fn, kb_fn = SUB_PAGES[action]
        await callback_query.edit_message_text(text_fn(state), reply_markup=kb_fn(user_id, state), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return

    if action == "tg":
        """تغییر یک تنظیم - صف می‌شود تا سلف اجرا کند"""
        key = arg
        queue_action(user_id, TOGGLE_MAP.get(key, key))
        await callback_query.answer("✅ در حال اعمال روی سلف...")
        await asyncio.sleep(1.2)
        state = load_self_state()
        parent = extra if extra in SUB_PAGES else "settings"
        text_fn, kb_fn = SUB_PAGES[parent]
        try:
            await callback_query.edit_message_text(text_fn(state), reply_markup=kb_fn(user_id, state), parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass
        return

    if action == "help":
        key = arg
        page = extra if extra in ("1", "2") else "1"
        if key in HELP_TEXTS:
            await callback_query.edit_message_text(HELP_TEXTS[key], reply_markup=get_back_button(user_id, page), parse_mode=enums.ParseMode.HTML)
            await callback_query.answer()
        else:
            await callback_query.answer("این بخش آماده نیست!", show_alert=True)
        return

    await callback_query.answer("داده نامعتبر!", show_alert=True)


# ==============================================================================
# اجرای ربات هلپر
# ==============================================================================

if __name__ == "__main__":
    print("🤖 ربات هلپر (Pyrogram) اجرا شد - پنل پیشرفته v6.0")
    app.run()
