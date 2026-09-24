from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButtonStyle, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from pyrogram.errors import SessionPasswordNeeded, MessageNotModified
import json, os, asyncio, subprocess, sys, time, threading, random
import html, re, zipfile, shutil
import logging
from pyrogram import enums

logging.basicConfig(level=logging.INFO)

# 💾 ذخیره‌سازی ماندگار: اگر Volume در /data مانت شده باشد،
# دیتابیس و سشن‌ها آنجا ذخیره می‌شوند تا با هر دیپلوی پاک نشوند
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.isdir("/data"):
    os.chdir("/data")
    os.makedirs("sessions", exist_ok=True)

MENU_WIDTH_PAD = "\n" + ("\u2007" * 64)

async def safe_edit_message(message, *args, **kwargs):
    """ویرایش امن پیام؛ اگر متن/کیبورد تغییری نکرده بود خطا ندهد."""
    try:
        return await message.edit_text(*args, **kwargs)
    except MessageNotModified:
        return None

# ==============================================================================
# 🔄 لوپ اصلی ربات — برای ارسال پیام از داخل تردهای تایمر (بدون بلاک شدن)
# ==============================================================================
BOT_LOOP = None

def send_async(coro):
    """ارسال امن پیام از داخل تردهای غیر-async (مثل تایمر ساعتی الماس)"""
    try:
        if BOT_LOOP is not None and BOT_LOOP.is_running():
            asyncio.run_coroutine_threadsafe(coro, BOT_LOOP)
        else:
            coro.close()
    except Exception as e:
        print(f"⚠️ خطا در ارسال پیام از ترد: {e}", flush=True)

user_temp_codes = {}
active_clients = {}
BOT_TOKEN = "8868043854:AAHblyKRa-DbGHefUp7q8_Zw675JTfBdgBw"
ADMIN_ID = 8953488723

SUPPORT_USERNAME = "Aliconfigs"
BUY_CHANNEL_USERNAME = "SelfPersiangulf"
HELPER_BOT_USERNAME = "Helpselfbotvippersian_bot"

os.makedirs("sessions", exist_ok=True)

FORCE_CHANNELS = [
    "SelfPersiangulf",
]

# ===== سیستم الماس 💎 =====
DIAMOND_RATE = 1440                 # 1440 الماس = 1 ماه (50,000 تومان)
PRICE_PER_MONTH = 50000             # تومان
TOMAN_PER_DIAMOND = PRICE_PER_MONTH / DIAMOND_RATE
ACTIVATION_COST = 2                 # ⚡ هزینه فعالسازی سلف (الماس)
card_info = {
    "card_number": "6037-1234-1234-1234",
    "card_owner": "نام صاحب کارت",
    "bank_name": "نام بانک"
}

ACTIVATION_TEXT = """🚀 **فعالسازی**

𝟏 ـ شما ابتدا الماس خود را از قسمت خرید الماس شارژ میکنید💎

𝟐 ـ سپس با زدن روی دکمه «📱 ارسال شماره» کد تلگرام برای شما ارسال میشود.. 📥

𝟑 ـ کد را به این صورت وارد میکنید 3.5.9.0.1 ، در صورت داشتن رمز دو مرحله ای آن را از شما میخواهد و آن را وارد میکنید.. 🔤

𝟒 ـ سلف روی اکانت شما با موفقیت فعال میشود .

𝟓 ـ فعالسازی با ۲ الماس 💙"""

# ===== 🎰 گردونه شانس =====
WHEEL_COOLDOWN = 86400              # روزی یک بار (ثانیه)
WHEEL_PRIZES = [5, 10, 15, 20, 25, 30, 50, 100]
WHEEL_WEIGHTS = [30, 25, 20, 12, 7, 4, 1.5, 0.5]

# ===== 🏆 لیدربورد =====
LEADERBOARD_PRIZES_TEXT = "💎 جوایزِ امشب: نفر اول ۲۰۰۰ / دوم ۱۰۰۰ / سوم ۵۰۰ الماس"

# ===== سیستم چند API_ID برای جلوگیری از محدودیت تلگرام =====
API_CREDENTIALS = [
    {"api_id": 35656061, "api_hash": "b37f2596516bc0439bf505d1d230395c"},
    {"api_id": 33452325, "api_hash": "57df08761ce14c556f3f0a7d09304246"}
]

def get_random_api():
    return random.choice(API_CREDENTIALS)

bot = Client("bot", bot_token=BOT_TOKEN, api_id=API_CREDENTIALS[0]["api_id"], api_hash=API_CREDENTIALS[0]["api_hash"])

admin_photo_wait = set()
admin_restore_wait = set()

class JSONDatabase:
    def __init__(self, filename="database.json"):
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                initial_data = {
                    "users": {},
                    "processes": {},
                    "temp_data": {},
                    "credits": {},
                    "timers": {},
                    "payments": {},
                    "group_bets": {},
                    "last_spin": {},
                    "last_play": {},
                    "settings": {
                        "diamond_rate": DIAMOND_RATE,
                        "toman_per_diamond": TOMAN_PER_DIAMOND,
                        "admin_id": ADMIN_ID
                    }
                }
                self.save_data(initial_data)
                return initial_data
        except Exception:
            return {
                "users": {}, "processes": {}, "temp_data": {},
                "credits": {}, "timers": {},
                "payments": {}, "group_bets": {},
                "last_spin": {}, "last_play": {}, "settings": {}
            }

    def save_data(self, data=None):
        try:
            if data:
                self.data = data
            temp_filename = f"{self.filename}.tmp"
            with open(temp_filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            os.replace(temp_filename, self.filename)
            return True
        except Exception as e:
            print(f"❌ خطا در ذخیره دیتابیس: {e}")
            return False

    def get(self, category, key, default=None):
        try:
            return self.data.get(category, {}).get(str(key), default)
        except:
            return default

    def set(self, category, key, value):
        try:
            if category not in self.data:
                self.data[category] = {}
            self.data[category][str(key)] = value
            return self.save_data()
        except Exception:
            return False

    def delete(self, category, key):
        try:
            if category in self.data and str(key) in self.data[category]:
                del self.data[category][str(key)]
                return self.save_data()
            return False
        except Exception:
            return False

    def get_all(self, category):
        try:
            return self.data.get(category, {})
        except:
            return {}

    def get_pending_payments(self):
        try:
            payments = self.data.get("payments", {})
            return {k: v for k, v in payments.items() if v.get('status') == 'pending'}
        except:
            return {}

db = JSONDatabase()
user_timers = {}

def save_bet_doz_image(file_id):
    db.data["bet_doz_image"] = file_id
    return db.save_data()

# ==============================================================================
# 💾 بکاپ و بازگردانی کامل (دیتابیس + سشن‌ها + فایل‌های وضعیت سلف‌ها)
# ==============================================================================
def make_backup_zip(out_path):
    count_sessions = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        if os.path.exists("database.json"):
            z.write("database.json", "database.json")
        if os.path.isdir("sessions"):
            for f in sorted(os.listdir("sessions")):
                p = os.path.join("sessions", f)
                if os.path.isfile(p) and f.endswith(".session"):
                    z.write(p, f"sessions/{f}")
                    count_sessions += 1
        for f in sorted(os.listdir(".")):
            if f.startswith("selfbot_state_") and f.endswith(".json"):
                z.write(f, f)
    return count_sessions

async def apply_restore(path):
    """توقف همه سلف‌ها → جایگزینی فایل‌ها → رفرش دیتابیس → روشن کردن مجدد سلف‌های فعال"""
    await asyncio.to_thread(stop_all_selfbots)
    restored_sessions = 0
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if "database.json" not in names:
                raise ValueError("فایل بکاپ معتبر نیست (دیتابیس داخلش پیدا نشد)")
            os.makedirs("sessions", exist_ok=True)
            z.extractall(".")
            restored_sessions = sum(1 for n in names if n.startswith("sessions/") and n.endswith(".session"))
    else:
        shutil.copyfile(path, "database.json")

    db.data = db.load_data()
    # ⚠️ PIDهای داخل بکاپ مال ماشین قبلی است — پاک می‌شوند تا پروسه اشتباهی کشته نشود
    db.data["processes"] = {}
    db.data["timers"] = {}
    db.save_data()

    restarted = 0
    for uid_s, info in db.get_all("users").items():
        try:
            uid = int(uid_s)
        except:
            continue
        if info.get("status") == "active" and db.get("credits", uid, 0) > 0:
            if await run_selfbot_async(uid, info.get("phone")):
                restarted += 1
    return restored_sessions, restarted

class UserTimer:
    def __init__(self, user_id, callback):
        self.user_id, self.callback, self.timer, self.is_running = user_id, callback, None, False

    def start(self):
        if self.is_running:
            self.stop()
        self.is_running = True
        self.timer = threading.Timer(3600, self._on_timer)
        self.timer.start()
        db.set("timers", self.user_id, {"start_time": time.time(), "is_running": True})

    def stop(self):
        if self.timer:
            self.timer.cancel()
        self.is_running = False
        db.delete("timers", self.user_id)

    def _on_timer(self):
        self.is_running = False
        db.delete("timers", self.user_id)
        self.callback(self.user_id)

def create_numpad_keyboard(prefix="code"):
    buttons = []
    buttons.append([
        InlineKeyboardButton("1️⃣", callback_data=f"{prefix}_1"),
        InlineKeyboardButton("2️⃣", callback_data=f"{prefix}_2"),
        InlineKeyboardButton("3️⃣", callback_data=f"{prefix}_3")
    ])
    buttons.append([
        InlineKeyboardButton("4️⃣", callback_data=f"{prefix}_4"),
        InlineKeyboardButton("5️⃣", callback_data=f"{prefix}_5"),
        InlineKeyboardButton("6️⃣", callback_data=f"{prefix}_6")
    ])
    buttons.append([
        InlineKeyboardButton("7️⃣", callback_data=f"{prefix}_7"),
        InlineKeyboardButton("8️⃣", callback_data=f"{prefix}_8"),
        InlineKeyboardButton("9️⃣", callback_data=f"{prefix}_9")
    ])
    buttons.append([
        InlineKeyboardButton("⌨️ پاک کن", callback_data=f"{prefix}_clear"),
        InlineKeyboardButton("0️⃣", callback_data=f"{prefix}_0"),
        InlineKeyboardButton("✅ ارسال", callback_data=f"{prefix}_send")
    ])
    buttons.append([
        InlineKeyboardButton("🔙 انصراف", callback_data=f"{prefix}_cancel")
    ])
    return InlineKeyboardMarkup(buttons)

def format_code_display(code):
    if not code:
        return "⚪.⚪.⚪.⚪.⚪"
    digits = list(code)
    while len(digits) < 5:
        digits.append("⚪")
    return ".".join(digits)

def share_phone_keyboard():
    """کیبورد با دکمه اشتراک‌گذاری شماره تلگرام (Warning + اشتراک‌گذاری سمت چپ)"""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📱 ارسال شماره", request_contact=True)],
            [KeyboardButton("❌ انصراف")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

async def complete_login(client, user_id, temp):
    """پس از ورود موفق: ذخیره اطلاعات، قطع کلاینت موقت و اجرای سلف"""
    user_info = {
        "phone": temp["phone"],
        "status": "active",
        "created_at": time.time(),
        "last_active": time.time(),
        "api_id": temp["api_id"],
        "api_hash": temp["api_hash"]
    }
    db.set("users", user_id, user_info)
    db.delete("temp_data", user_id)
    user_temp_codes.pop(user_id, None)

    if user_id in active_clients:
        try:
            await active_clients[user_id].disconnect()
        except:
            pass
        del active_clients[user_id]

    await asyncio.sleep(1)

    if await run_selfbot_async(user_id, temp["phone"]):
        credits = db.get("credits", user_id, 0)
        await client.send_message(
            user_id,
            f"✅ **سلف بات فعال شد!**\n\n"
            f"💎 الماس های شما: {credits:,}\n"
            f"⏰ زمان باقی‌مانده: {credits} ساعت",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await client.send_message(user_id, "❌ خطا در اجرای سلف بات", reply_markup=ReplyKeyboardRemove())

async def handle_code_from_keyboard(client, code_message):
    user_id = code_message.from_user.id
    code = code_message.text
    code = code.replace(".", "")

    temp_data = db.get("temp_data", user_id)

    if not temp_data:
        await client.send_message(user_id, "❌ اطلاعات یافت نشد\nلطفا دوباره شماره تلفن را ارسال کنید")
        return

    try:
        if user_id in active_clients:
            user_client = active_clients[user_id]
        else:
            session_name = f"sessions/{user_id}"
            user_client = Client(session_name, api_id=temp_data["api_id"], api_hash=temp_data["api_hash"])
            await user_client.connect()
            active_clients[user_id] = user_client

        try:
            await user_client.sign_in(temp_data["phone"], temp_data["phone_code_hash"], code)
        except SessionPasswordNeeded:
            await client.send_message(
                user_id,
                "🔒 **رمز دو مرحله‌ای نیاز است**\n\n"
                "لطفا رمز دو مرحله‌ای خود را به صورت متن ارسال کنید:"
            )
            db.set("temp_data", user_id, {**temp_data, "needs_password": True})
            return
        except Exception as e:
            err = str(e)
            if "PHONE_CODE_INVALID" in err:
                await client.send_message(user_id, "❌ **کد اشتباه است!**\nدوباره کد را وارد کنید.")
                return
            raise

        await complete_login(client, user_id, temp_data)

    except Exception as e:
        error_msg = str(e)
        if "PHONE_CODE_EXPIRED" in error_msg:
            await client.send_message(
                user_id,
                "❌ **کد منقضی شده!**\n\n"
                "لطفا دوباره روی «⚡ فعالسازی سلف» بزنید و شماره را بفرستید.",
                reply_markup=ReplyKeyboardRemove()
            )
            db.delete("temp_data", user_id)
            if user_id in active_clients:
                try:
                    await active_clients[user_id].disconnect()
                    del active_clients[user_id]
                except:
                    pass
        else:
            await client.send_message(user_id, f"❌ **خطا:** {error_msg}")

async def cancel_group_bet_if_no_joiner(client, bet_key):
    await asyncio.sleep(300)

    bet_data = db.get("group_bets", bet_key)
    if not bet_data or bet_data.get("finished"):
        return

    participants = bet_data.get("participants", [])
    chat_id = bet_data["chat_id"]
    message_id = bet_data["message_id"]
    amount = bet_data["amount"]
    creator_id = bet_data["creator_id"]
    creator_first_name = html.escape(bet_data.get('creator_name', 'کاربر'))
    creator_mention = f'<a href="tg://user?id={creator_id}"><b>{creator_first_name}</b></a>'

    if len(participants) > 0:
        return

    if bet_data.get("refunded"):
        return

    creator_credits = db.get("credits", creator_id, 0)
    db.set("credits", creator_id, creator_credits + amount)

    bet_data["finished"] = True
    bet_data["is_active"] = False
    bet_data["refunded"] = True
    db.set("group_bets", bet_key, bet_data)

    text = (
        "⛔ شرط به دلیل عدم شرکت‌کننده لغو شد.\n\n"
        f"👤 سازنده: {creator_mention}\n"
        f"💎 مبلغ شرط: <code>{amount:,}</code> الماس\n"
        "💸 مبلغ به سازنده برگشت داده شد."
    )

    try:
        await client.edit_message_text(chat_id, message_id, text, reply_markup=None, parse_mode=enums.ParseMode.HTML)
    except:
        pass

    try:
        await client.send_message(
            creator_id,
            f"⛔ **شرط شما لغو شد!**\n\n"
            f"به دلیل عدم شرکت‌کننده، شرط شما لغو شد.\n"
            f"💎 مبلغ شرط: <code>{amount:,}</code> الماس\n"
            f"💸 مبلغ به حساب شما برگشت داده شد.\n\n"
            f"📊 موجودی جدید شما: <code>{db.get('credits', creator_id, 0):,}</code> الماس"
        )
    except:
        pass

async def finish_group_bet(client, bet_key):
    await asyncio.sleep(5)

    bet_data = db.get("group_bets", bet_key)
    if not bet_data or bet_data.get("finished"):
        return

    chat_id = bet_data["chat_id"]
    message_id = bet_data["message_id"]
    amount = bet_data["amount"]
    creator_id = bet_data["creator_id"]
    creator_first_name = html.escape(bet_data.get('creator_name', 'کاربر'))
    creator_mention = f'<a href="tg://user?id={creator_id}"><b>{creator_first_name}</b></a>'
    participants = bet_data.get("participants", [])

    if len(participants) == 0:
        if not bet_data.get("refunded"):
            creator_credits = db.get("credits", creator_id, 0)
            db.set("credits", creator_id, creator_credits + amount)
            bet_data["refunded"] = True

        bet_data["finished"] = True
        bet_data["is_active"] = False
        db.set("group_bets", bet_key, bet_data)

        text = (
            "⛔ شرط به حد نصاب نرسید و لغو شد.\n\n"
            f"💎 مبلغ هر نفر: <code>{amount:,}</code> الماس\n"
            f"👤 سازنده: {creator_mention}"
        )
        try:
            await client.edit_message_text(chat_id, message_id, text, reply_markup=None, parse_mode=enums.ParseMode.HTML)
        except:
            pass
        return

    players = [{"id": creator_id, "name": bet_data.get('creator_name', 'کاربر')}] + participants
    player_ids = [creator_id] + [p["id"] for p in participants]
    player_mentions = [creator_mention]
    for p in participants:
        p_name = html.escape(p.get('name', 'کاربر'))
        player_mentions.append(f'<a href="tg://user?id={p["id"]}"><b>{p_name}</b></a>')

    gross_pot = (1 + len(participants)) * amount
    tax = int(gross_pot * 0.06)  # مالیات ۶٪ از مجموع شرط
    pot = gross_pot - tax

    winner_index = random.choice(range(len(players)))
    winner_id = player_ids[winner_index]
    winner_mention = player_mentions[winner_index]
    loser_index = 1 - winner_index if len(players) == 2 else None
    loser = players[loser_index] if loser_index is not None else None
    winner_credits = db.get("credits", winner_id, 0) + pot
    db.set("credits", winner_id, winner_credits)

    bet_data["finished"] = True
    bet_data["is_active"] = False
    bet_data["winner_id"] = winner_id
    bet_data["winner_name"] = players[winner_index].get("name", "کاربر")
    bet_data["pot"] = pot
    db.set("group_bets", bet_key, bet_data)

    loser_name = html.escape(loser.get("name", "کاربر")) if loser else "-"
    loser_id = loser.get("id", "-") if loser else "-"
    result_text = (
        "<b>◈ ━━━ selfisaz PersianGulf ━━━ ◈</b>\n"
        "<b>𝐕𝐈𝐏</b> | <b>نتیجه شرطبندی :</b>\n"
        f"<b>𝐕𝐈𝐏</b> | <b>برنده :</b> {html.escape(players[winner_index].get('name','کاربر'))} (<code>{winner_id}</code>)\n"
        f"<b>𝐕𝐈𝐏</b> | <b>بازنده :</b> {loser_name} (<code>{loser_id}</code>)\n"
        f"<b>𝐕𝐈𝐏</b> | <b>جایزه:</b> {pot:,} الماس\n"
        f"<b>𝐕𝐈𝐏</b> | <b>مالیات:</b> {tax:,} الماس\n"
        "◈ ━━━ <b>selfisaz PersianGulf</b> ━━━ ◈"
    )

    try:
        await client.edit_message_text(chat_id, message_id, result_text, reply_markup=None, parse_mode=enums.ParseMode.HTML)
    except:
        pass

    try:
        await client.send_message(
            chat_id,
            f"🏆 {winner_mention} برنده شرط <code>{amount:,}</code> الماسی شد و <b>{pot:,}</b> الماس دریافت کرد!",
            parse_mode=enums.ParseMode.HTML
        )
    except:
        pass
    try:
        await client.send_message(
            winner_id,
            f"🎉 **تبریک! شما برنده شرط شدید!**\n\n"
            f"💎 مبلغ شرط: <code>{amount:,}</code> الماس\n"
            f"💎 جایزه دریافتی: <b>{pot:,}</b> الماس\n"
            f"👥 تعداد بازیکنان: {len(players)} نفر\n\n"
            f"📊 موجودی جدید شما: <code>{db.get('credits', winner_id, 0):,}</code> الماس"
        )
    except:
        pass

    for player in players:
        if player["id"] != winner_id:
            try:
                await client.send_message(
                    player["id"],
                    f"😔 **متاسفانه شما در شرط باختید!**\n\n"
                    f"💎 مبلغ شرط: <code>{amount:,}</code> الماس\n"
                    f"👥 تعداد بازیکنان: {len(players)} نفر\n"
                    f"🏆 برنده: {winner_mention}\n\n"
                    f"📊 موجودی فعلی شما: <code>{db.get('credits', player['id'], 0):,}</code> الماس"
                )
            except:
                pass

async def check_force_join(client, user_id):
    not_joined = []
    for ch in FORCE_CHANNELS:
        try:
            member = await client.get_chat_member(ch, user_id)
            if member.status in ("kicked", "banned"):
                not_joined.append(ch)
        except:
            not_joined.append(ch)

    if not_joined:
        return False, not_joined

    return True, []

def deduct_diamond_callback(user_id):
    """هر ساعت ۱ الماس کم می‌شود؛ با تمام شدن الماس، سلف خاموش می‌شود"""
    try:
        if not db.get("processes", user_id):
            return
        credits = db.get("credits", user_id, 0)
        if credits > 0:
            new_credits = credits - 1
            db.set("credits", user_id, new_credits)
            print(f"⏳ [الماس] کاربر {user_id}: ۱ الماس کسر شد | باقی‌مانده: {new_credits}", flush=True)
            if new_credits <= 0:
                stop_selfbot(user_id, reason="الماس تمام شد")
                db.set("credits", user_id, 0)
                send_async(bot.send_message(
                    user_id,
                    "💎 **الماس های شما تمام شد!**\n\n"
                    "سلف بات متوقف شد.\n\n"
                    "💎 برای ادامه استفاده، از طریق منوی «خرید الماس» حساب خود را شارژ کنید."
                ))
            else:
                if user_id in user_timers:
                    user_timers[user_id].start()
        else:
            stop_selfbot(user_id, reason="الماس صفر بود")
            db.set("credits", user_id, 0)
            send_async(bot.send_message(
                user_id,
                "💎 **الماس های شما تمام شد!**\n\n"
                "سلف بات متوقف شد.\n\n"
                "💎 برای ادامه استفاده، از طریق منوی «خرید الماس» حساب خود را شارژ کنید."
            ))
    except Exception as e:
        print(f"❌ خطا در deduct_diamond_callback: {e}", flush=True)

def run_selfbot(user_id, phone=None):
    try:
        stop_selfbot(user_id)
        user_data = db.get("users", user_id, {})
        user_api_id = user_data.get("api_id", API_CREDENTIALS[0]["api_id"])
        user_api_hash = user_data.get("api_hash", API_CREDENTIALS[0]["api_hash"])

        self_path = os.path.join(BASE_DIR, "self.py")
        if phone:
            cmd = [sys.executable, self_path, str(user_id), phone, str(user_api_id), user_api_hash]
        else:
            cmd = [sys.executable, self_path, str(user_id), str(user_api_id), user_api_hash]

        # ⛔ اگر روزی SESSION_STRING در متغیرهای محیطی تعریف شد، نباید به
        # پروسه سلف کاربران ارث برسد وگرنه همه سلف‌ها روی یک اکانت می‌افتند
        env = os.environ.copy()
        env.pop("SESSION_STRING", None)

        process = subprocess.Popen(cmd, env=env)
        pid = process.pid

        db.set("processes", user_id, pid)

        with open(f"process_{user_id}.pid", "w") as f:
            f.write(str(pid))

        print(f"✅ سلف‌بات برای کاربر {user_id} راه‌اندازی شد | PID: {pid}", flush=True)
        if user_id not in user_timers:
            user_timers[user_id] = UserTimer(user_id, deduct_diamond_callback)
        user_timers[user_id].start()
        return True
    except Exception as e:
        print(f"❌ خطا در اجرای سلف‌بات: {e}", flush=True)
        return False

def stop_selfbot(user_id, reason=""):
    try:
        if user_id in user_timers:
            user_timers[user_id].stop()
            if not db.get("users", user_id):
                del user_timers[user_id]

        pid = db.get("processes", user_id)
        if pid:
            try:
                import signal
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(0.5)
                except:
                    pass
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except:
                    pass
                try:
                    # ⚠️ الگوی دقیق تا پیشوند آیدی یک کاربر، پروسه کاربر دیگر را نکشد
                    subprocess.run(["pkill", "-f", f"self\\.py {user_id}( |$)"], capture_output=True, check=False)
                except:
                    pass
            except Exception as e:
                print(f"⚠️ خطا در قطع پروسس: {e}")

            db.delete("processes", user_id)
            user_data = db.get("users", user_id, {})
            if user_data:
                user_data["status"] = "inactive"
                db.set("users", user_id, user_data)

            try:
                os.remove(f"process_{user_id}.pid")
            except:
                pass

            print(f"🛑 سلف‌بات کاربر {user_id} متوقف شد (PID: {pid})" + (f" | دلیل: {reason}" if reason else ""), flush=True)
            return True

        return False
    except Exception as e:
        print(f"❌ خطا در stop_selfbot: {e}", flush=True)
        return False

def stop_all_selfbots():
    try:
        for timer in list(user_timers.values()):
            timer.stop()
        user_timers.clear()
        for uid, pid in list(db.data.get("processes", {}).items()):
            try:
                os.kill(int(pid), 15)
            except:
                pass
            try:
                subprocess.run(["pkill", "-f", f"self\\.py {uid}( |$)"], capture_output=True, check=False)
            except:
                pass
        db.data["processes"], db.data["timers"] = {}, {}
        db.save_data()
    except:
        pass

async def run_selfbot_async(user_id, phone=None):
    """اجرای سلف بدون بلاک کردن ایونت‌لوپ بات"""
    return await asyncio.to_thread(run_selfbot, user_id, phone)

async def stop_selfbot_async(user_id, reason=""):
    return await asyncio.to_thread(stop_selfbot, user_id, reason)

# ==============================
# انتقال الماس بین کاربران گروه
# ==============================
@bot.on_message(filters.group & filters.reply & filters.regex(r'^انتقال\s+(\d+)\s*$'))
async def transfer_diamonds_handler(client, message: Message):
    sender_id = message.from_user.id
    recipient = message.reply_to_message.from_user if message.reply_to_message else None
    if not recipient:
        return
    recipient_id = recipient.id
    if recipient_id == sender_id:
        await message.reply_text("❌ نمی‌توانید به خودتان الماس انتقال دهید.")
        return
    amount = int(message.matches[0].group(1))
    if amount <= 0:
        await message.reply_text("❌ مقدار انتقال باید بیشتر از صفر باشد.")
        return
    sender_balance = db.get("credits", sender_id, 0)
    if sender_balance < amount:
        await message.reply_text(f"❌ موجودی الماس شما کافی نیست.\n\n💎 موجودی فعلی: {sender_balance:,} الماس")
        return
    if amount <= 5:
        fee_percent = random.choice([0, 0, 0, 1])
    elif amount <= 50:
        fee_percent = random.randint(0, 8)
    elif amount <= 500:
        fee_percent = random.randint(7, 12)
    else:
        fee_percent = random.randint(8, 15)
    fee = int(amount * fee_percent / 100)
    received_amount = amount - fee
    db.set("credits", sender_id, sender_balance - amount)
    recipient_balance = db.get("credits", recipient_id, 0) + received_amount
    db.set("credits", recipient_id, recipient_balance)
    sender_display = f"@{message.from_user.username}" if message.from_user.username else f"<a href=\"tg://user?id={sender_id}\">{html.escape(message.from_user.first_name or 'کاربر')}</a>"
    recipient_display = f"@{recipient.username}" if recipient.username else f"<a href=\"tg://user?id={recipient_id}\">{html.escape(recipient.first_name or 'کاربر')}</a>"
    transfer_text = (
        "✅ <b>انتقال موفق!</b>\n"
        "◈ ━━━ Persiangulf self ━━━ ◈\n"
        f"👤 <b>فرستنده:</b> {sender_display}\n"
        f"👤 <b>گیرنده:</b> {recipient_display}\n"
        f"💎 <b>مقدار دریافتی:</b> {received_amount:,} الماس\n"
        f"💵 <b>کارمزد ({fee_percent}٪):</b> {fee:,} الماس\n"
        "◈ ━━━ Persiangulf self ━━━ ◈\n"
        f"💎 <b>موجودی گیرنده:</b> {recipient_balance:,} الماس"
    )
    await message.reply_text(transfer_text, parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.group & filters.regex(r'^موجودی$'))
async def group_balance_simple(client, message: Message):
    user_id = message.from_user.id
    credits = db.get("credits", user_id, 0)
    toman_value = int(credits * TOMAN_PER_DIAMOND)
    text = "◈ ━━━ persiangulf self ━━━ ◈\n💎 <b>موجودی شما:</b>"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💎 {credits:,} الماس", callback_data="balance_noop", style=KeyboardButtonStyle(bg_primary=True))],
        [InlineKeyboardButton(f"💵 معادل {toman_value:,} تومان", callback_data="balance_noop", style=KeyboardButtonStyle(bg_success=True))]
    ])
    await message.reply_text(text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command("set") & filters.user(ADMIN_ID))
async def set_credits(client, message: Message):
    if len(message.command) != 3:
        await message.reply_text("❌ فرمت: `/set آیدی تعداد`")
        return

    try:
        target_id = int(message.command[1])
        amount = int(message.command[2])
        db.set("credits", target_id, amount)
        await message.reply_text(f"✅ الماس کاربر {target_id} روی {amount:,} تنظیم شد")
        try:
            await bot.send_message(target_id, f"🔧 موجودی شما تنظیم شد\n💎 جدید: {amount:,} الماس")
        except:
            pass
    except:
        await message.reply_text("❌ آیدی/تعداد باید عدد باشد")

@bot.on_message(filters.group & filters.regex(r'^شرطبندی\s+(\d+)(?:\s*الماس)?$'))
async def group_bet_handler(client, message: Message):
    chat_id = message.chat.id
    creator_id = message.from_user.id
    try:
        amount = int(message.matches[0].group(1))
    except:
        return
    if amount <= 0:
        await message.reply_text("❌ مقدار شرط باید بیشتر از صفر باشد.")
        return
    creator_credits = db.get("credits", creator_id, 0)
    if creator_credits < amount:
        await message.reply_text(f"❌ الماس کافی برای ساخت شرط ندارید.\n💎 موجودی شما: {creator_credits:,} الماس")
        return
    db.set("credits", creator_id, creator_credits - amount)
    db.set("last_play", creator_id, time.time())
    creator_first_name = html.escape(message.from_user.first_name or 'کاربر')
    creator_mention = f'<a href="tg://user?id={creator_id}"><b>{creator_first_name}</b></a>'
    bet_text = (
        "<b>◈ ━ selfisaz PersianGulf ━ ◈</b>\n<b>𝐕𝐈𝐏</b> | شرطبندی :\n"
        f"<b>𝐕𝐈𝐏</b> | {amount:,} الماس\n<b>𝐕𝐈𝐏</b> | سازنده: {creator_mention}\n<b>◈ ━ selfisaz PersianGulf ━ ◈</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("◈ ━ پیوستن ━ ◈", callback_data=f"joinbet_waiting", style=KeyboardButtonStyle(bg_success=True)),
            InlineKeyboardButton("❌ لغو", callback_data=f"cancelbet_waiting", style=KeyboardButtonStyle(bg_danger=True))
        ]
    ])
    bet_image = db.data.get("bet_doz_image")
    if bet_image:
        bet_msg = await message.reply_photo(photo=bet_image, caption=bet_text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    else:
        bet_msg = await message.reply_text(bet_text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    bet_key = f"{chat_id}_{bet_msg.id}"
    bet_data = {
        "chat_id": chat_id, "message_id": bet_msg.id, "amount": amount, "creator_id": creator_id,
        "creator_name": message.from_user.first_name or "", "creator_username": message.from_user.username or "",
        "participants": [], "is_active": True, "finished": False, "timer_started": False,
        "created_at": time.time(), "refunded": False
    }
    db.set("group_bets", bet_key, bet_data)
    try:
        new_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("◈ ━ پیوستن ━ ◈", callback_data=f"joinbet_{chat_id}_{bet_msg.id}", style=KeyboardButtonStyle(bg_success=True)),
                InlineKeyboardButton("❌ لغو", callback_data=f"cancelbet_{chat_id}_{bet_msg.id}", style=KeyboardButtonStyle(bg_danger=True))
            ]
        ])
        await bet_msg.edit_reply_markup(new_keyboard)
    except:
        pass
    asyncio.create_task(cancel_group_bet_if_no_joiner(client, bet_key))

@bot.on_message(filters.command("user") & filters.user(ADMIN_ID))
async def user_info(client, message: Message):
    if len(message.command) != 2:
        await message.reply_text("❌ فرمت: `/user آیدی`")
        return
    try:
        target_id = int(message.command[1])
        user_data = db.get("users", target_id, {})
        credits = db.get("credits", target_id, 0)
        process = db.get("processes", target_id)
        if not user_data:
            await message.reply_text("❌ کاربر یافت نشد")
            return
        status = "🟢 فعال" if user_data.get('status') == 'active' else "🔴 غیرفعال"
        phone = user_data.get('phone', '❌ ثبت نشده')
        created = time.ctime(user_data.get('created_at', time.time()))
        running = "🟢 بله" if process else "🔴 خیر"
        created_time = user_data.get('created_at', time.time())
        time_diff = time.time() - created_time
        days = int(time_diff // 86400); hours = int((time_diff % 86400) // 3600)
        info_text = f"""
👤 **اطلاعات کاربر {target_id}**
📱 **شماره:** `{phone}`
📊 **وضعیت:** {status}
💎 **الماس:** `{credits:,}`
🔄 **سلف:** {running}
📅 **تاریخ ایجاد:** `{created}`
⏳ **عضو شده:** {days} روز و {hours} ساعت
⏱ **زمان باقی‌مانده:** `{credits}` ساعت
💸 **مصرف:** 1 الماس در ساعت
"""
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎯 تنظیم الماس", callback_data=f"set_{target_id}"), InlineKeyboardButton("🛑 توقف سلف", callback_data=f"stop_{target_id}")]])
        await message.reply_text(info_text, reply_markup=keyboard)
    except:
        await message.reply_text("❌ آیدی باید عدد باشد")

@bot.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_panel(client, message: Message):
    users = db.data.get("users", {})
    active_count = len(db.data.get("processes", {}))
    total_credits = sum(db.data.get("credits", {}).values())
    pending_payments = len(db.get_pending_payments())
    today = time.time() - 86400
    new_today = sum(1 for user_data in users.values() if user_data.get("created_at", 0) > today)
    stats_text = (
        "🛠 **پنل مدیریت ادمین**\n\n"
        f"👥 **کل کاربران:** `{len(users)}`\n🟢 **کاربران فعال:** `{active_count}`\n"
        f"🆕 **کاربران امروز:** `{new_today}`\n💎 **مجموع الماس ها:** `{total_credits:,}`\n\n"
        f"📋 **درخواست‌های در انتظار:**\n└─ 💳 پرداخت: `{pending_payments}`\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزودن الماس به کاربر", callback_data="admin_add_diamond", style=KeyboardButtonStyle(bg_success=True))],
        [InlineKeyboardButton("🖼 مدیریت عکس شرط و دوز", callback_data="admin_photo_manager", style=KeyboardButtonStyle(bg_primary=True))],
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_list"), InlineKeyboardButton("📊 آمار کامل", callback_data="admin_stats")],
        [InlineKeyboardButton("🏆 برترین کاربران", callback_data="admin_top"), InlineKeyboardButton("🛑 توقف همه", callback_data="admin_stop_all")],
        [InlineKeyboardButton("💳 درخواست پرداخت", callback_data="admin_payments")],
        [InlineKeyboardButton("💎 الماس همگانی", callback_data="admin_global_coins", style=KeyboardButtonStyle(bg_success=True))],
        [InlineKeyboardButton("💾 دریافت دیتابیس", callback_data="db_download", style=KeyboardButtonStyle(bg_primary=True)),
         InlineKeyboardButton("📤 بازگردانی دیتابیس", callback_data="db_upload", style=KeyboardButtonStyle(bg_danger=True))]
    ])
    await message.reply_text(stats_text, reply_markup=keyboard)

@bot.on_callback_query(filters.regex(r'^code_'))
async def numpad_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    current_code = user_temp_codes.get(user_id, "")
    if data == "code_clear":
        user_temp_codes[user_id] = current_code[:-1]
        display_code = user_temp_codes[user_id]
        formatted = format_code_display(display_code)
        try:
            await safe_edit_message(callback_query.message, f"🔢 **کد تایید را وارد کنید:**\n\n<b><code>{formatted}</code></b>\n\n📱 کد {len(display_code)}/5 رقم وارد شد", reply_markup=create_numpad_keyboard(), parse_mode=enums.ParseMode.HTML)
        except:
            pass
        await callback_query.answer()
    elif data == "code_send":
        if len(current_code) == 5:
            await callback_query.answer("✅ کد ارسال شد...", show_alert=True)
            class FakeMessage:
                def __init__(self, user_id, code):
                    self.from_user = type('obj', (object,), {'id': user_id})()
                    self.text = code; self.chat = type('obj', (object,), {'id': user_id})(); self.reply_text = None
                async def reply_text(self, text, *args, **kwargs): await client.send_message(user_id, text, *args, **kwargs)
            fake_msg = FakeMessage(user_id, current_code)
            await handle_code_from_keyboard(client, fake_msg)
            user_temp_codes.pop(user_id, None)
        else:
            await callback_query.answer(f"❌ کد باید 5 رقم باشد (الان {len(current_code)} رقم)", show_alert=True)
    elif data == "code_cancel":
        user_temp_codes.pop(user_id, None)
        try:
            await safe_edit_message(callback_query.message, "❌ **ورود کد لغو شد**\n\nبرای شروع مجدد از /start استفاده کنید", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]))
        except:
            pass
        await callback_query.answer()
    else:
        number = data.split("_")[1]
        if len(current_code) < 5:
            new_code = current_code + number
            user_temp_codes[user_id] = new_code
            formatted = format_code_display(new_code)
            try:
                await safe_edit_message(callback_query.message, f"🔢 **کد تایید را وارد کنید:**\n\n<b><code>{formatted}</code></b>\n\n📱 کد {len(new_code)}/5 رقم وارد شد", reply_markup=create_numpad_keyboard(), parse_mode=enums.ParseMode.HTML)
            except:
                pass
            await callback_query.answer()
        else:
            await callback_query.answer("❌ کد کامل شده است! روی 'ارسال' کلیک کنید", show_alert=True)

# ==============================================================================
# 📱 فعالسازی: ارسال کد + کسر ۲ الماس (مشترک بین Contact و شماره تایپ‌شده)
# ==============================================================================
async def start_activation_with_phone(client, reply_target, uid, phone_digits):
    ok, chans = await check_force_join(client, uid)
    if not ok:
        rows = [[InlineKeyboardButton(f"📣 عضویت در {ch}", url=f"https://t.me/{ch}")] for ch in chans]
        rows.append([InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_join")])
        await client.send_message(uid, "⚠️ ابتدا در کانال عضو شوید:", reply_markup=InlineKeyboardMarkup(rows), disable_web_page_preview=True)
        return

    credits = db.get("credits", uid, 0)
    if credits < ACTIVATION_COST:
        await client.send_message(
            uid,
            f"💎 **الماس کافی ندارید!**\n\n"
            f"فعالسازی سلف به {ACTIVATION_COST} الماس نیاز دارد.\n"
            f"💎 موجودی شما: {credits:,} الماس\n\n"
            f"از منوی «خرید الماس» شارژ کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if not phone_digits.startswith("+"):
        phone_digits = "+" + phone_digits

    status_msg = await reply_target.reply_text("📱 در حال ارسال کد تایید...")

    # اگر سلف قبلی روشن است، اول خاموش شود (فایل سشن آزاد شود) — بدون بلاک شدن بات
    await stop_selfbot_async(uid)
    old = active_clients.pop(uid, None)
    if old:
        try:
            await old.disconnect()
        except:
            pass

    api = get_random_api()
    try:
        user_client = Client(f"sessions/{uid}", api_id=api["api_id"], api_hash=api["api_hash"])
        await user_client.connect()
        sent = await user_client.send_code(phone_digits)
        active_clients[uid] = user_client
        db.set("temp_data", uid, {
            "phone": phone_digits,
            "phone_code_hash": sent.phone_code_hash,
            "api_id": api["api_id"],
            "api_hash": api["api_hash"]
        })

        # 💙 کسر هزینه فعالسازی
        new_balance = db.get("credits", uid, 0) - ACTIVATION_COST
        db.set("credits", uid, max(0, new_balance))

        await status_msg.edit_text(
            "✅ **کد تایید ارسال شد!**\n\n"
            "🔢 کد ۵ رقمی را با کیبورد زیر وارد کنید:\n\n"
            f"💙 {ACTIVATION_COST} الماس بابت فعالسازی کسر شد."
        )
        await client.send_message(uid, "🔢 **ورود کد:**", reply_markup=create_numpad_keyboard())
    except Exception as e:
        err = str(e)
        try:
            if uid in active_clients:
                await active_clients[uid].disconnect()
                del active_clients[uid]
        except:
            pass
        if "PHONE_NUMBER_INVALID" in err:
            await status_msg.edit_text("❌ شماره نامعتبر است. با فرمت بین‌المللی بفرستید:\n`+989123456789`")
        elif "FLOOD" in err:
            await status_msg.edit_text("⏳ تلگرام محدودیت زمانی اعمال کرده. چند دقیقه دیگر دوباره تلاش کنید.")
        else:
            await status_msg.edit_text(f"❌ **خطا:** {err}")

# ==============================================================================
# 📱 دریافت شماره از دکمه اشتراک‌گذاری تلگرام (Contact)
# ==============================================================================
@bot.on_message(filters.private & filters.contact)
async def contact_share_handler(client, message: Message):
    uid = message.from_user.id
    c = message.contact

    # فقط شماره خود کاربر قابل قبول است
    if c.user_id and c.user_id != uid:
        await message.reply_text("❌ فقط **شماره خودتان** را به اشتراک بگذارید!")
        return

    phone_digits = re.sub(r'[^\d+]', '', c.phone_number or "")
    if not phone_digits:
        await message.reply_text("❌ شماره دریافت نشد. دوباره تلاش کنید.")
        return

    await message.reply_text("📲 شماره شما دریافت شد...")
    await start_activation_with_phone(client, message, uid, phone_digits)

# ==============================
# 📥 دریافت فایل بکاپ از ادمین
# ==============================
@bot.on_message(filters.user(ADMIN_ID) & filters.document)
async def restore_document_handler(client, message: Message):
    if ADMIN_ID not in admin_restore_wait:
        return
    admin_restore_wait.discard(ADMIN_ID)
    doc = message.document
    fname = doc.file_name or ""
    if not (fname.endswith(".zip") or fname == "database.json"):
        await message.reply_text("❌ فقط فایل بکاپ `.zip` یا فایل `database.json` قبول است.")
        return
    wait_msg = await message.reply_text("📥 **در حال بازگردانی...**\nسلف‌ها خاموش و فایل‌ها جایگزین می‌شوند...")
    path = await message.download()
    try:
        sessions_n, restarted = await apply_restore(path)
        await wait_msg.edit_text(
            f"✅ **بازگردانی کامل شد!**\n\n"
            f"📦 دیتابیس: ✅ جایگزین شد\n"
            f"🔐 سشن‌های بازگردانی‌شده: {sessions_n}\n"
            f"🚀 سلف‌های دوباره‌راه‌اندازی‌شده: {restarted}"
        )
    except Exception as e:
        await wait_msg.edit_text(f"❌ **خطا در بازگردانی:** {e}")
    finally:
        try:
            os.remove(path)
        except:
            pass

# ==============================
# 📸 عکس‌ها: رسید پرداخت کاربران + عکس شرط و دوز ادمین
# ==============================
@bot.on_message(filters.private & filters.photo)
async def private_photo_handler(client, message: Message):
    uid = message.from_user.id

    if uid == ADMIN_ID and uid in admin_photo_wait:
        admin_photo_wait.discard(uid)
        save_bet_doz_image(message.photo.file_id)
        await message.reply_text("✅ عکس شرط و دوز ذخیره شد.")
        return

    caption = message.caption or ""
    m = re.search(r'\d+', caption.replace(",", ""))
    if not m:
        await message.reply_text(
            "💎 برای ثبت درخواست خرید، تعداد الماس را **در کپشن عکس** بنویسید.\n"
            "مثال: `1440`"
        )
        return
    coins = int(m.group())
    if coins <= 0:
        await message.reply_text("❌ تعداد الماس باید بیشتر از صفر باشد.")
        return

    db.set("payments", uid, {
        "coins": coins,
        "status": "pending",
        "first_name": message.from_user.first_name or "ناشناس",
        "username": message.from_user.username or "",
        "ts": time.time()
    })

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"payment_approve_{uid}", style=KeyboardButtonStyle(bg_success=True)),
        InlineKeyboardButton("❌ رد پرداخت", callback_data=f"payment_reject_{uid}", style=KeyboardButtonStyle(bg_danger=True))
    ]])
    try:
        await bot.send_photo(
            ADMIN_ID, message.photo.file_id,
            caption=(f"💳 **درخواست خرید الماس**\n\n"
                     f"👤 کاربر: {html.escape(message.from_user.first_name or '')} | `{uid}`\n"
                     f"💎 تعداد: {coins:,} الماس"),
            reply_markup=kb
        )
        await message.reply_text("✅ رسید شما ارسال شد و در انتظار تایید مدیریت است.")
    except:
        await message.reply_text("❌ خطا در ارسال رسید. بعداً دوباره تلاش کنید.")

# ==============================
# 🏓 تست سلامت بات (قبل از روتر متن تا اولویت داشته باشد)
# ==============================
@bot.on_message(filters.command("ping") & filters.private)
async def ping_cmd(client, message):
    await message.reply_text(f"🏓 پونگ! بات زنده است ⏰ {time.strftime('%H:%M:%S')}")

# ==============================
# روتر پیام‌های متنی پیوی
# ==============================
@bot.on_message(filters.private & filters.text)
async def private_text_router(client, message: Message):
    uid = message.from_user.id
    t = (message.text or "").strip()

    # دستورات و انصراف
    if t.startswith("/"):
        if t.startswith("/cancel"):
            admin_restore_wait.discard(uid)
            admin_photo_wait.discard(uid)
            if uid == ADMIN_ID:
                db.delete("temp_data", f"admin_global_coins_{uid}")
                db.delete("temp_data", f"admin_set_{uid}")
                db.delete("temp_data", f"admin_add_uid_{uid}")
                db.delete("temp_data", f"admin_add_amount_{uid}")
            await message.reply_text("✅ لغو شد.", reply_markup=ReplyKeyboardRemove())
        return

    if t == "❌ انصراف":
        await message.reply_text("✅ لغو شد. برای شروع از /start استفاده کنید.", reply_markup=ReplyKeyboardRemove())
        return

    # ---------- ورودی‌های ادمین ----------
    if uid == ADMIN_ID:
        if db.get("temp_data", f"admin_add_uid_{uid}"):
            target = None
            display_name = "کاربر"
            t2 = t.strip()
            if re.fullmatch(r'\d{4,}', t2):
                target = int(t2)
                display_name = (db.get("users", target, {}) or {}).get("first_name", "کاربر")
            elif t2.startswith("@") and len(t2) > 4:
                try:
                    u = await client.get_users(t2)
                    target = u.id
                    display_name = u.first_name or "کاربر"
                except:
                    await message.reply_text("❌ کاربر با این یوزرنیم پیدا نشد. آیدی عددی بفرستید.")
                    return
            else:
                await message.reply_text("❌ آیدی عددی یا `@یوزرنیم` معتبر بفرستید.\n❌ لغو: `/cancel`")
                return
            db.set("temp_data", f"admin_add_amount_{uid}", target)
            db.delete("temp_data", f"admin_add_uid_{uid}")
            await message.reply_text(
                f"✅ کاربر پیدا شد: **{display_name}** (`{target}`)\n\n"
                "💎 حالا **مقدار الماس** را بفرستید:\n"
                "• مثال: `500` (افزودن)\n"
                "• عدد منفی: `-100` (کم کردن)\n\n"
                "❌ لغو: `/cancel`"
            )
            return

        admin_add_target = db.get("temp_data", f"admin_add_amount_{uid}")
        if admin_add_target is not None:
            try:
                amount = int(t.replace(",", ""))
            except:
                await message.reply_text("❌ لطفا فقط عدد بفرستید.")
                return
            target = int(admin_add_target)
            db.delete("temp_data", f"admin_add_amount_{uid}")
            current = db.get("credits", target, 0)
            new_balance = max(0, current + amount)
            db.set("credits", target, new_balance)
            sign = "➕" if amount >= 0 else "➖"
            await message.reply_text(
                f"✅ **انجام شد!**\n\n"
                f"{sign} {abs(amount):,} الماس برای کاربر `{target}`\n"
                f"💎 موجودی جدید: {new_balance:,} الماس"
            )
            try:
                await bot.send_message(target, f"🎁 **هدیه مدیریت!**\n\n{sign} {abs(amount):,} الماس به حساب شما اضافه شد.\n💎 موجودی جدید: {new_balance:,} الماس")
            except:
                pass
            return

        if db.get("temp_data", f"admin_global_coins_{uid}"):
            try:
                amount = int(t.replace(",", ""))
            except:
                await message.reply_text("❌ لطفا فقط عدد بفرستید.")
                return
            users = db.get_all("users")
            for u in users:
                db.set("credits", int(u), db.get("credits", int(u), 0) + amount)
            db.delete("temp_data", f"admin_global_coins_{uid}")
            await message.reply_text(f"✅ {amount:,} الماس به {len(users)} کاربر اضافه شد.")
            return

        admin_set_target = db.get("temp_data", f"admin_set_{uid}")
        if admin_set_target is not None:
            try:
                amount = int(t.replace(",", ""))
            except:
                await message.reply_text("❌ لطفا فقط عدد بفرستید.")
                return
            db.set("credits", int(admin_set_target), amount)
            db.delete("temp_data", f"admin_set_{uid}")
            await message.reply_text(f"✅ الماس کاربر {admin_set_target} روی {amount:,} تنظیم شد.")
            try:
                await bot.send_message(int(admin_set_target), f"🔧 موجودی شما تنظیم شد\n💎 جدید: {amount:,} الماس")
            except:
                pass
            return

    # ---------- رمز دو مرحله‌ای ----------
    temp = db.get("temp_data", uid)
    if temp and temp.get("needs_password"):
        user_client = active_clients.get(uid)
        if user_client is None:
            try:
                user_client = Client(f"sessions/{uid}", api_id=temp["api_id"], api_hash=temp["api_hash"])
                await user_client.connect()
                active_clients[uid] = user_client
            except Exception as e:
                await message.reply_text(f"❌ خطا در اتصال: {e}")
                db.delete("temp_data", uid)
                return
        try:
            await user_client.check_password(t)
            await complete_login(client, uid, temp)
        except Exception as e:
            if "PASSWORD_HASH_INVALID" in str(e):
                await message.reply_text("❌ **رمز اشتباه است!** دوباره رمز را بفرستید:")
            else:
                await message.reply_text(f"❌ **خطا:** {e}")
                db.delete("temp_data", uid)
        return

    # ---------- شماره تلفن تایپ‌شده (فالبک؛ روش اصلی دکمه اشتراک‌گذاری است) ----------
    phone_digits = re.sub(r'[\s\-()]', '', t)
    if re.fullmatch(r'\+?\d{10,14}', phone_digits):
        if not phone_digits.startswith("+"):
            phone_digits = "+" + phone_digits
        await start_activation_with_phone(client, message, uid, phone_digits)
        return

    await message.reply_text("🌸 برای شروع از دستور /start استفاده کنید.")

# ==============================
# 🎰 گردونه شانس
# ==============================
async def lucky_wheel_handler(client, callback_query):
    user_id = callback_query.from_user.id
    now = time.time()
    last = db.get("last_spin", user_id, 0) or 0
    remaining = WHEEL_COOLDOWN - (now - last)
    if remaining > 0:
        h = int(remaining // 3600)
        m = int((remaining % 3600) // 60)
        await callback_query.answer(f"⏳ شانس امروزت را گرفتی!\nدفععه بعد: {h} ساعت و {m} دقیقه دیگر", show_alert=True)
        return

    await callback_query.answer("🎰 گردونه در حال چرخش...")
    msg = callback_query.message
    spin_emojis = ["🎰", "💎", "⭐", "🍀", "🎲", "🔥"]

    for i in range(4):
        await asyncio.sleep(0.6)
        try:
            await msg.edit_text(
                f"{'  '.join(random.choices(spin_emojis, k=3))}\n\n"
                f"🔄 **گردونه در حال چرخش {'.' * (i + 1)}**"
            )
        except:
            pass

    prize = random.choices(WHEEL_PRIZES, weights=WHEEL_WEIGHTS)[0]
    db.set("credits", user_id, db.get("credits", user_id, 0) + prize)
    db.set("last_spin", user_id, now)

    result_text = (
        "🎉 **گردونه شانس — نتیجه!**\n\n"
        f"{'💎' * min(5, (prize // 20) + 1)}\n\n"
        f"🏆 **{prize} الماس** برنده شدی!\n\n"
        f"📊 موجودی جدید: **{db.get('credits', user_id, 0):,} الماس**\n\n"
        "⏰ ۲۴ ساعت دیگر دوباره امتحان کن!"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏆 لیدربورد", callback_data="leaderboard", style=KeyboardButtonStyle(bg_primary=True))],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]
    ])
    try:
        await msg.edit_text(result_text, reply_markup=kb)
    except:
        pass

# ==============================
# 🏆 لیدربورد
# ==============================
async def leaderboard_handler(client, callback_query):
    user_id = callback_query.from_user.id
    credits_all = db.get_all("credits")
    users_all = db.get_all("users")

    ranked = sorted(((int(k), int(v)) for k, v in credits_all.items()), key=lambda x: x[1], reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    shown = 0
    for uid_, bal in ranked:
        if shown >= 10:
            break
        if bal <= 0:
            continue
        info = users_all.get(str(uid_), {}) or {}
        name = (info.get("first_name") or "کاربر")[:22]
        name = html.escape(name)
        rank_icon = medals[shown] if shown < 3 else f"**{shown + 1}.**"
        lines.append(f"{rank_icon} <a href=\"tg://user?id={uid_}\">{name}</a> — 💎 {bal:,}")
        shown += 1

    if not lines:
        lines.append("هنوز کسی در جدول نیست — اولین نفر باش! 🚀")

    today_start = time.mktime(time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d"))
    last_play = db.get("last_play", user_id, 0) or 0
    if last_play >= today_start:
        play_line = "🎮 امروز بازی کردی! ادامه بده 💪"
    else:
        play_line = "🎮 تو امروز هنوز بازی نکردی — یه بازی بزن تا وارد جدول بشی!"

    lb_text = (
        "🏆 **لیدربورد — برترین‌های PersianGulf**\n\n"
        + "\n".join(lines)
        + "\n\n" + play_line
        + "\n" + LEADERBOARD_PRIZES_TEXT
    )

    my_rank = None
    for idx, (uid_, bal) in enumerate(ranked, 1):
        if uid_ == user_id:
            my_rank = idx
            break
    if my_rank:
        lb_text += f"\n\n📍 رتبه شما: **#{my_rank}** با 💎 {db.get('credits', user_id, 0):,} الماس"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 گردونه شانس", callback_data="lucky_wheel", style=KeyboardButtonStyle(bg_success=True))],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]
    ])
    await safe_edit_message(callback_query.message, lb_text, reply_markup=kb, parse_mode=enums.ParseMode.HTML)
    await callback_query.answer()

@bot.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data or ""

    if data in ("joinbet_waiting", "cancelbet_waiting"):
        await callback_query.answer("⏳ در حال آماده‌سازی شرط، لحظه‌ای صبر کنید...")
        return

    # ---------- پیوستن / لغو شرط‌بندی ----------
    if data.startswith("joinbet_"):
        try:
            _, chat_s, msg_s = data.split("_")
            key = f"{chat_s}_{msg_s}"
            bet = db.get("group_bets", key)
            if not bet or bet.get("finished"):
                await callback_query.answer("⛔ این شرط تمام شده است.", show_alert=True)
                return
            if bet["creator_id"] == user_id:
                await callback_query.answer("❌ نمی‌توانید با خودتان شرط ببندید!", show_alert=True)
                return
            if any(p["id"] == user_id for p in bet.get("participants", [])):
                await callback_query.answer("ℹ️ قبلاً به این شرط پیوسته‌اید.")
                return
            credits = db.get("credits", user_id, 0)
            if credits < bet["amount"]:
                await callback_query.answer(f"❌ الماس کافی ندارید. موجودی: {credits:,}", show_alert=True)
                return
            db.set("credits", user_id, credits - bet["amount"])
            db.set("last_play", user_id, time.time())
            bet.setdefault("participants", []).append({
                "id": user_id,
                "name": callback_query.from_user.first_name or "کاربر"
            })
            if not bet.get("timer_started"):
                bet["timer_started"] = True
                db.set("group_bets", key, bet)
                asyncio.create_task(finish_group_bet(client, key))
            else:
                db.set("group_bets", key, bet)
            joined_text = (
                "<b>◈ ━ selfisaz PersianGulf ━ ◈</b>\n"
                f"<b>𝐕𝐈𝐏</b> | شرطبندی : <code>{bet['amount']:,}</code> الماس\n"
                f"<b>𝐕𝐈𝐏</b> | سازنده: {html.escape(bet.get('creator_name','کاربر'))}\n"
                f"<b>𝐕𝐈𝐏</b> | حریف: {html.escape(callback_query.from_user.first_name or 'کاربر')}\n"
                "⏳ در حال تعیین برنده...\n"
                "<b>◈ ━ selfisaz PersianGulf ━ ◈</b>"
            )
            try:
                await client.edit_message_text(int(chat_s), int(msg_s), joined_text, reply_markup=None, parse_mode=enums.ParseMode.HTML)
            except:
                pass
            await callback_query.answer("✅ به شرط پیوستید! موفق باشی 🍀")
        except Exception as e:
            await callback_query.answer(f"⚠️ خطا: {str(e)[:80]}", show_alert=True)
        return

    if data.startswith("cancelbet_"):
        try:
            _, chat_s, msg_s = data.split("_")
            key = f"{chat_s}_{msg_s}"
            bet = db.get("group_bets", key)
            if not bet or bet.get("finished"):
                await callback_query.answer("⛔ این شرط تمام شده است.", show_alert=True)
                return
            if bet["creator_id"] != user_id:
                await callback_query.answer("⛔ فقط سازنده شرط می‌تواند لغو کند!", show_alert=True)
                return
            if not bet.get("refunded"):
                db.set("credits", user_id, db.get("credits", user_id, 0) + bet["amount"])
                bet["refunded"] = True
            bet["finished"] = True
            bet["is_active"] = False
            db.set("group_bets", key, bet)
            cancel_text = (
                "<b>◈ ━ selfisaz PersianGulf ━ ◈</b>\n"
                f"⛔ شرط <code>{bet['amount']:,}</code> الماسی توسط سازنده لغو شد.\n"
                "💸 مبلغ به سازنده برگشت داده شد.\n"
                "<b>◈ ━ selfisaz PersianGulf ━ ◈</b>"
            )
            try:
                await client.edit_message_text(int(chat_s), int(msg_s), cancel_text, reply_markup=None, parse_mode=enums.ParseMode.HTML)
            except:
                pass
            await callback_query.answer("✅ شرط لغو و مبلغ برگشت داده شد.")
        except Exception as e:
            await callback_query.answer(f"⚠️ خطا: {str(e)[:80]}", show_alert=True)
        return

    if data == "lucky_wheel":
        await lucky_wheel_handler(client, callback_query)
        return

    if data == "leaderboard":
        await leaderboard_handler(client, callback_query)
        return

    # ---------- منوی اصلی ----------
    if data == "referral":
        bot_info = await client.get_me()
        referral_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        refs = (db.get("users", user_id, {}) or {}).get("referrals", 0)
        referral_text = (
            "👥 **سیستم زیرمجموعه**\n\n"
            "با لینک اختصاصی خود دوستانتان را به ربات دعوت کنید.\n"
            "🎁 به ازای هر نفر: **+۳ الماس هدیه**\n\n"
            f"📊 زیرمجموعه‌های شما: **{refs}**\n\n"
            f"🔗 **لینک دعوت شما:**\n`{referral_link}`"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]])
        await safe_edit_message(callback_query.message, referral_text, reply_markup=keyboard)
        await callback_query.answer()
        return

    if data == "buy_guide":
        guide_text = (
            "📖 **راهنمای خرید و فعالسازی سلف**\n\n"
            "1️⃣ از «💎 خرید الماس» الماس تهیه کنید (هر ۱ الماس = ۱ ساعت سلف)\n"
            "2️⃣ روی «⚡ فعالسازی سلف» بزنید و «📱 ارسال شماره» را بزنید\n"
            "3️⃣ کد ۵ رقمی تلگرام را با کیبورد عددی وارد کنید\n"
            "4️⃣ تمام! سلف شما فعال شد ✨\n\n"
            f"💙 هزینه فعالسازی: {ACTIVATION_COST} الماس"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ فعالسازی سلف", callback_data="activate_self", style=KeyboardButtonStyle(bg_success=True))],
            [InlineKeyboardButton("💎 خرید الماس", callback_data="increase_balance", style=KeyboardButtonStyle(bg_primary=True))],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]
        ])
        await safe_edit_message(callback_query.message, guide_text, reply_markup=keyboard)
        await callback_query.answer()
        return

    if data == "support":
        if not SUPPORT_USERNAME or SUPPORT_USERNAME == "YourSupportUsername":
            await callback_query.answer("⚠️ یوزرنیم پشتیبانی هنوز تنظیم نشده است.", show_alert=True)
            return
        support_text = "👨‍💻 **پشتیبانی**\n\nبرای ارتباط با پشتیبانی روی دکمه زیر کلیک کنید."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 ارتباط با پشتیبانی", url=f"https://t.me/{SUPPORT_USERNAME}", style=KeyboardButtonStyle(bg_success=True))],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]
        ])
        await safe_edit_message(callback_query.message, support_text, reply_markup=keyboard)
        await callback_query.answer()
        return

    if data == "buy_channel":
        if not BUY_CHANNEL_USERNAME or BUY_CHANNEL_USERNAME == "YourChannelUsername":
            await callback_query.answer("⚠️ یوزرنیم کانال خرید هنوز تنظیم نشده است.", show_alert=True)
            return
        channel_text = "📣 **کانال خرید**\n\nبرای مشاهده اطلاعات خرید و اطلاعیه‌ها وارد کانال شوید."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📣 ورود به کانال", url=f"https://t.me/{BUY_CHANNEL_USERNAME}", style=KeyboardButtonStyle(bg_success=True))],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]
        ])
        await safe_edit_message(callback_query.message, channel_text, reply_markup=keyboard)
        await callback_query.answer()
        return

    if data == "help":
        help_text = (
            "📢 **راهنمای سلف بات**\n\n"
            "⚡ فعالسازی: «⚡ فعالسازی سلف» ← «📱 ارسال شماره» ← وارد کردن کد ۵ رقمی\n\n"
            f"💙 هزینه فعالسازی: {ACTIVATION_COST} الماس\n"
            "💎 هر ۱ الماس = ۱ ساعت سلف فعال\n"
            "🎰 گردونه شانس: روزی یک بار الماس رایگان!\n"
            "🎲 شرطبندی گروهی: در گروه بنویسید `شرطبندی 100`\n"
            "🎁 زیرمجموعه: +۳ الماس برای هر دعوت"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]])
        await safe_edit_message(callback_query.message, help_text, reply_markup=keyboard)
        await callback_query.answer()
        return

    if data == "status_credits":
        u = db.get("users", user_id, {}) or {}
        credits = db.get("credits", user_id, 0)
        status = "🟢 فعال" if u.get("status") == "active" else "🔴 غیرفعال"
        phone = u.get("phone", "ثبت نشده")
        text = (
            "👤 **حساب کاربری شما**\n\n"
            f"💎 الماس: `{credits:,}`\n"
            f"⏰ زمان باقی‌مانده: `{credits}` ساعت\n"
            f"📊 وضعیت سلف: {status}\n"
            f"📱 شماره: `{phone}`"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ فعالسازی سلف", callback_data="activate_self", style=KeyboardButtonStyle(bg_success=True))],
            [InlineKeyboardButton("⚙️ مدیریت بات", callback_data="self_management", style=KeyboardButtonStyle(bg_primary=True))],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]
        ])
        await safe_edit_message(callback_query.message, text, reply_markup=keyboard)
        await callback_query.answer()
        return

    if data == "activation_guide":
        text = (
            "💎 **پکیج‌های الماس**\n\n"
            "⚡ هر **۱ الماس = ۱ ساعت** سلف فعال\n\n"
            f"📦 پکیج پیشنهادی:\n"
            f"• {DIAMOND_RATE:,} الماس (۱ ماه) = {PRICE_PER_MONTH:,} تومان\n\n"
            "👇 برای خرید، مبلغ را واریز کنید و عکس رسید را با کپشنِ تعداد الماس بفرستید."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 خرید الماس", callback_data="increase_balance", style=KeyboardButtonStyle(bg_success=True))],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]
        ])
        await safe_edit_message(callback_query.message, text, reply_markup=keyboard)
        await callback_query.answer()
        return

    if data == "increase_balance":
        text = (
            "💳 **خرید الماس**\n\n"
            f"🏦 بانک: {card_info['bank_name']}\n"
            f"💳 شماره کارت:\n`{card_info['card_number']}`\n"
            f"👤 به نام: {card_info['card_owner']}\n\n"
            f"💎 هر {DIAMOND_RATE:,} الماس (۱ ماه) = {PRICE_PER_MONTH:,} تومان\n\n"
            "📌 **مراحل:**\n"
            "1️⃣ مبلغ را واریز کنید\n"
            "2️⃣ عکس رسید را بفرستید و **در کپشن تعداد الماس** را بنویسید\n"
            "3️⃣ بعد از تایید مدیر، الماس اضافه می‌شود"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]])
        await safe_edit_message(callback_query.message, text, reply_markup=keyboard)
        await callback_query.answer()
        return

    if data == "self_management":
        u = db.get("users", user_id, {}) or {}
        credits = db.get("credits", user_id, 0)
        status = "🟢 فعال" if u.get("status") == "active" else "🔴 غیرفعال"
        text = (
            "⚙️ **مدیریت سلف بات**\n\n"
            f"📊 وضعیت: {status}\n"
            f"💎 الماس: `{credits:,}`\n"
            f"⏰ زمان باقی‌مانده: `{credits}` ساعت\n\n"
            "💡 با «⚡ فعالسازی سلف» سلف شما ساخته و روشن می‌شود."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ فعالسازی سلف", callback_data="activate_self", style=KeyboardButtonStyle(bg_success=True))],
            [InlineKeyboardButton("🛑 خاموش کردن سلف", callback_data="stop_self", style=KeyboardButtonStyle(bg_danger=True))],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]
        ])
        await safe_edit_message(callback_query.message, text, reply_markup=keyboard)
        await callback_query.answer()
        return

    # ---------- ⚡ فعالسازی سلف: متن راهنما + دکمه اشتراک‌گذاری شماره ----------
    if data in ("activate_self", "start_login"):
        ok, chans = await check_force_join(client, user_id)
        if not ok:
            await callback_query.answer("⚠️ ابتدا در کانال عضو شوید!", show_alert=True)
            return
        credits = db.get("credits", user_id, 0)
        if credits < ACTIVATION_COST:
            await callback_query.answer(f"💎 الماس کافی ندارید! فعالسازی {ACTIVATION_COST} الماس است. موجودی شما: {credits:,}", show_alert=True)
            return

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 خرید الماس", callback_data="increase_balance", style=KeyboardButtonStyle(bg_primary=True))],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back", style=KeyboardButtonStyle(bg_primary=True))]
        ])
        try:
            await safe_edit_message(callback_query.message, ACTIVATION_TEXT, reply_markup=kb, parse_mode=enums.ParseMode.HTML)
        except:
            pass

        # 📱 کیبورد با دکمه اشتراک‌گذاری شماره تلگرام (Warning + اشتراک‌گذاری)
        await client.send_message(
            user_id,
            f"👇 روی دکمه پایین بزنید و «اشتراک‌گذاری» را تایید کنید\n"
            f"(💙 هزینه فعالسازی: {ACTIVATION_COST} الماس)",
            reply_markup=share_phone_keyboard()
        )
        await callback_query.answer()
        return

    if data == "stop_self":
        if await stop_selfbot_async(user_id):
            await callback_query.answer("🛑 سلف شما خاموش شد.", show_alert=True)
        else:
            await callback_query.answer("ℹ️ سلف شما از قبل خاموش بود.", show_alert=True)
        return

    if data == "back":
        text = (
            "**🌺 منوی اصلی ربات سلف ساز**\n\n"
            "از دکمه‌های زیر استفاده کنید."
        )
        await safe_edit_message(callback_query.message, text, reply_markup=create_main_menu(user_id))
        await callback_query.answer()
        return

    if data == "balance_noop":
        await callback_query.answer("💎")
        return

    if data == "check_join":
        ok, chans = await check_force_join(client, user_id)
        if ok:
            await callback_query.answer("✅ عضویت تایید شد!", show_alert=True)
            await show_main_menu(client, user_id, callback_query.from_user)
        else:
            await callback_query.answer("❌ هنوز عضو کانال نشده‌اید!", show_alert=True)
        return

    if user_id == ADMIN_ID:
        await admin_callback_handler(client, callback_query)
    else:
        await callback_query.answer()

async def admin_callback_handler(client, callback_query):
    data = callback_query.data; user_id = callback_query.from_user.id

    # ---------- 💾 بکاپ و بازگردانی دیتابیس ----------
    if data == "db_download":
        await callback_query.answer("📦 در حال ساخت بکاپ...")
        path = f"backup_{time.strftime('%Y%m%d_%H%M')}.zip"
        try:
            n_sessions = await asyncio.to_thread(make_backup_zip, path)
            size_kb = os.path.getsize(path) // 1024
            await client.send_document(
                user_id, path,
                caption=(f"💾 **بکاپ کامل PersianGulf**\n\n"
                         f"📦 شامل: database.json + {n_sessions} سشن + فایل‌های وضعیت\n"
                         f"⚖️ حجم: {size_kb} KB\n🕘 زمان: {time.strftime('%Y-%m-%d %H:%M')}\n\n"
                         f"💡 برای بازگردانی: دکمه «📤 بازگردانی دیتابیس» را بزنید و همین فایل را بفرستید")
            )
        except Exception as e:
            await client.send_message(user_id, f"❌ خطا در ساخت بکاپ: {e}")
        finally:
            try:
                os.remove(path)
            except:
                pass
        return

    if data == "db_upload":
        admin_restore_wait.add(user_id)
        await safe_edit_message(
            callback_query.message,
            "📤 **بازگردانی دیتابیس**\n\n"
            "فایل بکاپ (`.zip`) یا فایل `database.json` را **همین‌جا** بفرستید.\n\n"
            "⚠️ **توجه:**\n"
            "• همه سلف‌ها اول خاموش می‌شوند\n"
            "• دیتابیس و سشن‌ها جایگزین می‌شوند\n"
            "• سلف کاربران فعال خودکار دوباره روشن می‌شود\n\n"
            "❌ برای لغو: `/cancel`"
        )
        await callback_query.answer()
        return

    # ---------- ➕ افزودن الماس به کاربر ----------
    if data == "admin_add_diamond":
        db.set("temp_data", f"admin_add_uid_{user_id}", True)
        await safe_edit_message(
            callback_query.message,
            "➕ **افزودن الماس به کاربر**\n\n"
            "🆔 **آیدی کاربر را بفرستید:**\n"
            "• آیدی عددی: `8953488723`\n"
            "• یا یوزرنیم: `@username`\n\n"
            "❌ لغو: `/cancel`"
        )
        await callback_query.answer()
        return

    if data == "admin_list":
        users = db.get_all("users")
        if not users:
            await safe_edit_message(callback_query.message, "❌ هیچ کاربری ثبت نشده است.")
            return
        text = "👥 **لیست کاربران:**\n\n"
        for i, (uid, info) in enumerate(list(users.items())[:20], 1):
            credits = db.get("credits", int(uid), 0)
            status = "🟢" if info.get('status') == 'active' else "🔴"
            text += f"{i}. {status} `{uid}` → {credits:,} الماس\n"
        if len(users) > 20:
            text += f"\n... و {len(users) - 20} کاربر دیگر"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]])
        await safe_edit_message(callback_query.message, text, reply_markup=keyboard)
        await callback_query.answer()
    elif data == "admin_stats":
        users = db.get_all("users"); processes = db.get_all("processes"); credits = db.get_all("credits"); payments = db.get_all("payments")
        total_users = len(users); active_users = len(processes); total_credits = sum(credits.values()) if credits else 0
        pending_pay = sum(1 for p in payments.values() if p.get('status') == 'pending')
        text = f"📊 **آمار کامل سیستم**\n\n👥 **کاربران کل:** {total_users}\n🟢 **فعال:** {active_users}\n💎 **مجموع الماس‌ها:** {total_credits:,}\n\n💳 **درخواست پرداخت:** {pending_pay}\n\n📅 **تاریخ:** {time.ctime()}"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]])
        await safe_edit_message(callback_query.message, text, reply_markup=keyboard)
        await callback_query.answer()
    elif data == "admin_top":
        credits = db.get_all("credits")
        if not credits:
            await safe_edit_message(callback_query.message, "❌ هیچ کاربری الماس ندارد.")
            return
        sorted_users = sorted(credits.items(), key=lambda x: x[1], reverse=True)[:10]
        text = "🏆 **برترین کاربران از نظر الماس:**\n\n"
        for i, (uid, amount) in enumerate(sorted_users, 1):
            user_data = db.get("users", int(uid), {})
            name = user_data.get('first_name', 'ناشناس')
            text += f"{i}. {name} → `{amount:,}` الماس\n"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]])
        await safe_edit_message(callback_query.message, text, reply_markup=keyboard)
        await callback_query.answer()
    elif data == "admin_stop_all":
        await safe_edit_message(callback_query.message, "🛑 **در حال توقف همه سلف‌بات‌ها...**")
        await asyncio.to_thread(stop_all_selfbots)
        await safe_edit_message(callback_query.message, "✅ **همه سلف‌بات‌ها متوقف شدند.**")
        await callback_query.answer()
    elif data == "admin_payments":
        payments = db.get_pending_payments()
        if not payments:
            await safe_edit_message(callback_query.message, "❌ هیچ درخواست پرداخت در انتظاری وجود ندارد.")
            return
        text = "💳 **درخواست‌های پرداخت:**\n\n"
        for uid, info in list(payments.items())[:10]:
            name = info.get('first_name', 'ناشناس')
            coins = info.get('coins', 0)
            text += f"👤 {name} → `{uid}` | {coins:,} الماس\n"
        if len(payments) > 10:
            text += f"\n... و {len(payments) - 10} درخواست دیگر"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]])
        await safe_edit_message(callback_query.message, text, reply_markup=keyboard)
        await callback_query.answer()
    elif data == "admin_photo_manager":
        if user_id != ADMIN_ID:
            await callback_query.answer("⛔ دسترسی ندارید.", show_alert=True)
            return
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال عکس جدید", callback_data="set_bet_photo")], [InlineKeyboardButton("🗑 حذف عکس", callback_data="del_bet_photo")], [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_back")]])
        status = "عکس ذخیره شده: ✅ فعال" if db.data.get("bet_doz_image") else "عکس ذخیره شده: ❌ ندارد"
        await safe_edit_message(callback_query.message, f"🖼 **مدیریت عکس شرط و دوز**\n\n{status}", reply_markup=kb)
        await callback_query.answer()
    elif data == "set_bet_photo":
        if user_id != ADMIN_ID:
            await callback_query.answer("⛔ دسترسی ندارید.", show_alert=True)
            return
        admin_photo_wait.add(user_id)
        await callback_query.answer("✅ حالا عکس را ارسال کنید.")
        await client.send_message(user_id, "📤 **عکس جدید شرط و دوز را ارسال کنید.**")
    elif data == "del_bet_photo":
        if user_id != ADMIN_ID:
            await callback_query.answer("⛔ دسترسی ندارید.", show_alert=True)
            return
        db.data.pop("bet_doz_image", None)
        ok = db.save_data()
        if ok:
            await callback_query.answer("✅ عکس حذف شد.", show_alert=True)
        else:
            await callback_query.answer("❌ ذخیره تغییرات ناموفق بود.", show_alert=True)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال عکس جدید", callback_data="set_bet_photo")], [InlineKeyboardButton("🗑 حذف عکس", callback_data="del_bet_photo")], [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_back")]])
        await safe_edit_message(callback_query.message, "🖼 **مدیریت عکس شرط و دوز**\n\nعکس ذخیره شده: ❌ ندارد", reply_markup=kb)
    elif data == "admin_global_coins":
        db.set("temp_data", f"admin_global_coins_{user_id}", True)
        await safe_edit_message(callback_query.message, "💎 تعداد الماسی که می‌خواهید به همه کاربران اضافه شود را ارسال کنید:")
        await callback_query.answer()
    elif data == "admin_back":
        await admin_panel(client, callback_query.message)
        await callback_query.answer()
    elif data.startswith("set_"):
        target_id = int(data.split("_")[1])
        db.set("temp_data", f"admin_set_{user_id}", target_id)
        await safe_edit_message(callback_query.message, f"💎 **تعداد الماس جدید برای کاربر {target_id} را وارد کنید:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="admin_back")]]))
        await callback_query.answer()
    elif data.startswith("stop_"):
        target_id = int(data.split("_")[1])
        if await stop_selfbot_async(target_id):
            await safe_edit_message(callback_query.message, f"✅ سلف‌بات کاربر {target_id} متوقف شد.")
        else:
            await safe_edit_message(callback_query.message, f"ℹ️ سلف‌بات کاربر {target_id} از قبل متوقف بود.")
        await callback_query.answer()
    elif data.startswith("payment_approve_"):
        target_id = int(data.split("_")[2])
        payment_data = db.get("payments", target_id)
        if payment_data:
            coins = payment_data.get("coins", 0)
            current = db.get("credits", target_id, 0)
            db.set("credits", target_id, current + coins)
            payment_data["status"] = "approved"
            db.set("payments", target_id, payment_data)
            await safe_edit_message(callback_query.message, f"✅ پرداخت کاربر {target_id} تایید شد.\n💎 {coins:,} الماس به حسابش اضافه شد.")
            try:
                await bot.send_message(target_id, f"✅ **پرداخت شما تایید شد!**\n\n💎 {coins:,} الماس به حساب شما اضافه شد.\n📊 موجودی جدید: {db.get('credits', target_id, 0):,} الماس")
            except:
                pass
        else:
            await safe_edit_message(callback_query.message, f"❌ اطلاعات پرداخت کاربر {target_id} یافت نشد.")
        await callback_query.answer()
    elif data.startswith("payment_reject_"):
        target_id = int(data.split("_")[2])
        payment_data = db.get("payments", target_id)
        if payment_data:
            payment_data["status"] = "rejected"
            db.set("payments", target_id, payment_data)
            await safe_edit_message(callback_query.message, f"❌ پرداخت کاربر {target_id} رد شد.")
            try:
                await bot.send_message(target_id, "❌ **پرداخت شما رد شد!**\n\nلطفا مجدداً با ارسال رسید واضح‌تر اقدام کنید.")
            except:
                pass
        else:
            await safe_edit_message(callback_query.message, f"❌ اطلاعات پرداخت کاربر {target_id} یافت نشد.")
        await callback_query.answer()
    else:
        await callback_query.answer()

def create_main_menu(user_id):
    wide = "\u2007" * 8; half = "\u2007" * 3
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{wide}⚡ فعالسازی سلف{wide}", callback_data="activate_self", style=KeyboardButtonStyle(bg_success=True))],
        [
            InlineKeyboardButton(f"{half}🎰 گردونه شانس{half}", callback_data="lucky_wheel", style=KeyboardButtonStyle(bg_success=True)),
            InlineKeyboardButton(f"{half}🏆 لیدربورد{half}", callback_data="leaderboard", style=KeyboardButtonStyle(bg_primary=True))
        ],
        [
            InlineKeyboardButton(f"{half}👤 حساب کاربری{half}", callback_data="status_credits", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton(f"{half}👥 زیرمجموعه{half}", callback_data="referral", style=KeyboardButtonStyle(bg_success=True))
        ],
        [InlineKeyboardButton(f"{wide}⚙️ مدیریت بات ⚙️{wide}", callback_data="self_management", style=KeyboardButtonStyle(bg_primary=True))],
        [
            InlineKeyboardButton(f"{half}• راهنمای خرید •{half}", callback_data="buy_guide", style=KeyboardButtonStyle(bg_primary=True)),
            InlineKeyboardButton(f"{half}• خرید الماس •{half}", callback_data="increase_balance", style=KeyboardButtonStyle(bg_success=True))
        ],
        [InlineKeyboardButton(f"{wide}👨‍💻 پشتیبانی 👨‍💻{wide}", callback_data="support", style=KeyboardButtonStyle(bg_success=True))],
        [InlineKeyboardButton(f"{wide}📣 چنل ما 📣{wide}", callback_data="buy_channel", style=KeyboardButtonStyle(bg_primary=True))]
    ])

async def show_main_menu(client, chat_id, user):
    user_id = user.id
    existing_user = db.get("users", user_id)
    is_new_user = False
    if not existing_user:
        user_info = {"status": "inactive", "created_at": time.time(), "first_name": user.first_name or "", "username": user.username or ""}
        db.set("users", user_id, user_info)
        is_new_user = True
    else:
        user_info = existing_user
        user_info["first_name"] = user.first_name or ""
        user_info["username"] = user.username or ""
        db.set("users", user_id, user_info)
    credits = db.get("credits", user_id, 0)
    if is_new_user and credits == 0:
        db.set("credits", user_id, 5)
        credits = 5
    user_data = db.get("users", user_id, {})
    status = "🟢 فعال" if user_data.get('status') == 'active' else "🔴 غیرفعال"
    phone = user_data.get('phone', '')
    keyboard = create_main_menu(user_id)
    welcome_text = f"""**🌺 به ربات سلف ساز خوش آمدید!**

🤖 **ربات مدیریت سلف بات حرفه‌ای**
📊 **وضعیت حساب شما:**
├─ 👤 کاربر: {user.first_name or "ناشناس"}
├─ 🔋 وضعیت: {status}
├─ 💎 الماس: {credits:,} عدد
└─ ⏰ مصرف 1 الماس در ساعت

{f"📱 **شماره:** `{phone}`" if phone else "⚠️ **شماره ثبت نشده**"}

💡 برای شروع روی «⚡ فعالسازی سلف» کلیک کنید.
🎰 هر روز یک بار گردونه شانس را امتحان کن!
{MENU_WIDTH_PAD}"""
    await client.send_message(chat_id, welcome_text, reply_markup=keyboard)

# ==============================
# استارت + عضویت اجباری + زیرمجموعه
# ==============================
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    user = message.from_user
    uid = user.id
    payload = message.command[1] if len(message.command) > 1 else ""

    ok, chans = await check_force_join(client, uid)
    if not ok:
        rows = [[InlineKeyboardButton(f"📣 عضویت در {ch}", url=f"https://t.me/{ch}")] for ch in chans]
        rows.append([InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_join", style=KeyboardButtonStyle(bg_success=True))])
        await message.reply_text(
            "⚠️ **برای استفاده از ربات ابتدا در کانال عضو شوید:**",
            reply_markup=InlineKeyboardMarkup(rows),
            disable_web_page_preview=True
        )
        return

    was_new = db.get("users", uid) is None
    await show_main_menu(client, uid, user)

    if was_new and payload.startswith("ref_"):
        try:
            ref_id = int(payload[4:])
        except:
            ref_id = None
        if ref_id and ref_id != uid and db.get("users", ref_id) is not None:
            ref_info = db.get("users", ref_id)
            ref_info["referrals"] = ref_info.get("referrals", 0) + 1
            db.set("users", ref_id, ref_info)
            db.set("credits", ref_id, db.get("credits", ref_id, 0) + 3)
            try:
                await client.send_message(ref_id, "🎁 یک نفر با لینک شما عضو ربات شد!\n💎 +۳ الماس به حساب شما اضافه شد.")
            except:
                pass

# ==============================
# 🔍 لاگ همه پیام‌های پیوی (برای عیب‌یابی)
# ==============================
@bot.on_message(filters.private, group=-100)
async def _log_all_private(client, message):
    try:
        print(f"📩 پیام از {message.from_user.id}: {(message.text or 'مدیا')[:30]}", flush=True)
    except:
        pass

# ==============================================================================
# 🚀 استارت + ری‌استارت خودکار سلف‌های فعال پس از هر ری‌استارت بات
# ==============================================================================
async def _auto_restart_on_boot():
    """اگر بات ری‌استارت شده بود، سلف‌های فعال را دوباره روشن می‌کند"""
    await asyncio.sleep(8)
    restarted = 0
    for uid_s, info in db.get_all("users").items():
        try:
            uid = int(uid_s)
        except:
            continue
        if info.get("status") == "active" and db.get("credits", uid, 0) > 0:
            if await run_selfbot_async(uid, info.get("phone")):
                restarted += 1
    if restarted:
        print(f"🚀 {restarted} سلف فعال پس از استارت بات دوباره راه‌اندازی شد", flush=True)

if __name__ == "__main__":
    print("🤖 ربات مدیریت سلف PersianGulf اجرا شد", flush=True)

    async def main():
        global BOT_LOOP
        BOT_LOOP = asyncio.get_running_loop()
        await bot.start()
        asyncio.create_task(_auto_restart_on_boot())
        print("✅ بات آماده است", flush=True)
        await idle()
        await bot.stop()

    bot.run(main())
