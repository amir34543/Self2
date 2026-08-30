from pyrogram import Client, enums, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent, KeyboardButtonStyle
import logging

TOKEN = "8895709305:AAEUAYHr1nKKk46wpQaAzC98mWa3ChKUfis" # توکن ربات هلپر
API_ID = 35656061
API_HASH = "b37f2596516bc0439bf505d1d230395c"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client("helper_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

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

✅ دانلود با کیفیت اصلی
✅ نمایش توضیحات پست
""",

    "id": """
🆔 <b>سیستم آیدی پیشرفته</b>

<b>دستور قابل کپی:</b>
<code>ایدی</code>

✅ نمایش آیدی عددی کاربر
✅ یوزرنیم و نام کامل
✅ وضعیت پریمیوم
✅ گروه‌های مشترک
""",

    "photo": """
📸 <b>ذخیره عکس تایمدار</b>

<b>دستور قابل کپی:</b>
<code>عکس سیو</code> (ریپلای روی عکس)

ذخیره دستی عکس‌های تایمدار با اطلاعات کامل کاربر
""",

    "backup": """
💾 <b>پشتیبان‌گیری</b>

<b>دستور قابل کپی:</b>
<code>سیو @یوزرنیم</code>

ذخیره تاریخچه چت در فایل متنی و ارسال به پیام‌های ذخیره شده
""",

    "font": """
🔤 <b>مدیریت فونت</b>

<b>دستورات قابل کپی:</b>
<code>لیست فونت</code>
<code>تنظیم فونت 1</code> تا <code>تنظیم فونت 6</code>

تغییر فونت نمایش زمان کنار نام کاربری
""",

    "price": """
💱 <b>قیمت ارز</b>

<b>دستور قابل کپی:</b>
<code>قیمت BTC</code>
<code>قیمت TON</code>

نمایش قیمت لحظه‌ای ارزهای دیجیتال (تومانی و دلاری)
""",

    "spam": """
🔁 <b>ارسال اسپم</b>

<b>دستور قابل کپی:</b>
<code>اسپم 10 سلام</code>

ارسال پیام تکراری (حداکثر ۵۰ پیام در یک دستور)
""",

    "format": """
🎨 <b>سیستم فرمت خودکار HTML</b>

<b>دستورات:</b>
<code>فرمت بولد روشن</code>
<code>فرمت ایتالیک خاموش</code>
<code>فرمت ریست</code>

تبدیل خودکار پیام‌ها به فرمت‌های مختلف تایپی
""",

    "enemy": """
👿 <b>مدیریت دشمنان</b>

<b>دستورات:</b>
<code>دشمن</code> (ریپلای روی پیام کاربر)
<code>حذف دشمن</code>
<code>لیست دشمن</code>

ارسال خودکار فحش رندوم به دشمنان در پیوی و گروه
""",

    "autoreply": """
🤖 <b>پاسخ خودکار</b>

<b>دستورات:</b>
<code>پاسخ افزودن سلام|سلام چطوری</code>
<code>پاسخ حذف سلام</code>

تنظیم پاسخ خودکار برای کلمات خاص در پیوی
""",

    "insult": """
💢 <b>مدیریت فحش‌ها</b>

<b>دستورات:</b>
<code>فحش افزودن [متن]</code>
<code>فحش حذف [متن]</code>

مدیریت لیست فحش‌هایی که به دشمنان ارسال می‌شود
""",

    "online": """
🌐 <b>حالت همیشه آنلاین</b>

<b>دستورات:</b>
<code>آنلاین روشن</code>
<code>آنلاین خاموش</code>

فعال کردن حالت همیشه آنلاین در تلگرام
""",

    "lock": """
🔒 <b>سیستم قفل پیوی</b>

<b>دستورات:</b>
<code>همه روشن</code>
<code>مدیا روشن</code>
<code>استیکر روشن</code>
<code>وضعیت قفل</code>

محدود کردن ارسال انواع پیام در پیوی
""",

    "antilogin": """
🛡️ <b>سیستم انتی لاگین</b>

<b>دستورات:</b>
<code>انتی لاگین روشن</code>
<code>انتی لاگین خاموش</code>

منقضی کردن کد اتوماتیک و جلوگیری از هک اکانت
""",

    "reaction": """
🎭 <b>سیستم ریکشن خودکار</b>

<b>دستورات:</b>
<code>ریکت 😊</code> (ریپلای روی کاربر)
<code>حذف ریکت</code>

اعمال ریکشن خودکار روی تمام پیام‌های یک کاربر خاص
""",

    "edit": """
✏️ <b>ویرایش سریع پیام</b>

<b>دستور:</b>
<code>ویرایش کلمه_قدیمی به کلمه_جدید</code> (ریپلای)

جایگزینی سریع کلمه در پیام بدون نیاز به کپی و ادیت دستی
""",

    "banner": """
📢 <b>سیستم مدیریت بنر</b>

<b>دستورات:</b>
<code>تنظیم بنر</code> (ریپلای روی پیام)
<code>بنر همگانی 1</code>

ارسال همگانی بنر به گروه‌ها و سوپرگروه‌ها
""",

    "download": """
📥 <b>دانلودر تلگرام</b>

<b>دستور قابل کپی:</b>
<code>دانلود https://t.me/channel/123</code>

دانلود پست کانال‌های اسکم یا گروه‌ها
""",
    "new": """
🆕 <b>دستورات گروه/کانال</b>

<code>پینگ</code>
<code>تعداد کانال ها</code>
<code>خروج همه کانال</code>
""",
    "extra": """
✨ <b>امکانات جدید سلف</b>

<b>تغییرات اکانت:</b>
<code>پروفایل</code> (ریپلای روی عکس) - تغییر عکس اکانت
<code>بایو متن جدید</code> - تغییر بیوگرافی
<code>یوزر username</code> - تغییر آیدی

<b>ابزارها:</b>
<code>یادداشت متن</code> - ثبت یادداشت
<code>یادداشت‌ها</code> - مشاهده یادداشت‌ها
<code>ترجمه متن</code> (یا ریپلای) - ترجمه به فارسی
<code>آب و هوا تهران</code> - وضعیت آب و هوا
<code>بارکد متن</code> - ساخت QR Code

<b>مدیریت چت:</b>
<code>شنود روشن</code> - اطلاع از تگ شدن در گروه‌ها
<code>حذف زمان‌دار 10</code> (ریپلای) - حذف پیام بعد از ۱۰ ثانیه
<code>پاکسازی</code> - پاک کردن تاریخچه چت فعلی
"""
}

def get_main_menu_page1(user_id):
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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"help_back_{user_id}_{from_page}", style=KeyboardButtonStyle(bg_primary=True))]
    ])

def get_reopen_button(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 بازکردن پنل", callback_data=f"help_reopen_{user_id}", style=KeyboardButtonStyle(bg_success=True))]
    ])

@app.on_message(filters.command("start") & filters.private)
async def show_menu(client, message):
    user_id = message.from_user.id
    text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>"
    await message.reply_text(text, reply_markup=get_main_menu_page1(user_id), parse_mode=enums.ParseMode.HTML)

@app.on_inline_query()
async def inline_query_handler(client, inline_query):
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
        await inline_query.answer([], cache_time=10)

@app.on_callback_query()
async def callback_query_handler(client, callback_query):
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
    
    # استفاده از edit_message_text برای پشتیبانی از پیام‌های اینلاین
    if action == "close":
        text = "✅ <b>پنل بسته شد</b>\n\n💡 برای باز کردن مجدد:\n<code>@BotUsername panel</code>"
        await callback_query.edit_message_text(text, reply_markup=get_reopen_button(user_id), parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return
    
    if action == "reopen" or action == "page1":
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

if __name__ == "__main__":
    print("🤖 ربات هلپر اجرا شد")
    app.run()
