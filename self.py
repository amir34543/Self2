from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButtonStyle
from pyrogram.errors import SessionPasswordNeeded, MessageNotModified
import json, os, asyncio, subprocess, sys, time, threading, random
import html
from pyrogram import enums

# برای پهن‌تر شدن حباب پیام و در نتیجه کشیده‌تر شدن دکمه‌های اینلاین
# از فاصله‌های یونیکد در یک خط جدا استفاده می‌شود.
MENU_WIDTH_PAD = "\n" + ("\u2007" * 64)

async def safe_edit_message(message, *args, **kwargs):
    """ویرایش امن پیام؛ اگر متن/کیبورد تغییری نکرده بود خطا ندهد."""
    try:
        return await message.edit_text(*args, **kwargs)
    except MessageNotModified:
        return None

user_temp_codes = {}
active_clients = {}
BOT_TOKEN = "8876742932:AAHkfGQMsNEDH_bSQemz5p4NLdMtJOTOiTM"
API_ID = 35656061
API_HASH = "b37f2596516bc0439bf505d1d230395c"
ADMIN_ID = 7845464086

# تنظیمات منوی جدید
# یوزرنیم‌ها را بدون @ وارد کنید
SUPPORT_USERNAME = "Aliconfigs"
BUY_CHANNEL_USERNAME = "SelfPersiangulf"
HELPER_BOT_USERNAME = "Helpselfbotvippersian_bot"

os.makedirs("sessions", exist_ok=True)

# لیست کانال ها کم یا زیاد میتونید کنید بدون @
FORCE_CHANNELS = [
    "SH0PAL1",
]
