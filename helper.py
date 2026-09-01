# ==============================================================================
# ربات هلپر و مدیریت پنل سلف بات (PersianGulf Helper Bot)
# نسخه: 5.0.0 - پشتیبانی از دکمه‌های رنگی و رفع مشکل تایم اوت
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
# ساخت کیبوردهای پنل (دکمه‌های رنگی)
# ==============================================================================

def get_main_menu_page1(user_id):
    """صفحه اول پنل"""
    keyboard = [
        [
            InlineKeyboardButton("● ایدی ●", callback_data=f"help_id_{user_id}_1", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton("● تایم ●", callback_data=f"help_time_{user_id}_1", style=KeyboardButtonStyle(bg_primary=True))
        ],
        [
            InlineKeyboardButton("● عکس تایمدار ●", callback_data=f"help_photo_{user_id}_1", style=KeyboardButtonStyle(bg_primary=True)),
        ],
        [
            InlineKeyboardButton("● پشتیبان‌گیری ●", callback_data=f"help_backup_{user_id}_1", style=KeyboardButtonStyle(bg_success=True)),
            InlineKeyboardButton("● مدیریت فونت ●", callback_data=f"help_font_{user_id}_1", style=KeyboardButtonStyle(bg_success=True))
        ],
        [
            InlineKeyboardButton("● قیمت ارز ●", callback_data=f"help_price_{user_id}_1", style=KeyboardButtonStyle(bg_success=True)),
        ],
        [
            InlineKeyboardButton("● فرمت متن ●", callback_data=f"help_format_{user_id}_1", style=KeyboardButtonStyle(bg_danger=True)),
            InlineKeyboardButton("● اسپم ●", callback_data=f"help_spam_{user_id}_1", style=KeyboardButtonStyle(bg_danger=True))
        ],
        [
            InlineKeyboardButton("● مدیریت دشمنان ●", callback_data=f"help_enemy_{user_id}_1", style=KeyboardButtonStyle(bg_danger=True)),
        ],
        [
            InlineKeyboardButton("● پاسخ خودکار ●", callback_data=f"help_autoreply_{user_id}_1", style=KeyboardButtonStyle(bg_primary=True)),
        ],
        [
            InlineKeyboardButton("● صفحه 2 → ●", callback_data=f"help_page2_{user_id}", style=KeyboardButtonStyle(bg_success=True)),
            InlineKeyboardButton("● بست ●", callback_data=f"help_close_{user_id}", style=KeyboardButtonStyle(bg_danger=True))
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_page2(user_id):
    """صفحه دوم پنل"""
    keyboard = [
        [
            InlineKeyboardButton("● سیستم فحش ●", callback_data=f"help_insult_{user_id}_2", style=KeyboardButtonStyle(bg_danger=True)),
            InlineKeyboardButton("● همیشه آنلاین ●", callback_data=f"help_online_{user_id}_2", style=KeyboardButtonStyle(bg_danger=True))
        ],
        [
            InlineKeyboardButton("● قفل پیوی ●", callback_data=f"help_lock_{user_id}_2", style=KeyboardButtonStyle(bg_danger=True)),
        ],
        [
            InlineKeyboardButton("●️ انتی لاگین ●", callback_data=f"help_antilogin_{user_id}_2", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton("● ریکشن خودکار ●", callback_data=f"help_reaction_{user_id}_2", style=KeyboardButtonStyle(bg_primary=True))
        ],
        [
            InlineKeyboardButton("● ویرایش سریع ●", callback_data=f"help_edit_{user_id}_2", style=KeyboardButtonStyle(bg_primary=True)),
        ],
        [
            InlineKeyboardButton("● سیستم بنر ●", callback_data=f"help_banner_{user_id}_2", style=KeyboardButtonStyle(bg_success=True)),
            InlineKeyboardButton("● اینستاگرام ●", callback_data=f"help_instagram_{user_id}_2", style=KeyboardButtonStyle(bg_success=True))
        ],
        [
            InlineKeyboardButton("● دانلود تلگرام ●", callback_data=f"help_download_{user_id}_2", style=KeyboardButtonStyle(bg_success=True)),
        ],
        [
            InlineKeyboardButton("● مدیریت گروه/کانال ●", callback_data=f"help_new_{user_id}_2", style=KeyboardButtonStyle(bg_primary=True)),
        ],
        [
            InlineKeyboardButton("✨ امکانات جدید", callback_data=f"help_extra_{user_id}_2", style=KeyboardButtonStyle(bg_success=True)),
        ],
        [
            InlineKeyboardButton("← صفحه 1", callback_data=f"help_page1_{user_id}", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton("❌ بستن", callback_data=f"help_close_{user_id}", style=KeyboardButtonStyle(bg_danger=True))
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_button(user_id, from_page=1):
    """دکمه بازگشت"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"help_back_{user_id}_{from_page}", style=KeyboardButtonStyle(bg_primary=True))]
    ])

def get_reopen_button(user_id):
    """دکمه باز کردن مجدد پنل"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 بازکردن پنل", callback_data=f"help_reopen_{user_id}", style=KeyboardButtonStyle(bg_success=True))]
    ])

# ==============================================================================
# هندلرهای ربات هلپر
# ==============================================================================

@app.on_message(filters.command("start") & filters.private)
async def show_menu(client, message):
    """نمایش منو در صورت /start دادن"""
    text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>"
    await message.reply_text(text, reply_markup=get_main_menu_page1(message.from_user.id), parse_mode=enums.ParseMode.HTML)

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
                description="10 قابلیت اصلی - مدیریت کامل",
                input_message_content=InputTextMessageContent(
                    message_text="<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>",
                    parse_mode=enums.ParseMode.HTML
                ),
                reply_markup=get_main_menu_page1(user_id)
            ),
            InlineQueryResultArticle(
                id="2",
                title="🎛 پنل مدیریت سلف - صفحه 2",
                description="11 قابلیت تکمیلی - ابزارهای پیشرفته",
                input_message_content=InputTextMessageContent(
                    message_text="<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه دوم - 11 قابلیت تکمیلی</i>",
                    parse_mode=enums.ParseMode.HTML
                ),
                reply_markup=get_main_menu_page2(user_id)
            )
        ]
        await inline_query.answer(results, cache_time=300, is_personal=True)
    else:
        # پاسخ خالی به کوئری‌های نامعتبر برای جلوگیری از تایم‌اوت
        await inline_query.answer([], cache_time=10)

@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    """هندلر کلیک روی دکمه‌های پنل"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if not f"_{user_id}" in data:
        await callback_query.answer("دسترسی denied!", show_alert=True)
        return
        
    parts = data.split("_")
    if len(parts) >= 3:
        action = parts[1]
        page_num = int(parts[-1]) if len(parts) >= 4 and parts[-1].isdigit() else 1
    else:
        await callback_query.answer("داده نامعتبر!", show_alert=True)
        return
    
    if action == "close":
        text = "✅ <b>پنل بسته شد</b>\n\n💡 برای باز کردن مجدد:\n<code>@BotUsername panel</code>"
        await callback_query.edit_message_text(text, reply_markup=get_reopen_button(user_id), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return
    
    if action in ["reopen", "page1"]:
        text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>"
        await callback_query.edit_message_text(text, reply_markup=get_main_menu_page1(user_id), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return
    
    if action == "page2":
        text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه دوم - 11 قابلیت تکمیلی</i>"
        await callback_query.edit_message_text(text, reply_markup=get_main_menu_page2(user_id), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return
    
    if action == "back":
        if page_num == 2:
            text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه دوم - 11 قابلیت تکمیلی</i>"
            await callback_query.edit_message_text(text, reply_markup=get_main_menu_page2(user_id), parse_mode=enums.ParseMode.HTML)
        else:
            text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>"
            await callback_query.edit_message_text(text, reply_markup=get_main_menu_page1(user_id), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return
        
    if action in HELP_TEXTS:
        text = HELP_TEXTS.get(action, "راهنمای این بخش آماده نیست.")
        await callback_query.edit_message_text(text, reply_markup=get_back_button(user_id, page_num), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
    else:
        await callback_query.answer(f"این بخش ({action}) آماده نیست!", show_alert=True)

# ==============================================================================
# اجرای ربات هلپر
# ==============================================================================

if __name__ == "__main__":
    print("🤖 ربات هلپر (Pyrogram) اجرا شد")
    app.run()
