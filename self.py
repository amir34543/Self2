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
from pyrogram.errors import FloodWait, UserNotParticipant
try:
    from pyrogram.errors import ChatAdminRequired, PeerIdInvalid, ChannelPrivate
except ImportError:
    class ChatAdminRequired(Exception): pass
    class PeerIdInvalid(Exception): pass
    class ChannelPrivate(Exception): pass

bot_username = "Helperbotpersian_bot"  # یوزرنیم ربات هلپر بدون @

USER_ID = None
PHONE = None
API_ID = 35656061
API_HASH = "b37f2596516bc0439bf505d1d230395c"

if len(sys.argv) > 1: USER_ID = int(sys.argv[1])
if len(sys.argv) > 2: PHONE = sys.argv[2]
if len(sys.argv) > 3: API_ID = int(sys.argv[3])
if len(sys.argv) > 4: API_HASH = sys.argv[4]

# ⛔ SESSION_STRING کاملاً حذف شد — هر کاربر سشن اختصاصی خودش را دارد
# تا چندکاربره درست کار کند و سلفِ همه روی یک اکانت نیفتد
session_name = f"sessions/{USER_ID}" if USER_ID else "self"
app = Client(session_name, api_id=API_ID, api_hash=API_HASH)

# --- کش get_me: فراخوانی مکرر باعث FLOOD_WAIT می‌شود؛ ۹۰ ثانیه کش می‌کنیم ---
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
                _me_cache["ts"] = now + e.value
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

# ---- 📢 تبچی: نسخه پیشرفته بنر همگانی — چرخش چند بنر، تعداد دور مشخص، آمار ----
TABCHI_FILE = f"tabchi_{USER_ID}.json" if USER_ID else "tabchi.json"
tabchi = jload(TABCHI_FILE, {
    "active": False, "codes": [], "idx": 0, "interval": 300, "max_rounds": None,
    "rounds_done": 0, "last_run": 0.0,
    "sent_total": 0, "failed_total": 0, "last_sent": 0, "last_failed": 0, "last_ts": 0.0,
})
def tabchi_save(): jsave(TABCHI_FILE, tabchi)
START_TIME = time.time()

# ساعت در اسم: وضعیت باید روی دیسک ذخیره شود وگرنه بعد از هر ری‌استارت
# سلف، نام اصلی کاربر فراموش می‌شود و با فعال‌سازی دوباره، ساعت روی ساعت قبلی
# چسبانده می‌شود (نام بی‌نهایت بزرگ می‌شود و آپدیت پروفایل با خطا شکست می‌خورد
# بدون این‌که به کاربر نمایش داده شود — همان «دکمه کار نمی‌کند»)
TIME_STATE_FILE = "clock_state.json"
_time_state = jload(TIME_STATE_FILE, {"status": {}, "original": {}})
user_time_status = {int(k): v for k, v in _time_state.get("status", {}).items()}
user_original_names = {int(k): v for k, v in _time_state.get("original", {}).items()}

def _save_time_state():
    jsave(TIME_STATE_FILE, {
        "status": {str(k): v for k, v in user_time_status.items()},
        "original": {str(k): v for k, v in user_original_names.items()},
    })

def _clean_original_name(name):
    """اگر نام فعلی از قبل به‌اشتباه شامل ساعت باشد (مثلاً بعد از ری‌استارت)، آن را پاک می‌کند."""
    import unicodedata
    name = (name or "").strip()
    if not name:
        return name
    parts = name.split(" ")
    while parts:
        core = "".join(ch for ch in parts[-1] if unicodedata.category(ch) != "Mn").replace(":", "")
        if core and all(ch.isdigit() for ch in core):
            parts.pop()
        else:
            break
    cleaned = " ".join(parts).strip()
    return cleaned if cleaned else name

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
TIME_FONTS = {
    1: ["𝟎", "𝟏", "𝟐", "𝟑", "𝟒", "𝟓", "𝟔", "𝟕", "𝟖", "𝟗"],  # بولد
    2: ["𝟬", "𝟭", "𝟮", "𝟯", "𝟰", "𝟱", "𝟲", "𝟳", "𝟴", "𝟵"],  # سنس‌بولد
    3: ["０", "１", "２", "３", "４", "５", "６", "７", "８", "９"],  # تمام‌عرض
    4: ["𝟢", "𝟣", "𝟤", "𝟥", "𝟦", "𝟧", "𝟨", "𝟩", "𝟪", "𝟫"],  # سنس
    5: ["𝟘", "𝟙", "𝟚", "𝟛", "𝟜", "𝟝", "𝟞", "𝟟", "𝟠", "𝟡"],  # دابل‌استراک
    7: ["𝟶", "𝟷", "𝟸", "𝟹", "𝟺", "𝟻", "𝟼", "𝟽", "𝟾", "𝟿"],  # مونو‌اسپیس
    8: ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"],  # بالانویس
    9: ["₀", "₁", "₂", "₃", "₄", "₅", "₆", "₇", "₈", "₉"],  # پایین‌نویس
    10: ["⓪", "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"],  # دایره‌ای
    11: ["⓿", "❶", "❷", "❸", "❹", "❺", "❻", "❼", "❽", "❾"],  # دایره پر
    12: ["0", "⑴", "⑵", "⑶", "⑷", "⑸", "⑹", "⑺", "⑻", "⑼"],  # پرانتزی
    13: ["0", "⒈", "⒉", "⒊", "⒋", "⒌", "⒍", "⒎", "⒏", "⒐"],  # نقطه‌دار
    14: ["0̲", "1̲", "2̲", "3̲", "4̲", "5̲", "6̲", "7̲", "8̲", "9̲"],  # زیرخط
    15: ["0̳", "1̳", "2̳", "3̳", "4̳", "5̳", "6̳", "7̳", "8̳", "9̳"],  # زیرخط دوبل
    16: ["0̶", "1̶", "2̶", "3̶", "4̶", "5̶", "6̶", "7̶", "8̶", "9̶"],  # خط‌خورده
    17: ["0̅", "1̅", "2̅", "3̅", "4̅", "5̅", "6̅", "7̅", "8̅", "9̅"],  # روخط
    18: ["0̿", "1̿", "2̿", "3̿", "4̿", "5̿", "6̿", "7̿", "8̿", "9̿"],  # روخط دوبل
    19: ["0̃", "1̃", "2̃", "3̃", "4̃", "5̃", "6̃", "7̃", "8̃", "9̃"],  # مواج
    20: ["0̂", "1̂", "2̂", "3̂", "4̂", "5̂", "6̂", "7̂", "8̂", "9̂"],  # سقفی
    21: ["0̊", "1̊", "2̊", "3̊", "4̊", "5̊", "6̊", "7̊", "8̊", "9̊"],  # حلقه‌دار
    22: ["0̇", "1̇", "2̇", "3̇", "4̇", "5̇", "6̇", "7̇", "8̇", "9̇"],  # نقطه بالا
    23: ["0̣", "1̣", "2̣", "3̣", "4̣", "5̣", "6̣", "7̣", "8̣", "9̣"],  # نقطه پایین
    24: ["0̄", "1̄", "2̄", "3̄", "4̄", "5̄", "6̄", "7̄", "8̄", "9̄"],  # ماکرون
    25: ["0̱", "1̱", "2̱", "3̱", "4̱", "5̱", "6̱", "7̱", "8̱", "9̱"],  # زیرخط ضخیم
    26: ["0̀", "1̀", "2̀", "3̀", "4̀", "5̀", "6̀", "7̀", "8̀", "9̀"],  # گریو
    27: ["0́", "1́", "2́", "3́", "4́", "5́", "6́", "7́", "8́", "9́"],  # آکوت
    28: ["0̈", "1̈", "2̈", "3̈", "4̈", "5̈", "6̈", "7̈", "8̈", "9̈"],  # دیارز
    29: ["0̆", "1̆", "2̆", "3̆", "4̆", "5̆", "6̆", "7̆", "8̆", "9̆"],  # بروه
    30: ["0̌", "1̌", "2̌", "3̌", "4̌", "5̌", "6̌", "7̌", "8̌", "9̌"],  # کارون
    6: None,  # خط‌دار کلاسیک — مورد خاص، در fa_time_str مدیریت می‌شود
}

def fa_time_str(fid=1):
    t = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M")
    if fid == 6:
        return "".join(ch + "\u0334" for ch in t)
    digits = TIME_FONTS.get(fid) or TIME_FONTS[1]
    return t.translate({ord(str(i)): digits[i] for i in range(10)})

def _alpha(lo, up):
    return str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", lo + up)

FANCY_TRANS = {
    1: _alpha("𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇", "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"),  # سنس‌بولد
    2: _alpha("𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻", "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡"),  # سنس‌ایتالیک
    3: _alpha("𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫", "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"),  # دابل‌استراک
    5: _alpha("ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ", "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ"),  # دایره‌ای
    6: _alpha("𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟", "𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅"),  # فراکتور بولد
    7: _alpha("𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯", "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕"),  # سنس‌بولدایتالیک
    8: _alpha("𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣", "𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉"),  # مونو‌اسپیس
    9: _alpha("𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓", "𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹"),  # سنس
    10: _alpha("𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳", "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙"),  # بولد
    11: _alpha("𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧", "𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍"),  # ایتالیک
    12: _alpha("𝒂𝒃𝒄𝒅𝒆𝒇𝒈𝒉𝒊𝒋𝒌𝒍𝒎𝒏𝒐𝒑𝒒𝒓𝒔𝒕𝒖𝒗𝒘𝒙𝒚𝒛", "𝑨𝑩𝑪𝑫𝑬𝑭𝑮𝑯𝑰𝑱𝑲𝑳𝑴𝑵𝑶𝑷𝑸𝑹𝑺𝑻𝑼𝑽𝑾𝑿𝒀𝒁"),  # بولدایتالیک
    13: _alpha("𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏", "𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵"),  # اسکریپت
    14: _alpha("𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃", "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩"),  # بولداسکریپت
    15: _alpha("𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷", "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ"),  # فراکتور
    16: _alpha("ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ", "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"),  # تمام‌عرض
    4: _alpha("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"),  # کوچک‌بزرگ (Small Caps)
}

_ALPHA_ALL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
FANCY_COMB_MARKS = [
    '̲',
    '̳',
    '̶',
    '̅',
    '̃',
    '̂',
    '̊',
    '̇',
    '̣',
    '̄',
    '̀',
    '́',
    '̈',
    '̆',
]
for _i, _mk in enumerate(FANCY_COMB_MARKS):
    FANCY_TRANS[17 + _i] = {ord(c): c + _mk for c in _ALPHA_ALL}
WRAPPERS = {1: ("꧁ ", " ꧂"), 2: ("✦ ", " ✦"), 3: ("༺ ", " ༻"), 4: ("「 ", " 」"), 5: ("★ ", " ★"), 6: ("『 ", " 』"),
            7: ("◈ ", " ◈"), 8: ("♦ ", " ♦"), 9: ("☾ ", " ☽"), 10: ("▧ ", " ▧"), 11: ("▣ ", " ▣"), 12: ("❖ ", " ❖"),
            13: ("⟡ ", " ⟡"), 14: ("꒰ ", " ꒱"), 15: ("⚡ ", " ⚡"), 16: ("🔥 ", " 🔥"), 17: ("❁ ", " ❁"), 18: ("☆ ", " ☆"),
            19: ("⌈ ", " ⌉"), 20: ("» ", " «"), 21: ("⊰ ", " ⊱"), 22: ("◇ ", " ◇"), 23: ("✧ ", " ✧"), 24: ("⋆ ", " ⋆"),
            25: ("⟦ ", " ⟧"), 26: ("☙ ", " ❧"), 27: ("➤ ", " ➤"), 28: ("⁘ ", " ⁘"), 29: ("✵ ", " ✵"), 30: ("꧁", "꧂")}

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
                "پنل", "panel", "منش", "امضا", "جمنای", "هوش", "آهنگ", "موزیک", "اسم", "شزم", "اصلاح", "خلاصه", "متن", "تبدیل", "تبچی")

# ==============================================================================
# ★ هندلر پنل (اول از همه تا با بقیه تداخل نکند) ★
# ==============================================================================
@app.on_message(filters.me & filters.command(["پنل", "panel"], prefixes=""))
async def panel_command(client, message):
    loading_msg = await message.edit_text("⏳ **در حال باز کردن پنل Persian Gulf Self...**")
    async def _send_panel(query):
        results = await client.get_inline_bot_results(bot_username, query)
        if not (results and results.results): return False
        await client.send_inline_bot_result(chat_id=message.chat.id, query_id=results.query_id,
                                            result_id=results.results[0].id)
        return True
    try:
        try:
            ok = await _send_panel("panel")
        except Exception as e:
            # چت اجازه ارسال عکس نمی‌دهد (CHAT_SEND_PHOTOS_FORBIDDEN و مشابه): پنل متنی بدون بنر
            if any(k in str(e) for k in ("PHOTOS_FORBIDDEN", "MEDIA_FORBIDDEN", "SEND_MEDIA", "WRITE_FORBIDDEN")):
                ok = await _send_panel("paneltext")
            else:
                raise
        if ok: await loading_msg.delete()
        else: await loading_msg.edit_text("❌ **پنل یافت نشد**\nربات هلپر روشن است اما پاسخی نداد.")
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

@app.on_message(filters.me & filters.command(["بایو", "بیو"], prefixes=""))
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

@app.on_message(filters.me & filters.command(["نام", "اسم"], prefixes=""))
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

async def _apply_time_toggle(client, message, on):
    global user_fonts
    uid = message.from_user.id
    if on:
        base = user_original_names.get(uid) or _clean_original_name(message.from_user.first_name or "")
        fid = user_fonts.get(uid, 1)
        new_name = f"{base} {fa_time_str(fid)}".strip()[:64]
        try:
            await app.update_profile(first_name=new_name)
        except FloodWait as e:
            return await message.edit(f"❌ محدودیت تلگرام (Flood Wait): {e.value} ثانیه دیگر دوباره امتحان کنید")
        except Exception as e:
            return await message.edit(f"❌ خطا در تغییر نام:\n`{e}`")
        user_time_status[uid] = True
        user_original_names[uid] = base
        _save_time_state()
        await message.edit(f"✅ ساعت در اسم (تایم) روشن شد\n⏰ {fa_time_str(fid)}")
    else:
        base = user_original_names.get(uid, message.from_user.first_name or "")
        try:
            await app.update_profile(first_name=base)
        except FloodWait as e:
            user_time_status[uid] = False
            _save_time_state()
            return await message.edit(f"⚠️ خاموش شد، ولی به‌خاطر Flood Wait نام هنوز آپدیت نشده ({e.value} ثانیه دیگر خودش درست می‌شود)")
        except Exception:
            pass
        user_time_status[uid] = False
        _save_time_state()
        await message.edit("✅ ساعت در اسم (تایم) خاموش شد")

@app.on_message(filters.me & filters.command("تایم", prefixes="") & filters.regex(r"^تایم (روشن|خاموش)$"))
async def time_command(client, message):
    await _apply_time_toggle(client, message, message.command[1] == "روشن")

@app.on_message(filters.me & filters.regex(r"^ساعت نام (روشن|خاموش)$"))
async def clock_name_alias_cmd(client, message):
    await _apply_time_toggle(client, message, message.matches[0].group(1) == "روشن")

@app.on_message(filters.me & filters.regex(r"^(لیست فونت|تنظیم فونت \d+)$"))
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

def _fmt_secs(sec):
    sec = int(max(0, sec))
    if sec < 60: return f"{sec} ثانیه"
    m, s = divmod(sec, 60)
    return f"{m} دقیقه" + (f" و {s} ثانیه" if s else "")

def _tabchi_status_text():
    if not tabchi["codes"]:
        return "🛑 **تبچی خاموش است**\n\nابتدا کد بنر(ها) را انتخاب کن: `تبچی کد 1` یا `تبچی کد 1,2,3`"
    codes_txt = "، ".join(tabchi["codes"])
    rounds_txt = "نامحدود" if tabchi["max_rounds"] is None else f"{tabchi['rounds_done']}/{tabchi['max_rounds']}"
    lines = [
        f"{'🟢' if tabchi['active'] else '🔴'} **وضعیت تبچی:** {'روشن' if tabchi['active'] else 'خاموش'}",
        f"📋 کدهای در چرخش: {codes_txt}",
        f"⏱ فاصله هر دور: {_fmt_secs(tabchi['interval'])}",
        f"🔁 دور: {rounds_txt}",
    ]
    if tabchi["active"]:
        remain = tabchi["interval"] - (time.time() - tabchi["last_run"])
        lines.append(f"⏳ دور بعدی: {_fmt_secs(remain) if remain > 0 else 'در حال ارسال...'}")
    if tabchi["last_ts"]:
        ago = _fmt_secs(time.time() - tabchi["last_ts"])
        lines.append(f"📨 آخرین دور: {tabchi['last_sent']} موفق، {tabchi['last_failed']} ناموفق ({ago} پیش)")
    lines.append(f"📊 مجموع کل: {tabchi['sent_total']} موفق، {tabchi['failed_total']} ناموفق")
    return "\n".join(lines)

async def _tabchi_run_round(client):
    """یک دور تبچی: بنر بعدی در چرخش را به همه گروه‌ها می‌فرستد"""
    if not tabchi["codes"]: return
    code = tabchi["codes"][tabchi["idx"] % len(tabchi["codes"])]
    tabchi["idx"] += 1
    text = banners.get(code)
    if text is None: return
    sent = failed = 0
    async for d in app.get_dialogs(limit=300):
        if d.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
            try:
                await app.send_message(d.chat.id, text); sent += 1
                await asyncio.sleep(4)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                failed += 1
    tabchi["rounds_done"] += 1
    tabchi["last_run"] = time.time(); tabchi["last_ts"] = tabchi["last_run"]
    tabchi["last_sent"] = sent; tabchi["last_failed"] = failed
    tabchi["sent_total"] += sent; tabchi["failed_total"] += failed
    if tabchi["max_rounds"] is not None and tabchi["rounds_done"] >= tabchi["max_rounds"]:
        tabchi["active"] = False
    tabchi_save()

@app.on_message(filters.me & filters.regex(
    r"^(تبچی|تبچی وضعیت|تبچی شروع|تبچی توقف|تبچی کد [\d,\s]+|تبچی تکرار \d+ (\d+|نامحدود|بی نهایت))$"))
async def tabchi_cmd(client, message):
    t = message.text.strip()
    if t in ("تبچی", "تبچی وضعیت"):
        return await message.edit(_tabchi_status_text())
    if t.startswith("تبچی کد"):
        codes = [c.strip() for c in re.split(r"[,،\s]+", t[len("تبچی کد"):].strip()) if c.strip()]
        bad = [c for c in codes if c not in banners]
        if bad: return await message.edit(f"❌ کد نامعتبر: {', '.join(bad)}\nبا `لیست بنرها` کدهای موجود را ببین")
        tabchi["codes"] = codes; tabchi["idx"] = 0; tabchi_save()
        return await message.edit(f"✅ {len(codes)} بنر برای چرخش تبچی ثبت شد: {', '.join(codes)}")
    if t == "تبچی شروع":
        if not tabchi["codes"]:
            return await message.edit("❌ اول کد بنر را انتخاب کن: `تبچی کد 1`")
        m = await message.edit("📤 در حال ارسال دور تبچی...")
        await _tabchi_run_round(client)
        return await m.edit(f"✅ دور تبچی ارسال شد\n📨 {tabchi['last_sent']} موفق، {tabchi['last_failed']} ناموفق")
    if t == "تبچی توقف":
        tabchi["active"] = False; tabchi_save()
        return await message.edit("🛑 تبچی چرخه‌ای متوقف شد")
    if t.startswith("تبچی تکرار"):
        if not tabchi["codes"]:
            return await message.edit("❌ اول کد بنر را انتخاب کن: `تبچی کد 1`")
        parts = t.split()
        sec = int(parts[2])
        cnt_raw = parts[3]
        max_rounds = None if cnt_raw in ("نامحدود", "بی") or "نامحدود" in t else int(cnt_raw)
        tabchi.update(active=True, interval=max(20, sec), max_rounds=max_rounds,
                      rounds_done=0, last_run=0.0)
        tabchi_save()
        rounds_txt = "نامحدود" if max_rounds is None else str(max_rounds)
        await message.edit(f"📢 تبچی چرخه‌ای روشن شد — هر {_fmt_secs(tabchi['interval'])}، {rounds_txt} دور")

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
@app.on_message(filters.me & filters.regex(r"^(ایدی|اطلاعات)$"))
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

# ---------- اینستاگرام: API اصلی + فالبک yt-dlp ----------
IG_API_URL = "https://api.fast-creat.ir/instagram"
IG_API_KEY = os.environ.get("IG_API_KEY") or "8000978149:uJC3mxBncq9ELPN@Api_ManagerRoBOT"
IG_COOKIES_FILE = "instagram_cookies.txt"   # اختیاری: کوکی اینستاگرام (فرمت Netscape) برای yt-dlp
_IG_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

def _ig_walk(node, out):
    """هر آیتمی که video_url یا عکس دارد را از هر ساختار JSON بیرون می‌کشد"""
    if isinstance(node, dict):
        vid = node.get("video_url")
        if not vid and isinstance(node.get("url"), str) and ".mp4" in node["url"].split("?")[0]:
            vid = node["url"]
        if isinstance(vid, str) and vid.startswith("http"):
            out.append(("video", vid)); return
        img = node.get("display_url") or node.get("image_url") or node.get("photo_url") or node.get("thumbnail_url")
        if isinstance(img, str) and img.startswith("http"):
            out.append(("photo", img)); return
        for v in node.values():
            _ig_walk(v, out)
    elif isinstance(node, list):
        for v in node:
            if isinstance(v, str) and v.startswith("http"):
                base = v.split("?")[0].lower()
                if base.endswith(".mp4"): out.append(("video", v))
                elif base.endswith((".jpg", ".jpeg", ".png", ".webp")): out.append(("photo", v))
            else:
                _ig_walk(v, out)

def _ig_find_caption(node):
    if isinstance(node, dict):
        c = node.get("caption")
        if isinstance(c, str) and c.strip(): return c
        if isinstance(c, dict) and isinstance(c.get("text"), str): return c["text"]
        for v in node.values():
            r = _ig_find_caption(v)
            if r: return r
    elif isinstance(node, list):
        for v in node:
            r = _ig_find_caption(v)
            if r: return r
    return ""

def _ig_download(url, path, timeout=90):
    r = requests.get(url, headers=_IG_UA, timeout=timeout)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)

def _ig_via_api(u, api_type, prefix):
    """(files, caption, error) — بلاک‌کننده؛ با to_thread صدا زده می‌شود"""
    try:
        resp = requests.get(IG_API_URL, params={"apikey": IG_API_KEY, "type": api_type, "url": u},
                            headers=_IG_UA, timeout=30)
    except Exception as e:
        return [], "", f"اتصال به API: {e}"
    body = (resp.text or "")[:400]
    print(f"[IG-API] HTTP {resp.status_code} → {body}")
    try:
        r = resp.json()
    except Exception:
        return [], "", f"HTTP {resp.status_code} و پاسخ غیر JSON: {body[:200]}"
    found = []
    _ig_walk(r, found)
    if not found:
        err = ""
        if isinstance(r, dict):
            err = r.get("message") or r.get("error") or r.get("msg") or ""
        return [], "", f"HTTP {resp.status_code} — {err or body[:200]}"
    seen, files = set(), []
    for i, (kind, url) in enumerate(found[:10]):
        if url in seen: continue
        seen.add(url)
        path = f"{prefix}_{i}.{'mp4' if kind == 'video' else 'jpg'}"
        try:
            _ig_download(url, path)
            files.append((kind, path))
        except Exception as e:
            print(f"[IG-API] دانلود فایل {i} ناموفق: {e}")
    if not files:
        return [], "", "لینک‌ها از API آمد ولی دانلود فایل ناموفق بود"
    return files, _ig_find_caption(r), None

def _ig_via_ytdlp(u, prefix):
    import yt_dlp, glob
    opts = {"outtmpl": f"{prefix}_%(autonumber)s.%(ext)s", "quiet": True, "no_warnings": True,
            "noplaylist": False, "format": "best[ext=mp4]/best"}
    if os.path.exists(IG_COOKIES_FILE):
        opts["cookiefile"] = IG_COOKIES_FILE
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(u, download=True)
    files = []
    for p in sorted(glob.glob(f"{prefix}_*")):
        ext = p.rsplit(".", 1)[-1].lower()
        if ext in ("mp4", "mov", "webm", "mkv"): files.append(("video", p))
        elif ext in ("jpg", "jpeg", "png", "webp"): files.append(("photo", p))
    cap = (info or {}).get("description") or (info or {}).get("title") or ""
    return files[:10], cap

DL_SEND_GIF = True   # همراه هر ویدیوی دانلودشده (اینستاگرام/تیکتاک) نسخه گیف هم فرستاده شود

async def _has_audio(path):
    exe = _ff()
    if not exe: return True
    try:
        proc = await asyncio.create_subprocess_exec(exe, "-hide_banner", "-i", path,
                                                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, err = await asyncio.wait_for(proc.communicate(), 30)
        return "Audio:" in err.decode(errors="ignore")
    except Exception:
        return True

async def _dl_send_gif(client, chat_id, video_path, gif_path, reply_id=None):
    """گیف = ویدیوی بی‌صدا و سبک (حداکثر ۱۰ ثانیه) که به‌صورت animation فرستاده می‌شود"""
    if not DL_SEND_GIF or not _ff(): return
    try:
        await _ffrun("-i", video_path, "-t", "10", "-an",
                     "-vf", "scale='trunc(min(480,iw)/2)*2':-2,fps=15",
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-pix_fmt", "yuv420p",
                     "-movflags", "+faststart", gif_path)
        kw = {"reply_to_message_id": reply_id} if reply_id else {}
        await client.send_animation(chat_id, gif_path, **kw)
    except Exception as e:
        print(f"[GIF] ساخت/ارسال گیف ناموفق: {e}")

@app.on_message(filters.me & filters.command("اینستا", prefixes=""))
async def instagram_download_command(client, message):
    if len(message.command) < 2: return await message.edit("❌ `اینستا لینک`")
    u = message.command[1].strip()
    if not u.startswith(("https://www.instagram.com/", "https://instagram.com/", "https://instagr.am/")):
        return await message.edit("❌ لینک نامعتبر")
    m = await message.edit("🔄 در حال دریافت...")
    if "/reel/" in u or "/reels/" in u: api_type = "reel"
    elif "/stories/" in u: api_type = "story"
    else: api_type = "post"
    prefix = f"ig_{message.id}"
    files, caption, api_err, yt_err = [], "", None, None
    try:
        # 1) API اصلی
        files, caption, api_err = await asyncio.to_thread(_ig_via_api, u, api_type, prefix)
        # 2) اگر نشد، yt-dlp
        if not files:
            try:
                await m.edit("🔄 API جواب نداد، تلاش با روش دوم...")
                files, caption = await asyncio.to_thread(_ig_via_ytdlp, u, prefix)
            except ImportError:
                yt_err = "yt-dlp نصب نیست (pip install -U yt-dlp)"
            except Exception as e:
                yt_err = str(e)[:300]
        if not files:
            return await m.edit(f"❌ دانلود اینستاگرام ناموفق بود\n\n🔹 API: `{api_err}`\n🔹 yt-dlp: `{yt_err}`")

        caption = (caption or "")[:1000]
        if len(files) == 1:
            kind, path = files[0]
            if kind == "video":
                # اگر ویدیوی API بی‌صدا بود، تلاش برای نسخه اصلی (با صدا) از yt-dlp
                if not await _has_audio(path):
                    try:
                        yfiles, ycap = await asyncio.to_thread(_ig_via_ytdlp, u, prefix + "y")
                        yv = [p for k, p in yfiles if k == "video"]
                        if yv and await _has_audio(yv[0]):
                            path = yv[0]; caption = caption or (ycap or "")[:1000]
                    except Exception as e:
                        print(f"[IG] نسخه با صدا از yt-dlp نیامد: {e}")
                await app.send_video(message.chat.id, path, caption=caption, supports_streaming=True)
                await _dl_send_gif(client, message.chat.id, path, f"{prefix}_gif.mp4")
            else: await app.send_photo(message.chat.id, path, caption=caption)
        else:
            from pyrogram.types import InputMediaPhoto, InputMediaVideo
            media = []
            for idx, (kind, path) in enumerate(files):
                cap = caption if idx == 0 else ""
                media.append(InputMediaVideo(path, caption=cap) if kind == "video" else InputMediaPhoto(path, caption=cap))
            await app.send_media_group(message.chat.id, media)
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ خطا در دانلود:\n`{e}`")
    finally:
        import glob as _g
        for p in _g.glob(f"{prefix}_*") + _g.glob(f"{prefix}y_*"):
            try: os.remove(p)
            except Exception: pass

@app.on_message(filters.me & filters.command("تیکتاک", prefixes=""))
async def tiktok_download_command(client, message):
    if len(message.command) < 2: return await message.edit("❌ `تیکتاک لینک`")
    u = message.command[1].strip()
    if "tiktok.com" not in u:
        return await message.edit("❌ لینک نامعتبر")
    m = await message.edit("🔄 در حال دریافت...")
    path = f"tt_{message.id}.mp4"
    try:
        resp = requests.get("https://www.tikwm.com/api/", params={"url": u}, timeout=30)
        resp.raise_for_status()
        r = resp.json()
        data = r.get("data") or {}
        video_url = data.get("play") or data.get("hdplay") or data.get("wmplay")
        if r.get("code") != 0 or not video_url:
            err = r.get("msg") or "لینک پیدا نشد"
            return await m.edit(f"❌ خطا از API: `{err}`")
        if not video_url.startswith("http"):
            video_url = "https://www.tikwm.com" + video_url
        with open(path, "wb") as f:
            f.write(requests.get(video_url, timeout=60).content)
        caption = data.get("title") or ""
        await app.send_video(message.chat.id, path, caption=caption, supports_streaming=True)
        await _dl_send_gif(client, message.chat.id, path, f"tt_{message.id}_gif.mp4")
        await m.delete()
    except requests.exceptions.RequestException as e:
        await m.edit(f"❌ خطا در اتصال به سرور دانلودر:\n`{e}`")
    except Exception as e:
        await m.edit(f"❌ خطا در دانلود:\n`{e}`")
    finally:
        for _p in (path, f"tt_{message.id}_gif.mp4"):
            if os.path.exists(_p):
                try: os.remove(_p)
                except Exception: pass

@app.on_message(filters.me & filters.command("یوتیوب", prefixes=""))
async def youtube_download_command(client, message):
    if len(message.command) < 2: return await message.edit("❌ `یوتیوب لینک`")
    u = message.command[1].strip()
    if "youtube.com" not in u and "youtu.be" not in u:
        return await message.edit("❌ لینک نامعتبر")
    try:
        import yt_dlp
    except ImportError:
        return await message.edit(
            "❌ کتابخانه `yt-dlp` نصب نیست.\nروی سرور اجرا کنید:\n`pip install -U yt-dlp`"
        )
    m = await message.edit("🔄 در حال دریافت اطلاعات ویدیو...")
    out_tmpl = f"yt_{message.id}.%(ext)s"
    ydl_opts = {
        "format": "best[ext=mp4][height<=720]/best[height<=720]/best",
        "outtmpl": out_tmpl,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    final_path = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(u, download=False)
            duration = info.get("duration") or 0
            if duration and duration > 1200:  # بیش از ۲۰ دقیقه دانلود نشود
                return await m.edit("❌ ویدیو طولانی‌تر از ۲۰ دقیقه است و دانلود نمی‌شود")
            await m.edit(f"⬇️ در حال دانلود: {info.get('title', '')}")
            ydl.download([u])
            final_path = ydl.prepare_filename(info)
        if not final_path or not os.path.exists(final_path):
            return await m.edit("❌ دانلود ناموفق بود")
        size_mb = os.path.getsize(final_path) / (1024 * 1024)
        if size_mb > 1900:
            return await m.edit("❌ حجم فایل بیش از حد مجاز تلگرام است")
        await m.edit("📤 در حال ارسال...")
        await app.send_video(message.chat.id, final_path, caption=info.get("title", ""))
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ خطا در دانلود:\n`{e}`")
    finally:
        if final_path and os.path.exists(final_path):
            try: os.remove(final_path)
            except Exception: pass

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

@app.on_message(filters.me & filters.command(["یادداشت", "میمو"], prefixes=""))
async def note_cmd(client, message):
    t = message.text.strip()
    if t.startswith("میمو"): t = "یادداشت" + t[4:]   # میمو = یادداشت
    if t == "یادداشت ها": return await notes_list_cmd(client, message)
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

@app.on_message(filters.me & filters.regex(r"^(یادداشت‌ها|یادداشت ها|میمو‌ها|میمو ها)$"))
async def notes_list_cmd(client, message):
    if notes:
        await message.edit("📝 **یادداشت‌ها:**\n" + "\n".join(f"• {k}: {v[:60]}" for k, v in notes.items()))
    else:
        await message.edit("یادداشتی ثبت نشده")

# ================== 🤖 هوش مصنوعی (Gemini) + 🎵 موسیقی و صدا ==================
# نسخه بازنویسی‌شده: TTS چندموتوره، تبدیل ویس به متن، آهنگ‌یاب، جستجو و ارسال آهنگ، دستیار هوشمند
import base64, shutil, importlib.util, glob as _glob_mod

AI_CONFIG_FILE = f"ai_config_{USER_ID}.json" if USER_ID else "ai_config.json"
YT_COOKIES_FILE = "youtube_cookies.txt"          # اختیاری: کوکی یوتیوب (فرمت Netscape) اگر سرور بلاک شد
GEM_BASE = "https://generativelanguage.googleapis.com/v1beta"
# مدل‌ها زود عوض می‌شوند؛ اگر اولی 404 بدهد خودکار سراغ بعدی می‌رود و مدل سالم ذخیره می‌شود
GEM_TEXT_MODELS = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
GEM_TTS_MODELS = ["gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts"]
AI_ASK_NAMES = ("جمنای", "هوش")                  # کلمه‌های شروع دستور سوال از هوش مصنوعی
MUSIC_NAMES = ("آهنگ", "موزیک")                  # کلمه‌های شروع دستور جستجوی آهنگ
_PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")

_ai_cfg = jload(AI_CONFIG_FILE, {})
def _ai_save(): jsave(AI_CONFIG_FILE, _ai_cfg)
def _ai_key(): return (os.environ.get("GEMINI_API_KEY") or _ai_cfg.get("key") or "").strip()
def _have(mod): return importlib.util.find_spec(mod) is not None

def _ai_models(kind):
    custom = _ai_cfg.get(f"{kind}_model")
    base = GEM_TTS_MODELS if kind == "tts" else GEM_TEXT_MODELS
    return ([custom] if custom else []) + [m for m in base if m != custom]

# ---------------------------------------------------------------- ابزارهای کمکی دستورها
def _split_cmd(text, names):
    t = (text or "").strip()
    for n in sorted(names, key=len, reverse=True):
        if t == n: return n, ""
        if t.startswith(n) and t[len(n)] in " \n": return n, t[len(n):].strip()
    return None, None

def _mk_filter(fn, name):
    async def _f(_, __, m):
        try: return bool(m.text) and bool(fn(m))
        except Exception: return False
    return filters.create(_f, name)

def _audio_media(m):
    """ویس/موزیک/ویدیو گرد/ویدیو یا فایل صوتی-تصویری"""
    if not m: return None
    if m.voice or m.audio or m.video_note or m.video: return True
    d = m.document
    return bool(d and (d.mime_type or "").startswith(("audio/", "video/")))

def _mime_of(m):
    if m.voice: return "audio/ogg"
    if m.audio: return m.audio.mime_type or "audio/mpeg"
    if m.video_note or m.video: return "video/mp4"
    if m.document: return m.document.mime_type or "application/octet-stream"
    return "application/octet-stream"

def _rm(paths):
    for p in paths:
        try:
            if p and os.path.exists(p): os.remove(p)
        except Exception: pass

_NO_KEY_MSG = ("❌ کلید Gemini تنظیم نشده.\n"
               "۱) از aistudio.google.com/apikey یک کلید رایگان بگیر\n"
               "۲) بنویس: `جمنای کلید XXXX`")

def _ai_err(e):
    s = str(e)
    return _NO_KEY_MSG if s == "NO_KEY" else f"❌ {s[:350]}"

# ---------------------------------------------------------------- Gemini REST
def _gem_post(model, body, timeout=90):
    r = requests.post(f"{GEM_BASE}/models/{model}:generateContent",
                      headers={"x-goog-api-key": _ai_key(), "Content-Type": "application/json"},
                      json=body, timeout=timeout)
    try: data = r.json()
    except Exception: data = {}
    return r.status_code, data

def _gem_errmsg(st, data):
    msg = ""
    if isinstance(data, dict): msg = (data.get("error") or {}).get("message") or ""
    return f"HTTP {st}: {msg[:200]}"

def _gem_run(kind, body, timeout=90):
    """زنجیره مدل‌ها را امتحان می‌کند؛ فقط خطای «مدل پیدا نشد» به مدل بعدی می‌رود"""
    if not _ai_key(): raise RuntimeError("NO_KEY")
    chain = _ai_models(kind); last = ""
    for model in chain:
        for attempt in range(2):
            try: st, data = _gem_post(model, body, timeout)
            except requests.RequestException as e:
                raise RuntimeError(f"اتصال به Gemini برقرار نشد: {e}")
            if st == 200:
                if model != chain[0] and not _ai_cfg.get(f"{kind}_model"):
                    _ai_cfg[f"{kind}_model"] = model; _ai_save()
                return data
            last = _gem_errmsg(st, data)
            low = last.lower()
            if st in (500, 503) and attempt == 0:
                time.sleep(1.5); continue
            if st == 404 or (st == 400 and ("not found" in low or "not supported" in low)):
                break                                   # مدل بعدی
            if st == 429:
                raise RuntimeError("سهمیه/محدودیت نرخ Gemini تمام شده؛ کمی بعد دوباره امتحان کن")
            if st in (401, 403) or (st == 400 and "api key" in low):
                raise RuntimeError(f"کلید Gemini نامعتبر است یا دسترسی ندارد ({last})")
            raise RuntimeError(last)
    raise RuntimeError(last or "هیچ مدل Gemini در دسترس نبود")

def _gem_extract_text(data):
    out = []
    for c in (data.get("candidates") or [])[:1]:
        for p in (c.get("content") or {}).get("parts") or []:
            if p.get("text") and not p.get("thought"): out.append(p["text"])
    txt = "".join(out).strip()
    if not txt:
        br = (data.get("promptFeedback") or {}).get("blockReason")
        raise RuntimeError("پاسخ خالی" + (f" (مسدود شد: {br})" if br else ""))
    return txt

AI_SYSTEM = ("You are a smart assistant inside a personal Telegram self-bot. "
             "Reply in the same language the user writes in (Persian by default). "
             "Be concise and practical; use plain text without markdown symbols.")

def _gem_text(parts, system=AI_SYSTEM, json_mode=False, timeout=120):
    body = {"contents": [{"role": "user", "parts": parts}]}
    if system: body["systemInstruction"] = {"parts": [{"text": system}]}
    if json_mode: body["generationConfig"] = {"responseMimeType": "application/json"}
    return _gem_extract_text(_gem_run("text", body, timeout))

def _gem_tts_pcm(text, voice):
    body = {"contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    data = _gem_run("tts", body, 150)
    for c in (data.get("candidates") or [])[:1]:
        for p in (c.get("content") or {}).get("parts") or []:
            idata = p.get("inlineData") or p.get("inline_data")
            if idata and idata.get("data"):
                mt = idata.get("mimeType") or idata.get("mime_type") or ""
                m = re.search(r"rate=(\d+)", mt)
                return base64.b64decode(idata["data"]), int(m.group(1)) if m else 24000
    raise RuntimeError("Gemini صدایی برنگرداند")

def _inline(path, mime):
    with open(path, "rb") as f:
        return {"inline_data": {"mime_type": mime, "data": base64.b64encode(f.read()).decode()}}

def _gem_list_models():
    r = requests.get(f"{GEM_BASE}/models", params={"pageSize": 100},
                     headers={"x-goog-api-key": _ai_key()}, timeout=30)
    r.raise_for_status()
    names = []
    for m in r.json().get("models", []):
        if "generateContent" in (m.get("supportedGenerationMethods") or []):
            n = m.get("name", "").replace("models/", "")
            if "gemini" in n: names.append(n)
    return names

# ---------------------------------------------------------------- ffmpeg
_FF = {"exe": None, "done": False}
def _ff():
    """مسیر ffmpeg؛ اگر فقط imageio-ffmpeg باشد یک میان‌بر «ffmpeg» روی PATH می‌سازد (برای yt-dlp/shazamio)"""
    if _FF["done"]: return _FF["exe"]
    _FF["done"] = True
    exe = shutil.which("ffmpeg")
    if not exe:
        try:
            import imageio_ffmpeg
            real = imageio_ffmpeg.get_ffmpeg_exe()
            d = os.path.abspath("_ffbin"); os.makedirs(d, exist_ok=True)
            shim = os.path.join(d, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            if not os.path.exists(shim):
                try: os.symlink(real, shim)
                except Exception:
                    shutil.copy(real, shim); os.chmod(shim, 0o755)
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            exe = shim
        except Exception:
            exe = None
    _FF["exe"] = exe
    return exe

async def _ffrun(*args, timeout=180):
    exe = _ff()
    if not exe: raise RuntimeError("ffmpeg نصب نیست (pip install imageio-ffmpeg)")
    proc = await asyncio.create_subprocess_exec(exe, "-y", "-hide_banner", "-loglevel", "error", *args,
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    _, err = await asyncio.wait_for(proc.communicate(), timeout)
    if proc.returncode != 0:
        raise RuntimeError((err or b"").decode(errors="ignore")[-200:] or "ffmpeg failed")

async def _ff_duration(path):
    exe = _ff()
    if not exe: return 0
    try:
        proc = await asyncio.create_subprocess_exec(exe, "-hide_banner", "-i", path,
                                                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, err = await asyncio.wait_for(proc.communicate(), 30)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", err.decode(errors="ignore"))
        if m: return int(round(int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))))
    except Exception: pass
    return 0

async def _to_ogg(src, dst, pcm_rate=None):
    pre = ["-f", "s16le", "-ar", str(pcm_rate), "-ac", "1"] if pcm_rate else []
    await _ffrun(*pre, "-i", src, "-vn", "-c:a", "libopus", "-b:a", "32k", "-ar", "48000", "-ac", "1", dst)

def _pcm_to_wav(pcm, rate, path):
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)

async def _prep_audio(src, mime, tmp):
    """فایل صوتی را برای Gemini آماده می‌کند (مونو، سبک، mp3)"""
    size = os.path.getsize(src)
    if not _ff():
        if (mime or "").startswith("audio/") and size <= 14 * 1024 * 1024: return src, mime
        raise RuntimeError("برای پردازش ویدیو/فایل‌های سنگین ffmpeg لازم است (pip install imageio-ffmpeg)")
    if mime in ("audio/mpeg", "audio/mp3") and size <= 12 * 1024 * 1024: return src, "audio/mpeg"
    dst = src + "_c.mp3"; tmp.append(dst)
    await _ffrun("-i", src, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k", dst)
    if os.path.getsize(dst) > 15 * 1024 * 1024:
        raise RuntimeError("فایل صوتی برای پردازش خیلی طولانی است")
    return dst, "audio/mpeg"

# ---------------------------------------------------------------- 🎙 متن به ویس
def _voice_name():
    return _ai_cfg.get("voice") or ("Charon" if _ai_cfg.get("gender") == "male" else "Kore")

async def _synth_voice(text, base, tmp):
    """(path, engine, is_voice) — Gemini ← Edge-TTS ← gTTS؛ هر کدام شکست خورد بعدی"""
    errors = []
    ogg = base + ".ogg"; tmp.append(ogg)
    male = _ai_cfg.get("gender") == "male"
    fa = bool(_PERSIAN_RE.search(text))
    if _ai_key():
        try:
            pcm, rate = await asyncio.to_thread(_gem_tts_pcm, text, _voice_name())
            try:
                p = base + ".pcm"; tmp.append(p)
                with open(p, "wb") as f: f.write(pcm)
                await _to_ogg(p, ogg, rate)
                return ogg, "Gemini", True
            except Exception as e:
                if _ff(): raise
                w = base + ".wav"; tmp.append(w)      # بدون ffmpeg: wav خام
                _pcm_to_wav(pcm, rate, w)
                return w, "Gemini", False
        except Exception as e:
            errors.append(f"Gemini: {e}")
    mp3 = base + ".mp3"; tmp.append(mp3)
    try:
        import edge_tts
        voice = (("fa-IR-FaridNeural" if male else "fa-IR-DilaraNeural") if fa
                 else ("en-US-GuyNeural" if male else "en-US-AriaNeural"))
        await edge_tts.Communicate(text, voice).save(mp3)
        engine = "Edge-TTS"
    except ImportError:
        errors.append("edge-tts نصب نیست"); engine = None
    except Exception as e:
        errors.append(f"Edge-TTS: {e}"); engine = None
    if engine is None:
        try:
            from gtts import gTTS
            await asyncio.to_thread(lambda: gTTS(text[:4500], lang="fa" if fa else "en").save(mp3))
            engine = "gTTS"
        except ImportError:
            errors.append("gTTS نصب نیست")
        except Exception as e:
            errors.append(f"gTTS: {e}")
    if engine and os.path.exists(mp3):
        try:
            await _to_ogg(mp3, ogg)
            return ogg, engine, True
        except Exception:
            return mp3, engine, False
    raise RuntimeError(" | ".join(errors) or "هیچ موتور تبدیل متن به صدا در دسترس نیست")

def _f_tts(m):
    name, arg = _split_cmd(m.text, ("ویس کن", "ویس"))
    if not name or arg in ("روشن", "خاموش"): return False     # «ویس روشن» = قفل ویس
    return bool(arg) or bool(m.reply_to_message)

@app.on_message(filters.me & _mk_filter(_f_tts, "tts"))
async def tts_cmd(client, message):
    name, arg = _split_cmd(message.text, ("ویس کن", "ویس"))
    r = message.reply_to_message
    text = arg or ((r.text or r.caption or "") if r else "")
    if not text.strip():
        return await _safe_edit(message, "❌ `ویس متن` یا ریپلای روی یک متن + `ویس کن`")
    text = text.strip()[:3000]
    await _safe_edit(message, "🎙 در حال ساخت ویس...")
    tmp = []
    try:
        base = os.path.abspath(f"tts_{message.id}_{int(time.time())}")
        path, engine, is_voice = await _synth_voice(text, base, tmp)
        kw = {"reply_to_message_id": r.id} if r else {}
        if is_voice:
            dur = await _ff_duration(path)
            await client.send_voice(message.chat.id, path, duration=dur, **kw)
        else:
            await client.send_audio(message.chat.id, path, title="Voice", **kw)
        await message.delete()
    except Exception as e:
        await _safe_edit(message, f"❌ ساخت ویس ناموفق بود:\n`{str(e)[:400]}`")
    finally:
        _rm(tmp)

# ---------------------------------------------------------------- 📝 ویس به متن
STT_PROMPT = ("Transcribe this audio exactly as spoken. Detect the language automatically and keep the original "
              "language (do NOT translate). Persian must be written in Persian script with proper punctuation. "
              "Return ONLY the transcript, no comments. If there is no speech, return exactly: [بدون گفتار]")

async def _transcribe_msg(client, r, tmp):
    src = await client.download_media(r, file_name=os.path.abspath(f"stt_{r.id}_{int(time.time())}"))
    if not src: raise RuntimeError("دانلود فایل ناموفق بود")
    tmp.append(src)
    path, mime = await _prep_audio(src, _mime_of(r), tmp)
    return await asyncio.to_thread(_gem_text, [{"text": STT_PROMPT}, _inline(path, mime)], None)

def _f_stt(m):
    name, arg = _split_cmd(m.text, ("تبدیل به متن", "ویس به متن", "متن"))
    if not name or arg: return False
    if name == "متن": return bool(_audio_media(m.reply_to_message))    # «متن» تنها وقتی ریپلای روی ویس است
    return True

@app.on_message(filters.me & _mk_filter(_f_stt, "stt"))
async def stt_cmd(client, message):
    r = message.reply_to_message
    if not _audio_media(r):
        return await _safe_edit(message, "❌ روی یک ویس/موزیک/ویدیو ریپلای کنید")
    await _safe_edit(message, "📝 در حال تبدیل صدا به متن...")
    tmp = []
    try:
        txt = await _transcribe_msg(client, r, tmp)
        if len(txt) > 3800:
            p = os.path.abspath(f"stt_{message.id}.txt"); tmp.append(p)
            with open(p, "w", encoding="utf-8") as f: f.write(txt)
            await client.send_document(message.chat.id, p, caption="📝 متن ویس", reply_to_message_id=r.id)
            await message.delete()
        else:
            await _safe_edit(message, "📝 **متن ویس:**\n\n" + txt, parse_mode=enums.ParseMode.DISABLED)
    except Exception as e:
        await _safe_edit(message, _ai_err(e))
    finally:
        _rm(tmp)

@app.on_message(filters.private & filters.incoming & filters.voice, group=5)
async def auto_stt_incoming(client, message):
    """اختیاری: ویس‌های ورودی پیوی را به متن تبدیل و برای خودت در Saved Messages می‌فرستد (به طرف مقابل چیزی نمی‌رود)"""
    if not (_ai_cfg.get("auto_stt") and _ai_key()): return
    if (message.voice.duration or 0) > 300: return
    tmp = []
    try:
        txt = await _transcribe_msg(client, message, tmp)
        who = message.from_user.first_name if message.from_user else "؟"
        await client.send_message("me", f"🎙 ویس از {who}:\n\n{txt}"[:4000], parse_mode=enums.ParseMode.DISABLED)
    except Exception as e:
        print(f"[AUTO-STT] {e}")
    finally:
        _rm(tmp)

# ---------------------------------------------------------------- 🎵 آهنگ‌یاب (Shazam ← Gemini)
async def _sample_audio(src, tmp):
    dur = await _ff_duration(src)
    ss = min(int(dur * 0.3), 90) if dur and dur > 45 else 0
    dst = src + "_s.mp3"; tmp.append(dst)
    args = (["-ss", str(ss)] if ss else []) + ["-i", src, "-vn", "-t", "20", "-ac", "1", "-ar", "44100", "-b:a", "128k", dst]
    await _ffrun(*args)
    return dst

async def _recognize_song(client, r, tmp):
    """dict(title, artist, url, source, guess) یا None"""
    src = await client.download_media(r, file_name=os.path.abspath(f"rec_{r.id}_{int(time.time())}"))
    if not src: raise RuntimeError("دانلود فایل ناموفق بود")
    tmp.append(src)
    if not _have("shazamio") and not _ai_key():
        raise RuntimeError("نه shazamio نصب است نه کلید Gemini؛ `pip install shazamio` یا `جمنای کلید ...`")
    samp = await _sample_audio(src, tmp)
    errors = []
    if _have("shazamio"):
        try:
            from shazamio import Shazam
            sh = Shazam()
            fn = getattr(sh, "recognize", None) or getattr(sh, "recognize_song")
            out = await fn(samp)
            tr = (out or {}).get("track")
            if tr and tr.get("title"):
                return {"title": tr.get("title"), "artist": tr.get("subtitle") or "", "url": tr.get("url") or "",
                        "source": "Shazam", "guess": False}
        except Exception as e:
            errors.append(f"Shazam: {e}")
    if _ai_key():
        try:
            prompt = ("Identify the song in this audio clip (by melody, vocals and any audible lyrics). "
                      'Return JSON only: {"title": string|null, "artist": string|null}. '
                      "If you are not confident, use null for both. Never invent a song.")
            txt = await asyncio.to_thread(_gem_text, [{"text": prompt}, _inline(samp, "audio/mpeg")], None, True)
            try: d = json.loads(txt)
            except Exception:
                mm = re.search(r"\{.*\}", txt, re.S); d = json.loads(mm.group()) if mm else {}
            if isinstance(d, list) and d: d = d[0]
            if isinstance(d, dict) and d.get("title"):
                return {"title": d["title"], "artist": d.get("artist") or "", "url": "", "source": "Gemini", "guess": True}
        except Exception as e:
            errors.append(f"Gemini: {e}")
    if errors: print("[SONG-ID]", " | ".join(errors))
    return None

def _song_text(s):
    t = f"🎵 **{s['title']}**"
    if s["artist"]: t += f"\n👤 {s['artist']}"
    t += f"\n🔎 منبع: {s['source']}"
    if s["guess"]: t += "\n⚠️ این یک حدس هوش مصنوعی است و ممکن است اشتباه باشد"
    if s["url"]: t += f"\n🔗 {s['url']}"
    return t

def _f_songid(m):
    name, arg = _split_cmd(m.text, ("اسم آهنگ", "آهنگ یاب", "شزم"))
    return bool(name) and not arg

@app.on_message(filters.me & _mk_filter(_f_songid, "songid"))
async def songid_cmd(client, message):
    r = message.reply_to_message
    if not _audio_media(r):
        return await _safe_edit(message, "❌ روی یک ویس/آهنگ/ویدیو ریپلای کنید")
    await _safe_edit(message, "🎧 در حال تشخیص آهنگ...")
    tmp = []
    try:
        s = await _recognize_song(client, r, tmp)
        if not s: return await _safe_edit(message, "❌ آهنگ شناسایی نشد؛ یک تکه واضح‌تر (بدون حرف‌زدن روی آن) امتحان کنید")
        await _safe_edit(message, _song_text(s), parse_mode=enums.ParseMode.DISABLED)
    except Exception as e:
        await _safe_edit(message, _ai_err(e))
    finally:
        _rm(tmp)

# ---------------------------------------------------------------- 🎵 جستجو و ارسال آهنگ
def _music_fetch(query, prefix):
    """بلاک‌کننده (با to_thread صدا زده شود): جستجو در یوتیوب و در صورت شکست ساندکلود"""
    import yt_dlp
    errors = []
    for src in ("ytsearch5", "scsearch5"):
        try:
            so = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True, "socket_timeout": 30}
            if src.startswith("yt") and os.path.exists(YT_COOKIES_FILE): so["cookiefile"] = YT_COOKIES_FILE
            with yt_dlp.YoutubeDL(so) as y:
                res = y.extract_info(f"{src}:{query}", download=False)
            entries = [e for e in (res or {}).get("entries", []) if e]
            good = [e for e in entries if not e.get("is_live") and 30 <= (e.get("duration") or 200) <= 1200] or entries
            if not good:
                errors.append(f"{src[:2]}: نتیجه‌ای نبود"); continue
            pick = good[0]
            url = pick.get("webpage_url") or pick.get("url")
            dl = {"quiet": True, "no_warnings": True, "noplaylist": True, "socket_timeout": 30,
                  "format": "bestaudio[ext=m4a]/bestaudio/best", "outtmpl": f"{prefix}.%(ext)s"}
            if src.startswith("yt") and os.path.exists(YT_COOKIES_FILE): dl["cookiefile"] = YT_COOKIES_FILE
            with yt_dlp.YoutubeDL(dl) as y:
                info = y.extract_info(url, download=True)
            files = [p for p in _glob_mod.glob(f"{prefix}.*") if not p.endswith((".part", ".ytdl", ".jpg"))]
            if not files:
                errors.append(f"{src[:2]}: فایل دانلود نشد"); continue
            return {"path": files[0], "title": info.get("track") or info.get("title") or query,
                    "performer": info.get("artist") or info.get("uploader") or info.get("channel") or "",
                    "duration": int(info.get("duration") or 0), "thumb": info.get("thumbnail") or "", "url": url}
        except Exception as e:
            errors.append(f"{src[:2]}: {str(e)[:160]}")
    hint = ""
    if any("confirm you" in x.lower() or "sign in" in x.lower() for x in errors):
        hint = f"\n💡 یوتیوب سرور را بلاک کرده؛ فایل کوکی `{YT_COOKIES_FILE}` را کنار سلف بگذار"
    raise RuntimeError(" | ".join(errors) + hint)

async def _music_send(client, message, query, reply_id=None, extra=""):
    prefix = os.path.abspath(f"mus_{message.id}_{int(time.time())}")
    tmp = []
    try:
        await _safe_edit(message, f"🔎 در حال جستجوی «{query[:60]}»...")
        info = await asyncio.to_thread(_music_fetch, query, prefix)
        path = info["path"]; tmp.append(path)
        await _safe_edit(message, f"⬇️ {info['title'][:60]} — در حال آماده‌سازی...")
        if _ff() and not path.endswith(".mp3"):
            mp3 = prefix + "_out.mp3"; tmp.append(mp3)
            try:
                await _ffrun("-i", path, "-vn", "-c:a", "libmp3lame", "-b:a", "128k", mp3)
                path = mp3
            except Exception: pass                      # ارسال همان فایل اصلی
        if os.path.getsize(path) > 1900 * 1024 * 1024:
            return await _safe_edit(message, "❌ حجم فایل زیاد است")
        thumb = None
        if info["thumb"].lower().split("?")[0].endswith((".jpg", ".jpeg")):
            try:
                tp = prefix + "_t.jpg"; tmp.append(tp)
                rr = await asyncio.to_thread(lambda: requests.get(info["thumb"], timeout=15))
                if rr.ok and len(rr.content) < 200 * 1024:
                    with open(tp, "wb") as f: f.write(rr.content)
                    thumb = tp
            except Exception: pass
        cap = f"🎵 {info['title']}" + (f"\n👤 {info['performer']}" if info["performer"] else "") + extra
        kw = {"reply_to_message_id": reply_id} if reply_id else {}
        await client.send_audio(message.chat.id, path, caption=cap[:1000], title=info["title"][:64],
                                performer=(info["performer"] or "")[:64], duration=info["duration"],
                                thumb=thumb, **kw)
        await message.delete()
    except ImportError:
        await _safe_edit(message, "❌ `yt-dlp` نصب نیست: `pip install -U yt-dlp`")
    except Exception as e:
        await _safe_edit(message, f"❌ آهنگ پیدا/ارسال نشد:\n`{str(e)[:500]}`")
    finally:
        _rm(tmp); _rm(_glob_mod.glob(f"{prefix}*"))

def _f_music(m):
    name, arg = _split_cmd(m.text, MUSIC_NAMES)
    if not name: return False
    if not arg: return bool(m.reply_to_message)
    return len(arg.split()) <= 8 and "؟" not in arg and "?" not in arg    # جمله معمولی را دستور حساب نکن

@app.on_message(filters.me & _mk_filter(_f_music, "music"))
async def music_cmd(client, message):
    name, arg = _split_cmd(message.text, MUSIC_NAMES)
    r = message.reply_to_message
    if arg:
        return await _music_send(client, message, arg, r.id if r else None)
    if _audio_media(r):                                  # ریپلای روی ویس/آهنگ: تشخیص + ارسال نسخه کامل
        await _safe_edit(message, "🎧 در حال تشخیص آهنگ...")
        tmp = []
        try:
            s = await _recognize_song(client, r, tmp)
        except Exception as e:
            return await _safe_edit(message, _ai_err(e))
        finally:
            _rm(tmp)
        if not s:
            return await _safe_edit(message, "❌ آهنگ شناسایی نشد؛ یک تکه واضح‌تر امتحان کنید")
        q = f"{s['artist']} {s['title']}".strip()
        extra = "\n⚠️ حدس هوش مصنوعی" if s["guess"] else ""
        return await _music_send(client, message, q, r.id, extra)
    q = ((r.text or r.caption or "") if r else "").strip()[:100]
    if not q: return await _safe_edit(message, "❌ `آهنگ اسم` | ریپلای روی ویس/آهنگ | ریپلای روی متن")
    await _music_send(client, message, q, r.id)

# ---------------------------------------------------------------- 🤖 دستیار هوشمند (Gemini)
async def _media_parts(client, r, tmp):
    """عکس/ویس/موزیک/ویدیو گرد پیام ریپلای‌شده را برای Gemini آماده می‌کند"""
    if not r: return []
    if r.photo:
        p = await client.download_media(r, file_name=os.path.abspath(f"ai_{r.id}_{int(time.time())}"))
        if p: tmp.append(p); return [_inline(p, "image/jpeg")]
    elif _audio_media(r):
        p = await client.download_media(r, file_name=os.path.abspath(f"ai_{r.id}_{int(time.time())}"))
        if p:
            tmp.append(p); path, mime = await _prep_audio(p, _mime_of(r), tmp)
            return [_inline(path, mime)]
    return []

async def _send_long(client, message, text):
    chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)] or ["—"]
    await _safe_edit(message, chunks[0], parse_mode=enums.ParseMode.DISABLED)
    for c in chunks[1:]:
        try: await client.send_message(message.chat.id, c, parse_mode=enums.ParseMode.DISABLED)
        except Exception: pass

def _f_ask(m):
    name, arg = _split_cmd(m.text, AI_ASK_NAMES)
    return bool(name) and (bool(arg) or bool(m.reply_to_message))

async def _ai_admin(message, arg):
    """زیر‌دستورهای تنظیمات: کلید / وضعیت / مدل / صدا / خودکار / ریست"""
    first, _, rest = arg.partition(" "); rest = rest.strip()
    if first == "کلید":
        if not rest: return await _safe_edit(message, "❌ `جمنای کلید XXXX`")
        _ai_cfg["key"] = rest; _ai_save()
        await _safe_edit(message, "🔑 کلید ذخیره شد؛ در حال بررسی...")     # متن حاوی کلید همین لحظه ویرایش می‌شود
        try:
            await asyncio.to_thread(_gem_list_models)
            await _safe_edit(message, "✅ کلید Gemini معتبر است و ذخیره شد")
        except Exception as e:
            _ai_cfg.pop("key", None); _ai_save()
            await _safe_edit(message, f"❌ کلید معتبر نبود و ذخیره نشد: `{str(e)[:150]}`")
        await asyncio.sleep(6)
        try: await message.delete()
        except Exception: pass
        return True
    if first in ("وضعیت", "status") and not rest:
        k = _ai_key()
        eng = "، ".join(n for n, mod in (("Edge-TTS", "edge_tts"), ("gTTS", "gtts"), ("Shazam", "shazamio"),
                                        ("yt-dlp", "yt_dlp")) if _have(mod)) or "—"
        await _safe_edit(message,
            "🤖 **وضعیت هوش مصنوعی**\n"
            f"🔑 کلید: {'✅ ' + k[:6] + '…' if k else '❌ تنظیم نشده'}\n"
            f"🧠 مدل متن: `{_ai_models('text')[0]}`\n🗣 مدل صدا: `{_ai_models('tts')[0]}`\n"
            f"🎙 صدا: {_voice_name()} ({'مرد' if _ai_cfg.get('gender') == 'male' else 'زن'})\n"
            f"📝 ویس ورودی خودکار: {'روشن' if _ai_cfg.get('auto_stt') else 'خاموش'}\n"
            f"🎞 ffmpeg: {'✅' if _ff() else '❌'}\n🧩 ماژول‌ها: {eng}")
        return True
    if first == "مدل":
        if rest in ("ها", "لیست"):
            try:
                names = await asyncio.to_thread(_gem_list_models)
                await _safe_edit(message, "🧠 **مدل‌های در دسترس:**\n" + "\n".join(f"• `{n}`" for n in names[:40]))
            except Exception as e:
                await _safe_edit(message, _ai_err(e))
        elif rest.startswith("صدا "):
            _ai_cfg["tts_model"] = rest[4:].strip(); _ai_save()
            await _safe_edit(message, f"✅ مدل صدا: `{_ai_cfg['tts_model']}`")
        elif rest:
            _ai_cfg["text_model"] = rest; _ai_save()
            await _safe_edit(message, f"✅ مدل متن: `{rest}`")
        else:
            await _safe_edit(message, "❌ `جمنای مدل ها` | `جمنای مدل NAME` | `جمنای مدل صدا NAME`")
        return True
    if first == "صدا":
        if rest in ("زن", "مرد"):
            _ai_cfg["gender"] = "male" if rest == "مرد" else "female"; _ai_cfg.pop("voice", None)
        elif rest and re.fullmatch(r"[A-Za-z]{3,20}", rest):
            _ai_cfg["voice"] = rest.capitalize()
        else:
            await _safe_edit(message, "❌ `جمنای صدا زن` | `جمنای صدا مرد` | `جمنای صدا Puck`"); return True
        _ai_save(); await _safe_edit(message, f"✅ صدای ویس: {_voice_name()}")
        return True
    if first == "خودکار" and rest in ("روشن", "خاموش"):
        _ai_cfg["auto_stt"] = rest == "روشن"; _ai_save()
        await _safe_edit(message, f"📝 تبدیل خودکار ویس‌های ورودی پیوی {'روشن' if _ai_cfg['auto_stt'] else 'خاموش'} شد")
        return True
    if first == "ریست" and not rest:
        for k in ("text_model", "tts_model", "voice", "gender"): _ai_cfg.pop(k, None)
        _ai_save(); await _safe_edit(message, "🔄 تنظیمات مدل و صدا ریست شد")
        return True
    return False

@app.on_message(filters.me & _mk_filter(_f_ask, "ai_ask"))
async def ai_ask_cmd(client, message):
    name, arg = _split_cmd(message.text, AI_ASK_NAMES)
    if arg and await _ai_admin(message, arg): return
    r = message.reply_to_message
    await _safe_edit(message, "🤖 در حال فکر کردن...")
    tmp = []
    try:
        parts = []
        ctx = (r.text or r.caption or "") if r else ""
        if ctx:
            parts.append({"text": f"Message being discussed:\n\"\"\"\n{ctx[:6000]}\n\"\"\""})
        parts += await _media_parts(client, r, tmp)
        parts.append({"text": arg or "Explain / respond helpfully to the message above."})
        ans = await asyncio.to_thread(_gem_text, parts)
        head = f"❓ {arg[:200]}\n\n" if arg else ""
        await _send_long(client, message, f"{head}🤖 {ans}")
    except Exception as e:
        await _safe_edit(message, _ai_err(e))
    finally:
        _rm(tmp)

def _f_sum(m):
    t = (m.text or "").strip()
    return (t == "خلاصه" and bool(m.reply_to_message)) or bool(re.fullmatch(r"خلاصه \d{1,3}", t))

@app.on_message(filters.me & _mk_filter(_f_sum, "ai_sum"))
async def ai_summary_cmd(client, message):
    t = message.text.strip(); r = message.reply_to_message
    await _safe_edit(message, "🧾 در حال خلاصه‌سازی...")
    tmp = []
    try:
        if t == "خلاصه":
            parts = [{"text": "Summarize the following in a few short lines (same language as the content):"}]
            if r.text or r.caption: parts.append({"text": (r.text or r.caption)[:12000]})
            parts += await _media_parts(client, r, tmp)
        else:
            n = min(int(t.split()[1]), 300); lines = []
            async for m in client.get_chat_history(message.chat.id, limit=n + 1):
                if m.id == message.id: continue
                who = m.from_user.first_name if m.from_user else "؟"
                body = m.text or m.caption
                if not body and m.media: body = "[" + str(m.media).split(".")[-1].lower() + "]"
                if body: lines.append(f"{who}: {body}")
            lines.reverse()
            parts = [{"text": "Summarize this chat conversation: main topics, decisions, and anything needing a reply. "
                              "Be brief, same language as the chat.\n\n" + "\n".join(lines)[:30000]}]
        ans = await asyncio.to_thread(_gem_text, parts)
        await _send_long(client, message, f"🧾 **خلاصه:**\n\n{ans}")
    except Exception as e:
        await _safe_edit(message, _ai_err(e))
    finally:
        _rm(tmp)

def _f_fix(m):
    t = (m.text or "").strip()
    return (t in ("اصلاح", "اصلاح متن") and bool(m.reply_to_message)) or t.startswith("اصلاح متن ")

@app.on_message(filters.me & _mk_filter(_f_fix, "ai_fix"))
async def ai_fix_cmd(client, message):
    t = message.text.strip(); r = message.reply_to_message
    src = t[len("اصلاح متن "):].strip() if t.startswith("اصلاح متن ") else ((r.text or r.caption or "") if r else "")
    if not src: return await _safe_edit(message, "❌ روی یک متن ریپلای کنید یا `اصلاح متن ...` بنویسید")
    await _safe_edit(message, "✍️ در حال اصلاح...")
    try:
        ans = await asyncio.to_thread(_gem_text, [{"text": "Fix spelling, grammar and punctuation of this text without changing its "
                                                           "meaning or language. Return ONLY the corrected text:\n\n" + src[:6000]}], None)
        await _send_long(client, message, ans)
    except Exception as e:
        await _safe_edit(message, _ai_err(e))

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
@app.on_message(filters.me & filters.regex(r"^قلم \d+ .+"))
async def fancy_cmd(client, message):
    parts = message.text.split(" ", 2)
    try: sid = int(parts[1])
    except Exception: return await message.edit("❌ `قلم 1 متن`")
    tr = FANCY_TRANS.get(sid); w = WRAPPERS.get(sid, ("", ""))
    out = w[0] + (parts[2].translate(tr) if tr else parts[2]) + w[1]
    await message.edit(out)

@app.on_message(filters.me & filters.regex(r"^لیست قلم$"))
async def fancy_list_cmd(client, message):
    sample = "Persian Gulf 123"
    lines = []
    for i in sorted(FANCY_TRANS):
        w = WRAPPERS.get(i, ("", ""))
        lines.append(f"{i} - {w[0]}{sample.translate(FANCY_TRANS[i])}{w[1]}")
    await _safe_edit(message, "🔤 **۳۰ فونت متن (قلم):**\n\n" + "\n".join(lines) + "\n\n✅ با `قلم شماره متن` استفاده کنید")

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

@app.on_message(filters.private & filters.incoming & (filters.photo | filters.video | filters.voice | filters.video_note), group=4)
async def handle_timed_media(client, message):
    try:
        if feat.get("timed_save", True):
            await save_timed_media(client, message)
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

@app.on_message(filters.private & ~filters.me, group=3)
async def apply_actions_private(client, message): await apply_chat_actions(client, message)

@app.on_message(filters.group & ~filters.me, group=3)
async def apply_actions_group(client, message): await apply_chat_actions(client, message)

# ==============================================================================
# ★ قابلیت‌های جدید Persian Gulf Self (صفحه ۲ و ۳ پنل) ★
# ==============================================================================
FEATURES_FILE = "features.json"
_FEAT_DEFAULTS = {
    "seen": False,
    "filter_on": False, "filter_words": [], "filter_pv": True, "filter_groups": True,
    "guard_on": False, "guard_links": False, "guard_chats": [], "guard_pv": False,
    "timed_save": True, "timed_saved_count": 0,
    "secretary_on": False, "secretary_text": "سلام 🌹 فعلاً در دسترس نیستم، به‌زودی پاسخ می‌دهم.",
    "forcejoin_on": False, "forcejoin_chat": "", "forcejoin_last_error": "",
    "firstcomment_on": False, "firstcomment_text": "", "firstcomment_chats": [],
    "friends": [],
}
feat = {**_FEAT_DEFAULTS, **jload(FEATURES_FILE, {})}
def fsave(): jsave(FEATURES_FILE, feat)

# نگاشت اکشن‌های پنل به کلیدهای feat (خاموش/روشن سریع از پنل هلپر)
FEAT_TOGGLES = {
    "toggle_seen": "seen", "toggle_filter": "filter_on", "toggle_guard": "guard_on",
    "toggle_guardlinks": "guard_links", "toggle_secretary": "secretary_on",
    "toggle_forcejoin": "forcejoin_on", "toggle_firstcomment": "firstcomment_on",
    "toggle_filterpv": "filter_pv", "toggle_filtergroups": "filter_groups",
    "toggle_guardpv": "guard_pv", "toggle_timedsave": "timed_save",
}

def _onoff(word): return word == "روشن"
def _yn(v): return "🟢 روشن" if v else "🔴 خاموش"

async def _safe_edit(message, text, **kw):
    try: return await message.edit(text, **kw)
    except TypeError:   # پارامتر اضافه (مثل disable_web_page_preview) در این نسخه Pyrogram نیست
        try: return await message.edit(text)
        except Exception: return None
    except Exception: return None

# ---------------------------------------------------------------- 🔍 سرچ
def _wiki_search(q):
    hdr = {"User-Agent": "PersianGulfSelf/1.0"}
    for lang in ("fa", "en"):
        try:
            r = requests.get(f"https://{lang}.wikipedia.org/w/api.php", timeout=15, headers=hdr,
                             params={"action": "query", "list": "search", "srsearch": q,
                                     "format": "json", "srlimit": 4, "utf8": 1})
            hits = r.json().get("query", {}).get("search", [])
            if not hits: continue
            title = hits[0]["title"]
            s = requests.get(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title),
                             timeout=15, headers=hdr).json()
            url = (s.get("content_urls", {}).get("desktop", {}).get("page")
                   or f"https://{lang}.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")))
            return {"lang": lang, "title": title, "extract": (s.get("extract") or "")[:700],
                    "url": url, "others": [h["title"] for h in hits[1:]]}
        except Exception:
            continue
    return None

@app.on_message(filters.me & filters.regex(r"^سرچ .+"))
async def search_cmd(client, message):
    q = message.text.split(" ", 1)[1].strip()
    await _safe_edit(message, "🔍 در حال جستجو...")
    res = await asyncio.to_thread(_wiki_search, q)
    if not res:
        return await _safe_edit(message, f"❌ نتیجه‌ای برای «{q}» پیدا نشد")
    t = f"🔍 **{res['title']}** ({'ویکی‌پدیا فارسی' if res['lang'] == 'fa' else 'Wikipedia EN'})\n\n{res['extract']}\n\n🔗 {res['url']}"
    if res["others"]:
        t += "\n\n📌 موارد مرتبط: " + " | ".join(res["others"])
    await _safe_edit(message, t, disable_web_page_preview=True)

# ---------------------------------------------------------------- 🎲 تقلب
CHEAT_MAP = {"تاس": ("🎲", 6), "دارت": ("🎯", 6), "بولینگ": ("🎳", 6),
             "بسکتبال": ("🏀", 5), "فوتبال": ("⚽", 5), "اسلات": ("🎰", 64)}

@app.on_message(filters.me & filters.regex(r"^تقلب (تاس|دارت|بولینگ|بسکتبال|فوتبال|اسلات) (\d+)$"))
async def cheat_cmd(client, message):
    kind, val = message.matches[0].group(1), int(message.matches[0].group(2))
    emoji, mx = CHEAT_MAP[kind]
    if not 1 <= val <= mx:
        return await _safe_edit(message, f"❌ برای {kind} عدد باید بین 1 تا {mx} باشد")
    await _safe_edit(message, f"{emoji} در حال تلاش برای عدد {val} ...")
    for _ in range(40):
        try:
            m = await client.send_dice(message.chat.id, emoji)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1); continue
        except Exception as e:
            return await _safe_edit(message, f"❌ `{e}`")
        if m.dice and m.dice.value == val:
            try: await message.delete()
            except Exception: pass
            return
        await asyncio.sleep(0.7)
        try: await m.delete()
        except Exception: pass
    await _safe_edit(message, "😕 بعد از ۴۰ تلاش به عدد مورد نظر نرسید")

# ---------------------------------------------------------------- 📸 اسکرین
@app.on_message(filters.me & filters.regex(r"^اسکرین .+"))
async def screenshot_cmd(client, message):
    url = message.text.split(" ", 1)[1].strip()
    if not re.match(r"^https?://", url): url = "https://" + url
    await _safe_edit(message, "📸 در حال گرفتن اسکرین‌شات...")
    def fetch():
        r = requests.get("https://image.thum.io/get/width/1280/crop/800/noanimate/" + url, timeout=60)
        if r.status_code != 200 or "image" not in r.headers.get("content-type", ""):
            raise RuntimeError(f"HTTP {r.status_code}")
        return r.content
    try:
        data = await asyncio.to_thread(fetch)
        path = f"shot_{message.id}.png"
        with open(path, "wb") as f: f.write(data)
        await client.send_photo(message.chat.id, path, caption=f"📸 {url}")
        os.remove(path)
        await message.delete()
    except Exception as e:
        await _safe_edit(message, f"❌ اسکرین‌شات ناموفق بود: `{e}`")

# ---------------------------------------------------------------- 💬 کامنت اول
async def _resolve_chat(client, ref):
    ref = ref.strip()
    m = re.match(r"^(?:https?://)?t\.me/([\w\d_]+)", ref)
    if m: ref = m.group(1)
    return await client.get_chat(ref.lstrip("@"))

@app.on_message(filters.me & filters.regex(r"^کامنت اول (روشن|خاموش)$"))
async def fc_toggle(client, message):
    feat["firstcomment_on"] = _onoff(message.matches[0].group(1)); fsave()
    extra = ""
    if feat["firstcomment_on"] and (not feat["firstcomment_text"] or not feat["firstcomment_chats"]):
        extra = "\n⚠️ هنوز متن یا کانالی تنظیم نشده: `کامنت اول متن ...` و `کامنت اول افزودن @کانال`"
    await _safe_edit(message, f"💬 کامنت اول: {_yn(feat['firstcomment_on'])}{extra}")

@app.on_message(filters.me & filters.regex(r"^کامنت اول متن .+"))
async def fc_text(client, message):
    feat["firstcomment_text"] = message.text.split("متن", 1)[1].strip(); fsave()
    await _safe_edit(message, "✅ متن کامنت اول ذخیره شد")

@app.on_message(filters.me & filters.regex(r"^کامنت اول (افزودن|حذف) .+"))
async def fc_chats(client, message):
    parts = message.text.split(" ", 3)
    act, ref = parts[2], parts[3] if len(parts) > 3 else ""
    try:
        chat = await _resolve_chat(client, ref)
    except Exception as e:
        return await _safe_edit(message, f"❌ کانال پیدا نشد: `{e}`")
    if act == "افزودن":
        if chat.id not in feat["firstcomment_chats"]: feat["firstcomment_chats"].append(chat.id)
        msg = f"✅ «{chat.title}» به لیست کامنت اول اضافه شد"
    else:
        if chat.id in feat["firstcomment_chats"]: feat["firstcomment_chats"].remove(chat.id)
        msg = f"🗑 «{chat.title}» از لیست حذف شد"
    fsave(); await _safe_edit(message, msg)

@app.on_message(filters.me & filters.regex(r"^کامنت اول لیست$"))
async def fc_list(client, message):
    lines = []
    for cid in feat["firstcomment_chats"]:
        try: lines.append(f"• {(await client.get_chat(cid)).title} (`{cid}`)")
        except Exception: lines.append(f"• `{cid}`")
    await _safe_edit(message, f"💬 **کامنت اول** {_yn(feat['firstcomment_on'])}\n📝 متن: {feat['firstcomment_text'] or '—'}\n\n"
                              + ("\n".join(lines) if lines else "کانالی ثبت نشده"))

@app.on_message(filters.channel, group=11)
async def first_comment_handler(client, message):
    if not (feat["firstcomment_on"] and feat["firstcomment_text"]): return
    if message.chat.id not in feat["firstcomment_chats"]: return
    try:
        dm = await client.get_discussion_message(message.chat.id, message.id)
        if dm: await dm.reply_text(feat["firstcomment_text"])
    except Exception as e:
        print("⚠️ کامنت اول ناموفق:", e)

# ---------------------------------------------------------------- 🚫 فیلتر کلمات
@app.on_message(filters.me & filters.regex(r"^فیلتر (روشن|خاموش)$"))
async def wf_toggle(client, message):
    feat["filter_on"] = _onoff(message.matches[0].group(1)); fsave()
    await _safe_edit(message, f"🚫 فیلتر کلمات: {_yn(feat['filter_on'])} ({len(feat['filter_words'])} کلمه)\n"
                              f"👤 پیوی: {_yn(feat['filter_pv'])} | 👥 گروه: {_yn(feat['filter_groups'])}")

@app.on_message(filters.me & filters.regex(r"^فیلتر (پیوی|گروه) (روشن|خاموش)$"))
async def wf_scope(client, message):
    scope, val = message.matches[0].group(1), _onoff(message.matches[0].group(2))
    feat["filter_pv" if scope == "پیوی" else "filter_groups"] = val; fsave()
    await _safe_edit(message, f"🚫 فیلتر در {scope}: {_yn(val)}")

@app.on_message(filters.me & filters.regex(r"^فیلتر (افزودن|حذف) .+"))
async def wf_edit(client, message):
    parts = message.text.split(" ", 2)
    act, word = parts[1], parts[2].strip()
    if act == "افزودن":
        if word not in feat["filter_words"]: feat["filter_words"].append(word)
        msg = f"✅ «{word}» به فیلتر اضافه شد"
    elif word in feat["filter_words"]:
        feat["filter_words"].remove(word); msg = f"🗑 «{word}» حذف شد"
    else:
        msg = "❌ این کلمه در لیست نیست"
    fsave(); await _safe_edit(message, msg)

@app.on_message(filters.me & filters.regex(r"^فیلتر (لیست|پاکسازی)$"))
async def wf_list(client, message):
    if message.matches[0].group(1) == "پاکسازی":
        feat["filter_words"].clear(); fsave()
        return await _safe_edit(message, "🧹 لیست فیلتر پاک شد")
    w = feat["filter_words"]
    await _safe_edit(message, f"🚫 **فیلتر کلمات** {_yn(feat['filter_on'])}\n\n" + ("\n".join(f"• {x}" for x in w) if w else "لیست خالی است"))

# ---------------------------------------------------------------- 📌 عضویت اجباری پیوی
@app.on_message(filters.me & filters.regex(r"^عضویت اجباری (روشن|خاموش)$"))
async def fj_toggle(client, message):
    feat["forcejoin_on"] = _onoff(message.matches[0].group(1)); fsave()
    extra = "" if feat["forcejoin_chat"] or not feat["forcejoin_on"] else "\n⚠️ کانال تنظیم نشده: `عضویت اجباری کانال @کانال`"
    if feat.get("forcejoin_last_error"): extra += "\n" + feat["forcejoin_last_error"]
    await _safe_edit(message, f"📌 عضویت اجباری پیوی: {_yn(feat['forcejoin_on'])}{extra}")

@app.on_message(filters.me & filters.regex(r"^عضویت اجباری وضعیت$"))
async def fj_status(client, message):
    t = (f"📌 **عضویت اجباری پیوی** {_yn(feat['forcejoin_on'])}\n"
         f"📢 کانال/گروه: {feat['forcejoin_chat'] or '—'}")
    if feat.get("forcejoin_last_error"): t += "\n\n" + feat["forcejoin_last_error"]
    else: t += "\n\n✅ آخرین بررسی بدون خطا بوده"
    await _safe_edit(message, t)

@app.on_message(filters.me & filters.regex(r"^عضویت اجباری تست( .+)?$"))
async def fj_test(client, message):
    if not feat["forcejoin_chat"]:
        return await _safe_edit(message, "❌ اول کانال را ثبت کنید: `عضویت اجباری کانال @کانال`")
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.id
    else:
        arg = (message.matches[0].group(1) or "").strip()
        if arg:
            try: target = (await client.get_users(arg.lstrip("@"))).id
            except Exception as e: return await _safe_edit(message, f"❌ کاربر پیدا نشد: `{e}`")
    if not target:
        return await _safe_edit(message, "❌ روی پیام کسی ریپلای کنید یا بنویسید: `عضویت اجباری تست @user`")
    chat = feat["forcejoin_chat"]
    chat = int(chat) if re.fullmatch(r"-?\d+", chat) else chat
    is_member, err = await _check_forcejoin_membership(client, chat, target)
    if err:
        await _safe_edit(message, f"🧪 نتیجه تست:\n{err}")
    else:
        await _safe_edit(message, f"🧪 نتیجه تست:\n{'✅ عضو است' if is_member else '❌ عضو نیست'}")

@app.on_message(filters.me & filters.regex(r"^عضویت اجباری کانال .+"))
async def fj_chat(client, message):
    ref = message.text.split("کانال", 1)[1].strip()
    try:
        chat = await _resolve_chat(client, ref)
    except Exception as e:
        return await _safe_edit(message, f"❌ کانال پیدا نشد: `{e}`")
    feat["forcejoin_chat"] = f"@{chat.username}" if chat.username else str(chat.id); fsave()
    _fj_ok.clear()
    await _safe_edit(message, f"✅ کانال عضویت اجباری: «{chat.title}»\n⚠️ حساب شما باید ادمین آن کانال باشد تا عضویت افراد قابل بررسی شود")

# ---------------------------------------------------------------- 📰 منشی
@app.on_message(filters.me & filters.regex(r"^منشی (روشن|خاموش)$"))
async def sec_toggle(client, message):
    feat["secretary_on"] = _onoff(message.matches[0].group(1)); fsave()
    await _safe_edit(message, f"📰 منشی: {_yn(feat['secretary_on'])}")

@app.on_message(filters.me & filters.regex(r"^منشی متن .+"))
async def sec_text(client, message):
    feat["secretary_text"] = message.text.split("متن", 1)[1].strip(); fsave()
    await _safe_edit(message, "✅ متن منشی ذخیره شد")

@app.on_message(filters.me & filters.regex(r"^منشی وضعیت$"))
async def sec_status(client, message):
    await _safe_edit(message, f"📰 **منشی** {_yn(feat['secretary_on'])}\n📝 متن:\n{feat['secretary_text']}")

# ---------------------------------------------------------------- 🏷 تگ
@app.on_message(filters.me & filters.regex(r"^تگ( .+)?$"))
async def tagall_cmd(client, message):
    if message.chat.type not in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
        return await _safe_edit(message, "❌ این دستور فقط در گروه کار می‌کند")
    txt = (message.text.split(" ", 1)[1].strip() if " " in message.text else "📣")
    from html import escape as _esc
    members = []
    try:
        async for m in client.get_chat_members(message.chat.id, limit=100):
            u = m.user
            if u and not u.is_bot and not u.is_deleted: members.append(u)
    except Exception as e:
        return await _safe_edit(message, f"❌ دریافت اعضا ناموفق بود: `{e}`")
    if not members:
        return await _safe_edit(message, "❌ عضوی پیدا نشد")
    await _safe_edit(message, f"🏷 در حال تگ {len(members)} نفر ...")
    for i in range(0, len(members), 5):
        chunk = members[i:i + 5]
        line = " ".join(f'<a href="tg://user?id={u.id}">{_esc((u.first_name or "کاربر")[:12])}</a>' for u in chunk)
        try:
            await client.send_message(message.chat.id, f"{_esc(txt)}\n{line}", parse_mode=enums.ParseMode.HTML)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
        except Exception: pass
        await asyncio.sleep(2)
    try: await message.delete()
    except Exception: pass

# ---------------------------------------------------------------- 🗑 حذف (ریپلای)
@app.on_message(filters.me & filters.regex(r"^حذف$"))
async def delete_reply_cmd(client, message):
    r = message.reply_to_message
    if not r:
        return await _safe_edit(message, "❌ روی پیامی که می‌خواهید حذف شود ریپلای کنید")
    try:
        await r.delete()
        await message.delete()
    except Exception as e:
        await _safe_edit(message, f"❌ حذف نشد: `{e}`")

# ---------------------------------------------------------------- 🤝 دوست
FRIEND_LINES = ["🌹 قربانت", "😍 عزیزی", "🔥 دمت گرم", "❤️ دوستت دارم", "🙌 همیشه بهتر از بهترین‌ها"]

@app.on_message(filters.me & filters.regex(r"^(دوست|حذف دوست|لیست دوست|دوستان|پاک کردن دوستان)$"))
async def friend_cmd(client, message):
    t = message.text
    if t in ("دوست", "حذف دوست"):
        if not (message.reply_to_message and message.reply_to_message.from_user):
            return await _safe_edit(message, "❌ ریپلای کنید")
        uid = message.reply_to_message.from_user.id
        if t == "دوست":
            if uid not in feat["friends"]: feat["friends"].append(uid)
            msg = "🤝 دوست اضافه شد"
        else:
            if uid in feat["friends"]: feat["friends"].remove(uid)
            msg = "✅ دوست حذف شد"
        fsave(); return await _safe_edit(message, msg)
    if t in ("لیست دوست", "دوستان"):
        lines = []
        for f in feat["friends"]:
            try:
                u = await client.get_users(f)
                lines.append(f"• {u.first_name} | @{u.username or 'ندارد'} | `{f}`")
            except Exception: lines.append(f"• `{f}`")
        return await _safe_edit(message, f"🤝 **لیست دوستان ({len(feat['friends'])}):**\n" + ("\n".join(lines) if lines else "خالی است"))
    feat["friends"].clear(); fsave()
    await _safe_edit(message, "🧹 لیست دوستان پاک شد")

# ---------------------------------------------------------------- 🕵️ کپی پروفایل
PROFILE_BACKUP = "profile_backup.json"
PROFILE_BACKUP_PHOTO = os.path.abspath("profile_backup.jpg")

@app.on_message(filters.me & filters.regex(r"^کپی پروفایل( @?\w+)?$"))
async def copy_profile_cmd(client, message):
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    else:
        m = re.match(r"^کپی پروفایل @?(\w+)$", message.text.strip())
        if m:
            try: target = await client.get_users(m.group(1))
            except Exception: target = None
    if not target:
        return await _safe_edit(message, "❌ ریپلای کنید یا بنویسید: `کپی پروفایل @یوزر`")
    await _safe_edit(message, "🕵️ در حال کپی پروفایل...")
    try:
        me = await client.get_me()
        if not os.path.exists(PROFILE_BACKUP):   # پشتیبان اولیه (فقط یک‌بار)
            bio = ""
            try: bio = (await client.get_chat("me")).bio or ""
            except Exception: pass
            ph = None
            if me.photo:
                try: ph = await client.download_media(me.photo.big_file_id, file_name=PROFILE_BACKUP_PHOTO)
                except Exception: ph = None
            jsave(PROFILE_BACKUP, {"first_name": me.first_name or "", "last_name": me.last_name or "", "bio": bio, "photo": ph})
        t_bio = ""
        try: t_bio = (await client.get_chat(target.id)).bio or ""
        except Exception: pass
        await client.update_profile(first_name=target.first_name or "خالی", last_name=target.last_name or "", bio=t_bio[:70])
        if target.photo:
            p = await client.download_media(target.photo.big_file_id)
            await client.set_profile_photo(photo=p)
        await _safe_edit(message, f"✅ پروفایل «{target.first_name}» کپی شد\n↩️ برای برگشت: `بازگردانی پروفایل`")
    except Exception as e:
        await _safe_edit(message, f"❌ `{e}`")

@app.on_message(filters.me & filters.regex(r"^بازگردانی پروفایل$"))
async def restore_profile_cmd(client, message):
    bk = jload(PROFILE_BACKUP, None)
    if not bk:
        return await _safe_edit(message, "❌ پشتیبانی از پروفایل شما وجود ندارد")
    try:
        await client.update_profile(first_name=bk.get("first_name") or "خالی", last_name=bk.get("last_name", ""), bio=bk.get("bio", ""))
        try:
            async for ph in client.get_chat_photos("me", limit=1):
                await client.delete_profile_photos(ph.file_id)
        except Exception: pass
        if bk.get("photo") and os.path.exists(bk["photo"]):
            await client.set_profile_photo(photo=bk["photo"])
        try: os.remove(PROFILE_BACKUP)
        except Exception: pass
        await _safe_edit(message, "✅ پروفایل اصلی شما بازگردانی شد")
    except Exception as e:
        await _safe_edit(message, f"❌ `{e}`")

# ---------------------------------------------------------------- 🛡 نگهبان چت
_guard_admins = {}     # chat_id -> (ts, set(ids))
_guard_flood = {}      # (chat, user) -> [timestamps]

@app.on_message(filters.me & filters.regex(r"^نگهبان (روشن|خاموش)$"))
async def guard_toggle(client, message):
    if message.chat.type not in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
        return await _safe_edit(message, "❌ این دستور را داخل گروه بزنید")
    cid = message.chat.id
    if _onoff(message.matches[0].group(1)):
        if cid not in feat["guard_chats"]: feat["guard_chats"].append(cid)
        feat["guard_on"] = True
        msg = "🛡 نگهبان این گروه روشن شد\n⚠️ برای حذف پیام‌ها باید در گروه ادمین (با دسترسی حذف) باشید"
    else:
        if cid in feat["guard_chats"]: feat["guard_chats"].remove(cid)
        if not feat["guard_chats"]: feat["guard_on"] = False
        msg = "🛡 نگهبان این گروه خاموش شد"
    fsave(); await _safe_edit(message, msg)

@app.on_message(filters.me & filters.regex(r"^نگهبان لینک (روشن|خاموش)$"))
async def guard_links_toggle(client, message):
    feat["guard_links"] = _onoff(message.matches[0].group(1)); fsave()
    await _safe_edit(message, f"🔗 حذف لینک توسط نگهبان: {_yn(feat['guard_links'])}")

@app.on_message(filters.me & filters.regex(r"^نگهبان پیوی (روشن|خاموش)$"))
async def guard_pv_toggle(client, message):
    feat["guard_pv"] = _onoff(message.matches[0].group(1)); fsave()
    await _safe_edit(message, f"🛡 نگهبان پیوی: {_yn(feat['guard_pv'])}\n(مخاطبین و دوستان معاف‌اند؛ حذف دو طرفه)")

@app.on_message(filters.me & filters.regex(r"^نگهبان وضعیت$"))
async def guard_status(client, message):
    await _safe_edit(message, f"🛡 **نگهبان چت** {_yn(feat['guard_on'])}\n🔗 حذف لینک: {_yn(feat['guard_links'])}\n👤 نگهبان پیوی: {_yn(feat['guard_pv'])}\n💬 گروه‌های تحت نگهبانی: {len(feat['guard_chats'])}")

async def _guard_is_admin(client, chat_id, user_id):
    now = time.time()
    ts, ids = _guard_admins.get(chat_id, (0, set()))
    if now - ts > 300:
        ids = set()
        try:
            async for m in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                if m.user: ids.add(m.user.id)
        except Exception: pass
        _guard_admins[chat_id] = (now, ids)
    return user_id in ids

_LINK_RE = re.compile(r"(https?://|t\.me/|telegram\.me/|www\.|@[A-Za-z][\w]{4,})", re.I)

def _has_link(message):
    txt = (message.text or "") + " " + (message.caption or "")
    ents = (message.entities or []) + (message.caption_entities or [])
    return bool(_LINK_RE.search(txt) or any(str(getattr(e, "type", "")).lower().endswith(("url", "text_link")) for e in ents))

async def _nf_guard_pv(client, message):
    """نگهبان پیوی: لینک/فلود از غیرمخاطبین با حذف دو طرفه"""
    if not feat["guard_pv"] or not message.from_user: return False
    u = message.from_user
    if u.is_bot or u.is_self or u.id == 777000 or getattr(u, "is_contact", False) or u.id in feat["friends"]:
        return False
    cid = message.chat.id
    bad = feat["guard_links"] and _has_link(message)
    now = time.time()
    hist = [t for t in _guard_flood.get((cid, u.id), []) if now - t < 8] + [now]
    _guard_flood[(cid, u.id)] = hist
    if not (bad or len(hist) >= 6): return False
    try:
        await client.delete_messages(cid, message.id, revoke=True)
        return True
    except Exception:
        return False

async def _nf_guard(client, message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return await _nf_guard_pv(client, message)
    if not (feat["guard_on"] and message.chat.id in feat["guard_chats"]): return False
    if message.chat.type not in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP) or not message.from_user: return False
    uid, cid = message.from_user.id, message.chat.id
    if await _guard_is_admin(client, cid, uid): return False
    bad = feat["guard_links"] and _has_link(message)
    now = time.time()
    hist = [t for t in _guard_flood.get((cid, uid), []) if now - t < 8] + [now]
    _guard_flood[(cid, uid)] = hist
    flood = len(hist) >= 6
    if not (bad or flood): return False
    try: await message.delete()
    except Exception: pass
    if len(hist) >= 9:
        try:
            from datetime import timedelta
            await client.restrict_chat_member(cid, uid, ChatPermissions(), until_date=datetime.now() + timedelta(minutes=10))
            _guard_flood[(cid, uid)] = []
        except Exception: pass
    return True

# ---------------------------------------------------------------- 🎨 لوگو
def make_logo(text, out_path="logo.png"):
    """لوگوی طلایی روی پس‌زمینه سرمه‌ای از متن می‌سازد"""
    from PIL import Image, ImageDraw, ImageFilter, ImageOps
    W, H = 1024, 512
    rg = Image.radial_gradient("L").resize((W, H))
    bg = ImageOps.colorize(rg, black=(24, 48, 96), white=(4, 8, 20)).convert("RGB")
    txt = _panel_shape_text((text or "").strip()[:30] or "LOGO")
    d0 = ImageDraw.Draw(bg)
    fs = 220
    ft = _panel_font(fs)
    while d0.textlength(txt, font=ft) > W * 0.86 and fs > 30:
        fs -= 6; ft = _panel_font(fs)
    bb = d0.textbbox((0, 0), txt, font=ft, stroke_width=4)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x, y = (W - tw) // 2 - bb[0], (H - th) // 2 - bb[1] - 14
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).text((x, y), txt, font=ft, fill=255)
    outline = Image.new("L", (W, H), 0)
    ImageDraw.Draw(outline).text((x, y), txt, font=ft, fill=255, stroke_width=4, stroke_fill=255)
    # درخشش طلایی
    glow = mask.filter(ImageFilter.GaussianBlur(20)).point(lambda v: int(v * 0.6))
    bg = Image.composite(Image.new("RGB", (W, H), (255, 190, 60)), bg, glow)
    # پر کردن با گرادیان طلایی
    top, bot = y + bb[1], y + bb[3]
    grad = Image.new("RGB", (W, H))
    gd = ImageDraw.Draw(grad)
    for row in range(H):
        k = min(1.0, max(0.0, (row - top) / max(1, bot - top)))
        gd.line([(0, row), (W, row)], fill=(int(255 - 45 * k), int(228 - 95 * k), int(130 - 80 * k)))
    bg.paste((70, 40, 6), mask=outline)
    bg.paste(grad, mask=mask)
    # تزئینات زیر متن
    d = ImageDraw.Draw(bg)
    ly = min(H - 50, y + bb[3] + 46)
    gold = (255, 205, 90)
    d.line([(W * 0.18, ly), (W * 0.44, ly)], fill=gold, width=3)
    d.line([(W * 0.56, ly), (W * 0.82, ly)], fill=gold, width=3)
    d.polygon([(W / 2, ly - 14), (W / 2 + 14, ly), (W / 2, ly + 14), (W / 2 - 14, ly)], fill=gold)
    bg.save(out_path, "PNG")
    return out_path

@app.on_message(filters.me & filters.regex(r"^لوگو .+"))
async def logo_cmd(client, message):
    text = message.text.split(" ", 1)[1].strip()
    await _safe_edit(message, "🎨 در حال ساخت لوگو...")
    path = f"logo_{message.id}.png"
    try:
        await asyncio.to_thread(make_logo, text, path)
        await client.send_photo(message.chat.id, path)
        os.remove(path)
        await message.delete()
    except Exception as e:
        await _safe_edit(message, f"❌ ساخت لوگو ناموفق بود: `{e}`")

# ---------------------------------------------------------------- 📝 محتوا
def _fmt_size(n):
    try: n = float(n)
    except Exception: return "?"
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024: return f"{n:.1f} {u}" if u != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} TB"

def _fmt_dur(s):
    try: s = int(s)
    except Exception: return "?"
    return f"{s // 60}:{s % 60:02d}"

def describe_message(m):
    L = [f"🆔 پیام: `{getattr(m, 'id', '?')}`"]
    g = lambda o, k, d=None: getattr(o, k, d)
    kind = "متن"
    if g(m, "photo"):
        p = m.photo; kind = "عکس"; L.append(f"🖼 عکس {g(p,'width','?')}×{g(p,'height','?')} | {_fmt_size(g(p,'file_size'))}")
    elif g(m, "video"):
        v = m.video; kind = "ویدیو"; L.append(f"🎬 ویدیو {g(v,'width','?')}×{g(v,'height','?')} | {_fmt_dur(g(v,'duration'))} | {_fmt_size(g(v,'file_size'))}")
    elif g(m, "animation"):
        a = m.animation; kind = "گیف"; L.append(f"🎞 گیف {g(a,'width','?')}×{g(a,'height','?')} | {_fmt_dur(g(a,'duration'))} | {_fmt_size(g(a,'file_size'))}")
    elif g(m, "video_note"):
        v = m.video_note; kind = "ویدیو گرد"; L.append(f"⭕ ویدیو گرد | {_fmt_dur(g(v,'duration'))} | {_fmt_size(g(v,'file_size'))}")
    elif g(m, "voice"):
        v = m.voice; kind = "ویس"; L.append(f"🎙 ویس | {_fmt_dur(g(v,'duration'))} | {_fmt_size(g(v,'file_size'))}")
    elif g(m, "audio"):
        a = m.audio; kind = "موزیک"; L.append(f"🎵 {g(a,'title') or '—'} - {g(a,'performer') or '—'} | {_fmt_dur(g(a,'duration'))} | {_fmt_size(g(a,'file_size'))}")
    elif g(m, "sticker"):
        s = m.sticker; kind = "استیکر"; L.append(f"🩷 استیکر {g(s,'emoji') or ''} | پک: {g(s,'set_name') or '—'}")
    elif g(m, "document"):
        d = m.document; kind = "فایل"; L.append(f"📎 {g(d,'file_name') or 'بدون نام'} | {g(d,'mime_type') or '?'} | {_fmt_size(g(d,'file_size'))}")
    elif g(m, "poll"):
        pl = m.poll; kind = "نظرسنجی"; L.append(f"📊 {g(pl,'question')} | {len(g(pl,'options',[]) or [])} گزینه")
    elif g(m, "contact"):
        c = m.contact; kind = "مخاطب"; L.append(f"👤 {g(c,'first_name','')} {g(c,'phone_number','')}")
    elif g(m, "location"):
        l = m.location; kind = "لوکیشن"; L.append(f"📍 {g(l,'latitude')}, {g(l,'longitude')}")
    elif g(m, "dice"):
        dc = m.dice; kind = "بازی"; L.append(f"🎲 {g(dc,'emoji')} = {g(dc,'value')}")
    text = g(m, "text") or g(m, "caption") or ""
    if text:
        L.append(f"✍️ متن: {len(text)} کاراکتر | {len(text.split())} کلمه")
    ents = (g(m, "entities") or []) + (g(m, "caption_entities") or [])
    if ents: L.append(f"🔤 فرمت/لینک‌ها: {len(ents)}")
    L.insert(1, f"📦 نوع محتوا: **{kind}**")
    d_ = g(m, "date")
    if d_: L.append(f"🕒 {d_.strftime('%Y-%m-%d %H:%M:%S')}")
    fw = g(m, "forward_from_chat") or g(m, "forward_from")
    if fw: L.append(f"↪️ فوروارد از: {g(fw,'title') or g(fw,'first_name') or '?'}")
    if g(m, "views"): L.append(f"👁 بازدید: {m.views}")
    return "\n".join(L)

@app.on_message(filters.me & filters.regex(r"^محتوا$"))
async def content_cmd(client, message):
    r = message.reply_to_message
    if not r: return await _safe_edit(message, "❌ روی یک پیام ریپلای کنید")
    await _safe_edit(message, "📝 **اطلاعات محتوا**\n\n" + describe_message(r))

# ---------------------------------------------------------------- ⭐ استارزی / 💎 موجودی
def _amount(b):
    if b is None: return 0.0
    if isinstance(b, (int, float)): return float(b)
    a = float(getattr(b, "amount", 0) or 0)
    if "ton" in type(b).__name__.lower(): return a / 1e9
    return a + float(getattr(b, "nanos", 0) or 0) / 1e9

async def _balance(client, ton=False):
    from pyrogram.raw import types as rawtypes
    kw = {"peer": rawtypes.InputPeerSelf()}
    if ton: kw["ton"] = True
    r = await client.invoke(rawfn.payments.GetStarsStatus(**kw))
    return _amount(getattr(r, "balance", None))

@app.on_message(filters.me & filters.regex(r"^(استارز|استارزی)$"))
async def stars_cmd(client, message):
    try:
        v = await _balance(client)
        await _safe_edit(message, f"⭐ **موجودی استارز:** `{v:,.0f}`")
    except Exception as e:
        await _safe_edit(message, f"❌ دریافت موجودی استارز ناموفق بود: `{e}`")

@app.on_message(filters.me & filters.regex(r"^موجودی$"))
async def balance_cmd(client, message):
    out = []
    try: out.append(f"⭐ استارز: `{await _balance(client):,.0f}`")
    except Exception as e: out.append(f"⭐ استارز: ❌ `{e}`")
    try: out.append(f"💎 تون (TON): `{await _balance(client, ton=True):.4f}`")
    except Exception as e: out.append(f"💎 تون (TON): ❌ `{e}`")
    await _safe_edit(message, "💰 **موجودی اکانت**\n\n" + "\n".join(out))

# ---------------------------------------------------------------- 🎬 انیمیشن
ANIMS = {
    "ماه": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"] * 2,
    "قلب": ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎"] * 2,
    "ساعت": ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"],
    "موج": ["🌊", "🌊🌊", "🌊🌊🌊", "🌊🌊🌊🌊", "🌊🌊🌊", "🌊🌊", "🌊"] * 2,
    "آتش": ["🔥", "🔥🔥", "🔥🔥🔥", "🔥🔥🔥🔥", "🔥🔥🔥🔥🔥"] * 2,
}

@app.on_message(filters.me & filters.regex(r"^انیمیشن .+"))
async def anim_cmd(client, message):
    arg = message.text.split(" ", 1)[1].strip()
    if arg in ANIMS:
        frames = ANIMS[arg]
    else:   # افکت تایپ‌شونده
        arg = arg[:200]
        step = max(1, len(arg) // 20)
        frames = [arg[:i] + " ▌" for i in range(step, len(arg), step)] + [arg]
    last = None
    for fr in frames:
        if fr == last: continue
        try:
            await message.edit(fr); last = fr
        except FloodWait as e:
            await asyncio.sleep(e.value); 
        except Exception: pass
        await asyncio.sleep(0.6)

# ---------------------------------------------------------------- 😍 ایموجی پریمیوم
_EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\u2764\u203C\u2049\u2122\u2139]\ufe0f?")
_premoji_cache = {}

def _utf16_len(s): return len(s.encode("utf-16-le")) // 2

async def _premium_emoji_id(client, emoji):
    key = emoji.replace("\ufe0f", "")
    if key in _premoji_cache: return _premoji_cache[key]
    did = None
    try:
        r = await client.invoke(rawfn.messages.SearchCustomEmoji(emoticon=emoji, hash=0))
        ids = getattr(r, "document_id", None)
        if ids: did = ids[0]
    except Exception: pass
    _premoji_cache[key] = did
    return did

@app.on_message(filters.me & filters.regex(r"^ایموجی پریمیوم( .+)?$"))
async def premoji_cmd(client, message):
    from pyrogram.types import MessageEntity
    text = message.text.split(" ", 2)[2] if message.text.count(" ") >= 2 else ""
    if not text and message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
    if not text:
        return await _safe_edit(message, "❌ `ایموجی پریمیوم متن ❤️🔥` یا ریپلای روی یک پیام")
    me = await client.get_me()
    if not getattr(me, "is_premium", False):
        return await _safe_edit(message, "⚠️ ارسال ایموجی پریمیوم فقط با اکانت پریمیوم ممکن است")
    ents, found = [], 0
    for m in _EMOJI_RE.finditer(text):
        did = await _premium_emoji_id(client, m.group(0))
        if did:
            found += 1
            ents.append(MessageEntity(type=enums.MessageEntityType.CUSTOM_EMOJI,
                                      offset=_utf16_len(text[:m.start()]), length=_utf16_len(m.group(0)),
                                      custom_emoji_id=did))
    if not found:
        return await _safe_edit(message, "❌ ایموجی قابل تبدیل در متن پیدا نشد")
    try:
        await client.send_message(message.chat.id, text, entities=ents)
        await message.delete()
    except Exception as e:
        await _safe_edit(message, f"❌ `{e}`")

# ---------------------------------------------------------------- 🎥 ساخت ویدیو گرد
def _ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        import shutil
        return shutil.which("ffmpeg")

def _round_cmd(exe, src, dst):
    return [exe, "-y", "-i", src, "-t", "59",
            "-vf", "crop='min(iw,ih)':'min(iw,ih)',scale=384:384,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
            "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", dst]

@app.on_message(filters.me & filters.regex(r"^ساخت ویدیو گرد$"))
async def round_video_cmd(client, message):
    r = message.reply_to_message
    media = r and (r.video or r.animation or r.video_note or (r.document and (r.document.mime_type or "").startswith("video")))
    if not media:
        return await _safe_edit(message, "❌ روی یک ویدیو یا گیف ریپلای کنید")
    exe = _ffmpeg_exe()
    if not exe:
        return await _safe_edit(message, "❌ ffmpeg نصب نیست؛ `imageio-ffmpeg` را به requirements اضافه کنید")
    await _safe_edit(message, "🎥 در حال ساخت ویدیو گرد...")
    src = dst = None
    try:
        src = await client.download_media(r, file_name=os.path.abspath(f"rv_src_{message.id}"))
        dst = os.path.abspath(f"rv_{message.id}.mp4")
        proc = await asyncio.create_subprocess_exec(*_round_cmd(exe, src, dst),
                                                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, err = await asyncio.wait_for(proc.communicate(), 240)
        if proc.returncode != 0 or not os.path.exists(dst):
            raise RuntimeError((err or b"").decode(errors="ignore")[-200:] or "ffmpeg failed")
        await client.send_video_note(message.chat.id, dst, length=384)
        await message.delete()
    except Exception as e:
        await _safe_edit(message, f"❌ ساخت ویدیو گرد ناموفق بود: `{e}`")
    finally:
        for p in (src, dst):
            try:
                if p and os.path.exists(p): os.remove(p)
            except Exception: pass

# ---------------------------------------------------------------- ⏳ ذخیره تایمدار
def _ttl_info(message):
    for attr, ext, kind in (("photo", "jpg", "عکس"), ("video", "mp4", "ویدیو"),
                            ("voice", "ogg", "ویس"), ("video_note", "mp4", "ویدیو گرد")):
        m = getattr(message, attr, None)
        if m and getattr(m, "ttl_seconds", None):
            return attr, ext, kind, m.ttl_seconds
    return None

async def save_timed_media(client, message):
    """مدیای زمان‌دار (خودتخریب‌شونده) را در Saved Messages ذخیره می‌کند؛ True اگر ذخیره شد"""
    info = _ttl_info(message)
    if not info: return False
    attr, ext, kind, ttl = info
    os.makedirs(SAVED_PHOTOS_DIR, exist_ok=True)
    path = os.path.join(SAVED_PHOTOS_DIR, f"timed-{attr}-{message.id}-{random.randint(1000, 9999)}.{ext}")
    await client.download_media(message, path)
    if not os.path.exists(path):
        raise RuntimeError("دانلود مدیا ممکن نشد")
    s = message.from_user
    u = f"@{s.username}" if s and s.username else "ندارد"
    ttl_txt = f"{ttl}s" if isinstance(ttl, int) and ttl < 100000 else "یک‌بار مشاهده"
    cap = (f"🔥 مدیای زمان‌دار ({kind})\n👤 {s.first_name if s else '?'}\n🆔 {u}\n"
           f"⏳ تایمر: {ttl_txt}\n⏰ {datetime.now().strftime('%H:%M:%S')}")
    try:
        if attr == "photo": await client.send_photo("me", path, caption=cap)
        elif attr == "video": await client.send_video("me", path, caption=cap)
        elif attr == "video_note":
            await client.send_video_note("me", path)
            await client.send_message("me", cap)
        else: await client.send_voice("me", path, caption=cap)
    finally:
        try: os.remove(path)
        except Exception: pass
    feat["timed_saved_count"] = feat.get("timed_saved_count", 0) + 1; fsave()
    return True

@app.on_message(filters.me & filters.regex(r"^ذخیره تایمدار (روشن|خاموش)$"))
async def timed_toggle(client, message):
    feat["timed_save"] = _onoff(message.matches[0].group(1)); fsave()
    await _safe_edit(message, f"⏳ ذخیره خودکار مدیای تایمدار: {_yn(feat['timed_save'])}")

@app.on_message(filters.me & filters.regex(r"^ذخیره تایمدار وضعیت$"))
async def timed_status(client, message):
    await _safe_edit(message, f"⏳ **ذخیره تایمدار** {_yn(feat['timed_save'])}\n📦 تعداد ذخیره‌شده: {feat.get('timed_saved_count', 0)}")

@app.on_message(filters.me & filters.regex(r"^ذخیره تایمدار$"))
async def timed_manual(client, message):
    r = message.reply_to_message
    if not r:
        return await _safe_edit(message, "❌ روی یک عکس/ویدیو/ویس تایمدار ریپلای کنید")
    try:
        ok = await save_timed_media(client, r)
    except Exception as e:
        return await _safe_edit(message, f"❌ ذخیره نشد (مدیای تایمدار بعد از باز شدن حذف می‌شود): `{e}`")
    await _safe_edit(message, "✅ در پیام‌های ذخیره‌شده ذخیره شد" if ok else "❌ این پیام مدیای تایمدار ندارد")

# ---------------------------------------------------------------- هندلر پیام‌های ورودی برای قابلیت‌های جدید
_fj_ok, _fj_notified, _sec_last, _friend_last, _seen_last = {}, {}, {}, {}, {}

async def _nf_seen(client, message):
    if not feat["seen"]: return
    now = time.time()
    if now - _seen_last.get(message.chat.id, 0) < 2: return
    _seen_last[message.chat.id] = now
    try: await client.read_chat_history(message.chat.id)
    except Exception: pass

def _norm_fa(s):
    """یکسان‌سازی متن فارسی (ی/ک عربی، نیم‌فاصله، کشیده، اعراب) برای تطبیق دقیق‌تر فیلتر"""
    s = (s or "").lower().replace("ي", "ی").replace("ك", "ک").replace("ۀ", "ه").replace("ة", "ه")
    return re.sub(r"[\u200c\u200d\u200e\u200f\u0640\u064b-\u065f\u0670]", "", s)

async def _nf_filter(client, message):
    """حذف پیام‌های شامل کلمه فیلتر شده؛ هم در پیوی (حذف دو طرفه) و هم در گروه‌ها"""
    if not (feat["filter_on"] and feat["filter_words"]): return False
    ct = message.chat.type
    if ct == enums.ChatType.PRIVATE:
        if not feat["filter_pv"]: return False
    elif ct in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
        if not feat["filter_groups"]: return False
    else:
        return False
    txt = _norm_fa((message.text or "") + " " + (message.caption or ""))
    if not txt: return False
    if any(w.strip() and _norm_fa(w) in txt for w in feat["filter_words"]):
        try:
            await client.delete_messages(message.chat.id, message.id, revoke=True)
            return True
        except Exception:
            return False
    return False

async def _check_forcejoin_membership(client, chat, user_id):
    """بررسی عضویت؛ خروجی: (is_member: bool|None, error_hint: str|None). None یعنی نتیجه قطعی نیست"""
    try:
        await client.get_chat_member(chat, user_id)
        return True, None
    except UserNotParticipant:
        return False, None
    except (ChatAdminRequired, ChannelPrivate) as e:
        return None, ("⚠️ حساب شما باید ادمین کانال/گروه عضویت اجباری باشد، وگرنه بررسی عضویت دیگران ممکن نیست "
                      f"(`{type(e).__name__}`)")
    except PeerIdInvalid as e:
        return None, f"⚠️ کانال/گروه شناسایی نشد؛ دوباره با `عضویت اجباری کانال ...` ثبت کنید (`{type(e).__name__}`)"
    except Exception as e:
        return None, f"⚠️ خطای نامشخص در بررسی عضویت: `{e}`"

async def _nf_forcejoin(client, message):
    if not (feat["forcejoin_on"] and feat["forcejoin_chat"]): return False
    if message.chat.type != enums.ChatType.PRIVATE or not message.from_user: return False
    u = message.from_user
    if u.is_bot or u.is_self or u.id == 777000 or getattr(u, "is_contact", False): return False
    now = time.time()
    if now - _fj_ok.get(u.id, 0) < 600: return False
    chat = feat["forcejoin_chat"]
    chat = int(chat) if re.fullmatch(r"-?\d+", chat) else chat
    is_member, err = await _check_forcejoin_membership(client, chat, u.id)
    if err:
        feat["forcejoin_last_error"] = err; fsave()
        if now - _fj_notified.get("_admin", 0) > 3600:   # به خود شما، حداکثر هر ساعت یک‌بار
            _fj_notified["_admin"] = now
            print("⚠️ عضویت اجباری پیوی غیرفعال عمل کرد:", err)
        return False   # نتیجه نامعلوم است؛ برای جلوگیری از قفل‌شدن اشتباهیِ پیوی، پیام را نمی‌بندیم
    if is_member:
        _fj_ok[u.id] = now
        return False
    if now - _fj_notified.get(u.id, 0) > 600:
        _fj_notified[u.id] = now
        try: await message.reply_text(f"📌 برای پیام دادن ابتدا در کانال {feat['forcejoin_chat']} عضو شوید و سپس دوباره پیام دهید.")
        except Exception: pass
    try: await message.delete()
    except Exception: pass
    return True

async def _nf_secretary(client, message):
    if not feat["secretary_on"] or afk_mode: return
    if message.chat.type != enums.ChatType.PRIVATE or not message.from_user: return
    u = message.from_user
    if u.is_bot or u.is_self or u.id == 777000: return
    now = time.time()
    if now - _sec_last.get(u.id, 0) < 6 * 3600: return
    _sec_last[u.id] = now
    try: await message.reply_text(feat["secretary_text"])
    except Exception: pass

async def _nf_friend(client, message):
    if not message.from_user or message.from_user.id not in feat["friends"]: return
    try: await client.send_reaction(message.chat.id, message.id, "❤️")
    except Exception: pass
    uid = message.from_user.id
    if message.text and random.random() < 0.2 and time.time() - _friend_last.get(uid, 0) > 300:
        _friend_last[uid] = time.time()
        try: await message.reply_text(random.choice(FRIEND_LINES))
        except Exception: pass

@app.on_message(~filters.me & filters.incoming, group=10)
async def new_features_incoming(client, message):
    try:
        await _nf_seen(client, message)
        if await _nf_filter(client, message): return
        if await _nf_guard(client, message): return
        if await _nf_forcejoin(client, message): return
        await _nf_secretary(client, message)
        await _nf_friend(client, message)
    except Exception as e:
        print("⚠️ خطا در قابلیت‌های جدید:", e)

@app.on_edited_message(~filters.me & filters.incoming, group=12)
async def new_features_edited(client, message):
    """ویرایش پیام برای دور زدن فیلتر"""
    try: await _nf_filter(client, message)
    except Exception: pass


# ==============================================================================
# ★ ساخت بنر پنل (عکس پروفایل + اسم) با Pillow ★
# ==============================================================================
PANEL_BANNER_FILE = f"panel_banner_{USER_ID}.png" if USER_ID else "panel_banner.png"      # خروجی؛ هلپر همین فایل را می‌خواند
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
        print("⚠️ ساخت بنر پنل ناموفق بود [r10]:", repr(e))
        print(traceback.format_exc())
    finally:
        _panel_banner_busy = False

# ==============================================================================
# ★ سیستم پنل — ارتباط زنده با هلپر (فایل مشترک) ★
# ==============================================================================
STATE_FILE = f"selfbot_state_{USER_ID}.json" if USER_ID else "selfbot_state.json"
ACTIONS_FILE = f"panel_actions_{USER_ID}.json" if USER_ID else "panel_actions.json"

def _atomic_write_json(path, data):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception: pass

_bio_cache = {"bio": "", "ts": 0.0}
last_action_ts = 0.0

async def build_panel_state():
    me = await app.get_me()
    bio = _bio_cache["bio"]
    if time.time() - _bio_cache["ts"] > 300:
        _bio_cache["ts"] = time.time()
        try: bio = _bio_cache["bio"] = (await app.get_chat(me.id)).bio or ""
        except Exception: pass
    return {
        "updated": int(time.time()),
        "last_action_ts": last_action_ts,
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
            "seen_on": feat["seen"], "filter_on": feat["filter_on"], "guard_on": feat["guard_on"],
            "guard_links": feat["guard_links"], "secretary_on": feat["secretary_on"],
            "filter_pv": feat["filter_pv"], "filter_groups": feat["filter_groups"], "guard_pv": feat["guard_pv"],
            "timed_save_on": feat["timed_save"],
            "forcejoin_on": feat["forcejoin_on"], "firstcomment_on": feat["firstcomment_on"],
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
    global afk_mode, signature_on, auto_delete_seconds, last_action_ts
    name = item.get("action", "")
    try:
        # امنیت: فقط دستوری که از طرف خود صاحب اکانت آمده اجرا شود
        me0 = await app.get_me()
        if item.get("user_id") != me0.id:
            return
        if name == "toggle_time":
            name = "time_off" if user_time_status.get(me0.id) else "time_on"
        if name == "toggle_online": always_online_enabled = not always_online_enabled
        elif name == "toggle_taglogger": tag_logger_on = not tag_logger_on
        elif name == "toggle_antilogin": anti_login_enabled = not anti_login_enabled
        elif name == "toggle_afk":
            afk_mode = not afk_mode; afk_notified.clear()
        elif name == "toggle_signature": signature_on = not signature_on
        elif name == "toggle_autodel": auto_delete_seconds = 0 if auto_delete_seconds else 30
        elif name in FEAT_TOGGLES:
            k = FEAT_TOGGLES[name]; feat[k] = not feat[k]; fsave()
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
            base = user_original_names.get(me.id) or _clean_original_name(me.first_name or "")
            fid = user_fonts.get(me.id, 1)
            try:
                await app.update_profile(first_name=f"{base} {fa_time_str(fid)}".strip()[:64])
            except Exception:
                pass
            else:
                # فقط در صورت موفقیت واقعی وضعیت را روشن ثبت کن، وگرنه دکمه دوباره
                # به کاربر «روشن» نشان می‌دهد در حالی که نام واقعاً تغییر نکرده
                user_time_status[me.id] = True
                user_original_names[me.id] = base
                _save_time_state()
        elif name == "time_off":
            me = await app.get_me()
            base = user_original_names.get(me.id, me.first_name or "")
            try:
                await app.update_profile(first_name=base)
            except Exception:
                pass
            user_time_status[me.id] = False
            _save_time_state()
    except Exception: pass
    try: last_action_ts = max(last_action_ts, float(item.get("ts", 0)))
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
        extra_sleep = 0
        try:
            me = await app.get_me()
            if user_time_status.get(me.id):
                fid = user_fonts.get(me.id, 1)
                orig = user_original_names.get(me.id) or _clean_original_name(me.first_name or "")
                try:
                    await app.update_profile(first_name=f"{orig} {fa_time_str(fid)}".strip()[:64])
                    if user_original_names.get(me.id) != orig:
                        user_original_names[me.id] = orig
                        _save_time_state()
                except FloodWait as e:
                    # به‌جای کوبیدن هر ۶۰ ثانیه به سقف Flood Wait، صبر می‌کنیم
                    extra_sleep = min(e.value, 300)
        except Exception:
            pass
        await asyncio.sleep(60 + extra_sleep)

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

async def tabchi_loop():
    while True:
        try:
            if tabchi["active"] and tabchi["codes"] and (time.time() - tabchi["last_run"]) >= tabchi["interval"]:
                await _tabchi_run_round(app)
        except Exception as e:
            print("⚠️ تبچی ناموفق بود:", repr(e))
        await asyncio.sleep(5)

if __name__ == "__main__":
    print("🧩 Persian Gulf Self | build panel-timed-r10 |", os.path.abspath(__file__))
    if USER_ID: print(f"✅ Persian Gulf Self برای کاربر {USER_ID} در حال اجرا... (نسخه شاهکار v7.0)")
    else: print("⚠️ سلف‌بات در حالت معمولی اجرا شد")
    if not USER_ID and not SESSION_STRING and not os.path.exists("self.session"):
        print("❌ بدون آرگومان و بدون فایل self.session اجرا شد؛ این پروسه لازم نیست (سلف‌بات را هلپر اجرا می‌کند). خروج.")
        sys.exit(0)
    loop = asyncio.get_event_loop()
    app.start()
    print("🔗 سیستم پنل Persian Gulf Self فعال شد")
    print(f"🤖 Gemini: {'کلید تنظیم شده' if _ai_key() else 'کلید ندارد (جمنای کلید XXXX)'} | ffmpeg: {'OK' if _ff() else 'نیست'}")
    try:
        loop.run_until_complete(asyncio.gather(
            panel_state_loop(), panel_actions_loop(),
            online_loop(), time_loop(), banner_loop(), tabchi_loop()))
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()
