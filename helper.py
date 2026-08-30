from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
import logging

TOKEN = "8887093613:AAFkqOtkanU7E0qM4ArE8iQeOTBX4EtA9vU" # توکن ربات هلپر
API_ID = 35656061
API_HASH = "b37f2596516bc0439bf505d1d230395c"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client("helper_bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)

HELP_TEXTS = {
    "time": "⏰ <b>مدیریت تایم</b>\n\n<b>دستورات قابل کپی:</b>\n<code>تایم روشن</code>\n<code>تایم خاموش</code>\n\n<b>کاربرد:</b>\nنمایش زمان کنار نام کاربری",
    "instagram": "📥 <b>دانلودر اینستاگرام</b>\n\n<b>دستور قابل کپی:</b>\n<code>اینستا لینک_پست</code>",
    "id": "🆔 <b>سیستم آیدی پیشرفته</b>\n\n<b>دستور قابل کپی:</b>\n<code>ایدی</code>",
    "photo": "📸 <b>ذخیره عکس تایمدار</b>\n\n<b>دستور قابل کپی:</b>\n<code>عکس سیو</code> (ریپلای روی عکس)",
    "backup": "💾 <b>پشتیبان‌گیری</b>\n\n<b>دستور قابل کپی:</b>\n<code>سیو @یوزرنیم</code>",
    "font": "🔤 <b>مدیریت فونت</b>\n\n<b>دستورات قابل کپی:</b>\n<code>لیست فونت</code>\n<code>تنظیم فونت 1</code> تا <code>6</code>",
    "price": "💱 <b>قیمت ارز</b>\n\n<b>دستور قابل کپی:</b>\n<code>قیمت BTC</code>",
    "spam": "🔁 <b>ارسال اسپم</b>\n\n<b>دستور قابل کپی:</b>\n<code>اسپم 10 سلام</code>",
    "format": "🎨 <b>سیستم فرمت خودکار HTML</b>\n\n<b>دستورات:</b>\n<code>فرمت بولد روشن</code>\n<code>فرمت ریست</code>",
    "enemy": "👿 <b>مدیریت دشمنان</b>\n\n<b>دستورات:</b>\n<code>دشمن</code> (ریپلای)\n<code>لیست دشمن</code>",
    "autoreply": "🤖 <b>پاسخ خودکار</b>\n\n<b>دستورات:</b>\n<code>پاسخ افزودن سلام|سلام چطوری</code>",
    "insult": "💢 <b>مدیریت فحش‌ها</b>\n\n<b>دستورات:</b>\n<code>فحش افزودن [متن]</code>",
    "online": "🌐 <b>حالت همیشه آنلاین</b>\n\n<b>دستورات:</b>\n<code>آنلاین روشن</code>",
    "lock": "🔒 <b>سیستم قفل پیوی</b>\n\n<b>دستورات:</b>\n<code>همه روشن</code>\n<code>مدیا روشن</code>",
    "antilogin": "🛡️ <b>سیستم انتی لاگین</b>\n\n<b>دستورات:</b>\n<code>انتی لاگین روشن</code>",
    "reaction": "🎭 <b>سیستم ریکشن خودکار</b>\n\n<b>دستورات:</b>\n<code>ریکت 😊</code> (ریپلای)",
    "edit": "✏️ <b>ویرایش سریع پیام</b>\n\n<b>دستور:</b>\n<code>ویرایش کلمه_قدیمی به کلمه_جدید</code>",
    "banner": "📢 <b>سیستم مدیریت بنر</b>\n\n<b>دستورات:</b>\n<code>تنظیم بنر</code>\n<code>بنر همگانی 1</code>",
    "download": "📥 <b>دانلودر تلگرام</b>\n\n<b>دستور:</b>\n<code>دانلود https://t.me/channel/123</code>",
    "new": "🆕 <b>دستورات گروه/کانال</b>\n\n<code>پینگ</code>\n<code>تعداد کانال ها</code>",
}

def get_main_menu_page1(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("● ایدی ●", callback_data=f"help_id_{user_id}_1", style="primary"),
            InlineKeyboardButton("● تایم ●", callback_data=f"help_time_{user_id}_1", style="primary")
        ],
        [
            InlineKeyboardButton("● عکس تایمدار ●", callback_data=f"help_photo_{user_id}_1", style="primary"),
        ],
        [
            InlineKeyboardButton("● پشتیبان‌گیری ●", callback_data=f"help_backup_{user_id}_1", style="success"),
            InlineKeyboardButton("● مدیریت فونت ●", callback_data=f"help_font_{user_id}_1", style="success")
        ],
        [
            InlineKeyboardButton("● قیمت ارز ●", callback_data=f"help_price_{user_id}_1", style="success"),
        ],
        [
            InlineKeyboardButton("● فرمت متن ●", callback_data=f"help_format_{user_id}_1", style="danger"),
            InlineKeyboardButton("● اسپم ●", callback_data=f"help_spam_{user_id}_1", style="danger")
        ],
        [
            InlineKeyboardButton("● مدیریت دشمنان ●", callback_data=f"help_enemy_{user_id}_1", style="danger"),
        ],
        [
            InlineKeyboardButton("● پاسخ خودکار ●", callback_data=f"help_autoreply_{user_id}_1", style="primary"),
        ],
        [
            InlineKeyboardButton("● صفحه 2 → ●", callback_data=f"help_page2_{user_id}", style="success"),
            InlineKeyboardButton("● بست ●", callback_data=f"help_close_{user_id}", style="danger")
        ]
    ])

def get_main_menu_page2(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("● سیستم فحش ●", callback_data=f"help_insult_{user_id}_2", style="danger"),
            InlineKeyboardButton("● همیشه آنلاین ●", callback_data=f"help_online_{user_id}_2", style="danger")
        ],
        [
            InlineKeyboardButton("● قفل پیوی ●", callback_data=f"help_lock_{user_id}_2", style="danger"),
        ],
        [
            InlineKeyboardButton("●️ انتی لاگین ●", callback_data=f"help_antilogin_{user_id}_2", style="primary"),
            InlineKeyboardButton("● ریکشن خودکار ●", callback_data=f"help_reaction_{user_id}_2", style="primary")
        ],
        [
            InlineKeyboardButton("● ویرایش سریع ●", callback_data=f"help_edit_{user_id}_2", style="primary"),
        ],
        [
            InlineKeyboardButton("● سیستم بنر ●", callback_data=f"help_banner_{user_id}_2", style="success"),
            InlineKeyboardButton("● اینستاگرام ●", callback_data=f"help_instagram_{user_id}_2", style="success")
        ],
        [
            InlineKeyboardButton("● دانلود تلگرام ●", callback_data=f"help_download_{user_id}_2", style="success"),
        ],
        [
            InlineKeyboardButton("● مدیریت گروه/کانال ●", callback_data=f"help_new_{user_id}_2", style="primary"),
        ],
        [
            InlineKeyboardButton("← صفحه 1", callback_data=f"help_page1_{user_id}", style="primary"),
            InlineKeyboardButton("❌ بستن", callback_data=f"help_close_{user_id}", style="danger")
        ]
    ])

def get_back_button(user_id, from_page=1):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"help_back_{user_id}_{from_page}", style="primary")]
    ])

def get_reopen_button(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 بازکردن پنل", callback_data=f"help_reopen_{user_id}", style="success")]
    ])

@app.on_inline_query()
async def inline_query_handler(client, inline_query):
    query = inline_query.query.strip().lower()
    user_id = inline_query.from_user.id
    
    if query == "panel":
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
    
    if action == "close":
        text = "✅ <b>پنل بسته شد</b>\n\n💡 برای باز کردن مجدد:\n<code>@BotUsername panel</code>"
        await callback_query.message.edit_text(text, reply_markup=get_reopen_button(user_id), parse_mode=enums.ParseMode.HTML)
    elif action == "reopen" or action == "page1":
        text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>"
        await callback_query.message.edit_text(text, reply_markup=get_main_menu_page1(user_id), parse_mode=enums.ParseMode.HTML)
    elif action == "page2":
        text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه دوم - 11 قابلیت تکمیلی</i>"
        await callback_query.message.edit_text(text, reply_markup=get_main_menu_page2(user_id), parse_mode=enums.ParseMode.HTML)
    elif action == "back":
        if page_num == 2:
            text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه دوم - 11 قابلیت تکمیلی</i>"
            await callback_query.message.edit_text(text, reply_markup=get_main_menu_page2(user_id), parse_mode=enums.ParseMode.HTML)
        else:
            text = "<b>🎛 پنل مدیریت سلف</b>\n\n💡 <i>صفحه اول - 10 قابلیت اصلی</i>"
            await callback_query.message.edit_text(text, reply_markup=get_main_menu_page1(user_id), parse_mode=enums.ParseMode.HTML)
    elif action in HELP_TEXTS:
        text = HELP_TEXTS.get(action, "راهنمای این بخش آماده نیست.")
        await callback_query.message.edit_text(text, reply_markup=get_back_button(user_id, page_num), parse_mode=enums.ParseMode.HTML)
    else:
        await callback_query.answer(f"این بخش ({action}) آماده نیست!", show_alert=True)
        
    await callback_query.answer()

if __name__ == "__main__":
    print("🤖 ربات هلپر (Pyrogram) اجرا شد")
    app.run()
