from pyrogram import Client, enums, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent, KeyboardButtonStyle
import logging

TOKEN = "8895709305:AAEUAYHr1nKKk46wpQaAzC98mWa3ChKUfis" # توکن ربات هلپر
API_ID = 35656061
API_HASH = "b37f2596516bc0439bf505d1d230395c"

logging.basicConfig(level=logging.INFO)
app = Client("helper_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

HELP_TEXTS = {
    "time": "⏰ <b>مدیریت تایم</b>\n\n<code>تایم روشن</code>\n<code>تایم خاموش</code>\n\nنمایش زمان کنار نام کاربری با فونت‌های مختلف",
    "instagram": "📥 <b>دانلودر اینستاگرام</b>\n\n<code>اینستا لینک_پست</code>\n\n✅ دانلود با کیفیت اصلی\n✅ نمایش توضیحات پست",
    "id": "🆔 <b>سیستم آیدی پیشرفته</b>\n\n<code>ایدی</code>\n\n✅ نمایش آیدی عددی کاربر\n✅ یوزرنیم و نام کامل\n✅ وضعیت پریمیوم",
    "photo": "📸 <b>ذخیره عکس تایمدار</b>\n\n<code>عکس سیو</code> (ریپلای روی عکس)\n\nذخیره دستی عکس‌های تایمدار با اطلاعات کاربر",
    "backup": "💾 <b>پشتیبان‌گیری</b>\n\n<code>سیو @یوزرنیم</code>\n\nذخیره تاریخچه چت در فایل متنی",
    "font": "🔤 <b>مدیریت فونت</b>\n\n<code>لیست فونت</code>\n<code>تنظیم فونت 1</code> تا <code>6</code>\n\nتغییر فونت زمان کنار نام",
    "price": "💱 <b>قیمت ارز</b>\n\n<code>قیمت BTC</code>\n\nنمایش قیمت لحظه‌ای ارزها (تومانی و دلاری)",
    "spam": "🔁 <b>ارسال اسپم</b>\n\n<code>اسپم 10 سلام</code>\n\nارسال پیام تکراری (حداکثر ۵۰)",
    "format": "🎨 <b>فرمت خودکار HTML</b>\n\n<code>فرمت بولد روشن</code>\n<code>فرمت ریست</code>\n\nتبدیل خودکار پیام‌ها",
    "enemy": "👿 <b>مدیریت دشمنان</b>\n\n<code>دشمن</code> (ریپلای)\n<code>لیست دشمن</code>\n\nارسال خودکار فحش به دشمنان",
    "autoreply": "🤖 <b>پاسخ خودکار</b>\n\n<code>پاسخ افزودن سلام|سلام چطوری</code>\n\nتنظیم پاسخ خودکار برای کلمات",
    "insult": "💢 <b>مدیریت فحش‌ها</b>\n\n<code>فحش افزودن [متن]</code>\n\nمدیریت لیست فحش‌ها",
    "online": "🌐 <b>همیشه آنلاین</b>\n\n<code>آنلاین روشن</code>\n\nحالت همیشه آنلاین در تلگرام",
    "lock": "🔒 <b>قفل پیوی</b>\n\n<code>همه روشن</code>\n<code>مدیا روشن</code>\n\nمحدود کردن پیام‌ها در پیوی",
    "antilogin": "🛡️ <b>انتی لاگین</b>\n\n<code>انتی لاگین روشن</code>\n\nجلوگیری از هک اکانت",
    "reaction": "🎭 <b>ریکشن خودکار</b>\n\n<code>ریکت 😊</code> (ریپلای)\n\nاعمال ریکشن خودکار روی پیام‌های کاربر",
    "edit": "✏️ <b>ویرایش سریع</b>\n\n<code>ویرایش کلمه_قدیمی به کلمه_جدید</code>\n\nجایگزینی سریع کلمه",
    "banner": "📢 <b>سیستم بنر</b>\n\n<code>تنظیم بنر</code>\n<code>بنر همگانی 1</code>\n\nارسال همگانی به گروه‌ها",
    "download": "📥 <b>دانلودر تلگرام</b>\n\n<code>دانلود https://t.me/channel/123</code>\n\nدانلود پست کانال‌ها",
    "new": "🆕 <b>گروه/کانال</b>\n\n<code>پینگ</code>\n<code>تعداد کانال ها</code>\n<code>خروج همه گروه</code>",
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

<b>۴. سایر امکانات جدید:</b>
<code>پروفایل</code> (ریپلای روی عکس) - تغییر عکس
<code>بایو متن جدید</code> - تغییر بیوگرافی
<code>یوزر username</code> - تغییر آیدی
<code>یادداشت متن</code> - ثبت یادداشت
<code>ترجمه</code> (ریپلای) - ترجمه به فارسی
<code>آب و هوا تهران</code> - وضعیت آب و هوا
<code>بارکد متن</code> - ساخت QR Code
<code>حذف زمان‌دار 10</code> (ریپلای) - حذف پیام بعد از ۱۰ ثانیه
<code>پاکسازی</code> - پاک کردن تاریخچه چت
"""
}

def get_main_menu_page1(user_id):
    return InlineKeyboardMarkup([
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
    ])

def get_main_menu_page2(user_id):
    return InlineKeyboardMarkup([
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
    ])

def get_back_button(user_id, from_page=1):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=f"help_back_{user_id}_{from_page}", style=KeyboardButtonStyle(bg_primary=True))]])

def get_reopen_button(user_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 بازکردن پنل", callback_data=f"help_reopen_{user_id}", style=KeyboardButtonStyle(bg_success=True))]])

@app.on_message(filters.command("start") & filters.private)
async def show_menu(client, message):
    text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>"
    await message.reply_text(text, reply_markup=get_main_menu_page1(message.from_user.id), parse_mode=enums.ParseMode.HTML)

@app.on_inline_query()
async def inline_query_handler(client, inline_query):
    if inline_query.query.strip().lower() == "panel":
        user_id = inline_query.from_user.id
        results = [
            InlineQueryResultArticle(id="1", title="🎛 پنل مدیریت سلف - صفحه 1", description="10 قابلیت اصلی", input_message_content=InputTextMessageContent("<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>", parse_mode=enums.ParseMode.HTML), reply_markup=get_main_menu_page1(user_id)),
            InlineQueryResultArticle(id="2", title="🎛 پنل مدیریت سلف - صفحه 2", description="11 قابلیت تکمیلی", input_message_content=InputTextMessageContent("<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه دوم - 11 قابلیت تکمیلی</i>", parse_mode=enums.ParseMode.HTML), reply_markup=get_main_menu_page2(user_id))
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
    action = parts[1] if len(parts) > 1 else None
    page_num = int(parts[-1]) if len(parts) > 2 and parts[-1].isdigit() else 1
    
    if action == "close":
        await callback_query.edit_message_text("✅ <b>پنل بسته شد</b>\n\n💡 برای باز کردن مجدد:\n<code>@BotUsername panel</code>", reply_markup=get_reopen_button(user_id), parse_mode=enums.ParseMode.HTML)
    elif action in ["reopen", "page1"]:
        await callback_query.edit_message_text("<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>", reply_markup=get_main_menu_page1(user_id), parse_mode=enums.ParseMode.HTML)
    elif action == "page2":
        await callback_query.edit_message_text("<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه دوم - 11 قابلیت تکمیلی</i>", reply_markup=get_main_menu_page2(user_id), parse_mode=enums.ParseMode.HTML)
    elif action == "back":
        if page_num == 2:
            await callback_query.edit_message_text("<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه دوم - 11 قابلیت تکمیلی</i>", reply_markup=get_main_menu_page2(user_id), parse_mode=enums.ParseMode.HTML)
        else:
            await callback_query.edit_message_text("<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>", reply_markup=get_main_menu_page1(user_id), parse_mode=enums.ParseMode.HTML)
    elif action in HELP_TEXTS:
        await callback_query.edit_message_text(HELP_TEXTS[action], reply_markup=get_back_button(user_id, page_num), parse_mode=enums.ParseMode.HTML)
    else:
        await callback_query.answer(f"این بخش آماده نیست!", show_alert=True)
        
    await callback_query.answer()

if __name__ == "__main__":
    print("🤖 ربات هلپر اجرا شد")
    app.run()
