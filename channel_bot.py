# -*- coding: utf-8 -*-
"""
ربات پست خودکار کانال
------------------------
هر روز شش پست می‌فرسته، هر کدوم توی ساعت خودش:
  1) وان پیس تایم
  2) جهان انیمه
  3) دنیای فیلم و سریال
  4) چی ببینیم (فعلاً خالیه، بعداً با TMDB و AniList پر می‌شه)
  5) کوییز
  6) نظرسنجی

بخش هوش مصنوعی آماده‌ست ولی تا وقتی USE_AI = False باشه کار نمی‌کنه.
"""

import html
import random
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

# =====================================================================
# تنظیمات (فقط این بخش رو عوض کن)
# =====================================================================

TOKEN = "8802246679:AAFGshfJ2NqGvpJ4k_KuuRjm_zZAR6Ty6Iw"
CHANNEL = "@nakama_iran"                      # یوزرنیم کانال با @
CHANNEL_NAME = "Nakama_Iran"           # اسمی که توی «Join us» دیده می‌شه
CHANNEL_LINK = "https://t.me/nakama_iran"     # لینک کانال (بدون @). کانال خصوصی: لینک دعوت
TIMEZONE = "Asia/Tehran"

# اگه True باشه، همه پست‌ها همین الان یک بار فرستاده می‌شن (برای تست)
TEST = False

# ---- بخش هوش مصنوعی (فعلاً خاموش) ----
USE_AI = False
GEMINI_KEY = os.environ.get("GEMINI_KEY", "")  # کلید رایگان از Google AI Studio (متغیر GEMINI_KEY توی Render)
GEMINI_MODEL = ""        # اسم مدل رو از لیست AI Studio کپی کن (اسم‌ها زود عوض می‌شن)
AI_DRAFTS_PER_DAY = 10   # هر روز چند فکت پیش‌نویس بسازه
AI_DRAFT_TIME = "03:00"  # ساعت ساخت پیش‌نویس‌ها

# ساعت ارسال هر پست
TIMES = {
    "onepiece": "10:00",
    "anime": "12:00",
    "movies": "15:00",
    "watch": "18:00",
    "quiz": "20:00",
    "poll": "22:00",
}

API = f"https://api.telegram.org/bot{TOKEN}"


# =====================================================================
# ابزارهای کمکی
# =====================================================================

def e(text):
    """متن رو برای حالت HTML امن می‌کنه (جلوی خراب شدن پست با < و & رو می‌گیره)"""
    return html.escape(text)


def tg(method, **payload):
    """یک دستور به تلگرام می‌فرسته و اگه خطا داد، توضیحش رو چاپ می‌کنه"""
    try:
        r = requests.post(f"{API}/{method}", json=payload, timeout=30)
        data = r.json()
        if not data.get("ok"):
            print(f"[خطای تلگرام] {method}: {data.get('description')}")
        return data
    except Exception as ex:
        print(f"[خطای اینترنت] {method}: {ex}")
        return None


def send_text(text):
    return tg(
        "sendMessage",
        chat_id=CHANNEL,
        text=text,
        parse_mode="HTML",
        link_preview_options={"is_disabled": True},
    )


def send_photo(url, caption=""):
    """فرستادن عکس (برای پست چی ببینیم). توضیح زیر عکس حداکثر ۱۰۲۴ حرف"""
    return tg(
        "sendPhoto",
        chat_id=CHANNEL,
        photo=url,
        caption=caption[:1024],
        parse_mode="HTML",
    )


def footer(tag):
    """پایین هر پست: Join us + اسم کانال با لینک + هشتگ"""
    return (
        "\n\n➖➖➖➖➖➖\n"
        f'📢 Join us: <a href="{CHANNEL_LINK}">{e(CHANNEL_NAME)}</a>\n\n'
        f"{tag}"
    )


def read_text_file(name):
    try:
        with open(name, encoding="utf-8") as f:
            return f.read().replace("\r\n", "\n")
    except FileNotFoundError:
        raise Exception(f"فایل {name} پیدا نشد. کنار channel_bot.py بذارش.")


def pick_blocks(name, n):
    """فایل‌های فکت و SBS: هر فکت بین { و } نوشته می‌شه و می‌تونه چند خط باشه.
    اگه توی فایل هیچ { } نباشه، از خط خالی بین فکت‌ها برای جدا کردن استفاده می‌کنه."""
    content = read_text_file(name)

    if "{" in content or "}" in content:
        if content.count("{") != content.count("}"):
            print(f"[هشدار] توی {name} تعداد {{ و }} برابر نیست. یکی‌شون جا افتاده.")
        blocks = [b.strip() for b in re.findall(r"\{(.*?)\}", content, flags=re.DOTALL)]
        blocks = [b for b in blocks if b]
    else:
        blocks = [b.strip() for b in re.split(r"\n\s*\n", content) if b.strip()]

    if not blocks:
        raise Exception(f"فایل {name} خالیه.")
    return random.sample(blocks, min(n, len(blocks)))


def pick_line(name):
    """فایل‌های کوییز و نظرسنجی: هر سؤال توی یک خط"""
    lines = [l.strip() for l in read_text_file(name).split("\n") if l.strip()]
    if not lines:
        raise Exception(f"فایل {name} خالیه.")
    return random.choice(lines)


# =====================================================================
# پست‌ها
# =====================================================================

def post_onepiece():
    sbs = pick_blocks("onepiece_sbs.txt", 1)[0]
    facts = pick_blocks("onepiece_facts.txt", 2)
    text = "🔴 <b>وان پیس تایم</b> 🏴‍☠️\n\n"
    text += "📖 <b>SBS</b>\n🏴‍☠️ " + e(sbs) + "\n\n"
    text += "💡 <b>فکت‌ها</b>\n"
    text += "\n\n".join("🏴‍☠️ " + e(f) for f in facts)
    send_text(text + footer("#وان_پیس #انیمه #مانگا"))


def post_anime():
    facts = pick_blocks("anime_facts.txt", 3)
    text = "🔴 <b>جهان انیمه</b> 🌍\n\n"
    text += "\n\n".join("🌸 " + e(f) for f in facts)
    send_text(text + footer("#جهان_انیمه #انیمه #فکت"))


def post_movies():
    h = pick_blocks("hollywood_facts.txt", 1)[0]
    k = pick_blocks("kdrama_facts.txt", 1)[0]
    text = "🔴 <b>دنیای فیلم و سریال</b> 🎬\n\n"
    text += "🇺🇸 <b>هالیوود</b>\n🍿 " + e(h) + "\n\n"
    text += "🇰🇷 <b>کی‌درامای</b>\n💖 " + e(k)
    send_text(text + footer("#دنیای_فیلم_و_سریال #هالیوود #کیدراما"))


def post_watch():
    # بعداً با TMDB و AniList پر می‌شه. فعلاً چیزی نمی‌فرسته.
    pass


def post_quiz():
    # قالب هر خط: سؤال | گزینه ۱ | گزینه ۲ | ... | شماره جواب درست (از ۱ شروع می‌شه)
    parts = [p.strip() for p in pick_line("quiz.txt").split("|")]
    if len(parts) < 4:
        raise Exception("یک خط از quiz.txt ناقصه: باید سؤال، حداقل دو گزینه و شماره جواب داشته باشه.")
    question, options, correct = parts[0], parts[1:-1], int(parts[-1]) - 1
    if not (0 <= correct < len(options)):
        raise Exception(f"شماره جواب درست توی این سؤال اشتباهه: {question}")
    send_text("🔴 <b>کوییز امروز</b> 🧠" + footer("#کوییز #انیمه #فیلم_و_سریال"))
    tg(
        "sendPoll",
        chat_id=CHANNEL,
        question=question[:300],
        options=[o[:100] for o in options[:10]],
        type="quiz",
        correct_option_id=correct,
        is_anonymous=True,
    )


def post_poll():
    # قالب هر خط: سؤال | گزینه ۱ | گزینه ۲ | ...
    parts = [p.strip() for p in pick_line("poll.txt").split("|")]
    if len(parts) < 3:
        raise Exception("یک خط از poll.txt ناقصه: باید سؤال و حداقل دو گزینه داشته باشه.")
    send_text("🔴 <b>نظرسنجی امروز</b> 📊" + footer("#نظرسنجی #انیمه #فیلم_و_سریال"))
    tg(
        "sendPoll",
        chat_id=CHANNEL,
        question=parts[0][:300],
        options=[o[:100] for o in parts[1:11]],
        is_anonymous=True,
    )


# =====================================================================
# بخش هوش مصنوعی (آماده ولی فقط وقتی USE_AI = True باشه استفاده می‌شه)
# فکت‌ها مستقیم توی کانال نمی‌رن. توی drafts.txt ذخیره می‌شن تا خودت چک کنی.
# =====================================================================

def ask_ai(prompt):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    )
    r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        raise Exception(f"جواب Gemini درست نبود: {str(data)[:300]}")


def get_wiki_text(title):
    r = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query", "prop": "extracts", "explaintext": 1,
            "titles": title, "format": "json", "redirects": 1,
        },
        headers={"User-Agent": "ChannelBot/1.0"},
        timeout=30,
    )
    pages = r.json()["query"]["pages"]
    return next(iter(pages.values())).get("extract", "")


def make_fact_draft():
    """یک اسم از topics.txt برمی‌داره، متنش رو از ویکی‌پدیا می‌گیره،
    از Gemini می‌خواد فقط از روی همون متن فکت بنویسه و توی drafts.txt ذخیره‌ش می‌کنه"""
    lines = [l.strip() for l in read_text_file("topics.txt").split("\n") if l.strip()]
    title = random.choice(lines)
    text = get_wiki_text(title)[:6000]
    if not text:
        return
    prompt = (
        "فقط و فقط از روی متن زیر، یک فکت جالب و کوتاه (دو جمله) به فارسی ساده بنویس. "
        "هیچ اطلاعاتی که توی متن نیست اضافه نکن. اگه فکت جالبی نبود فقط بنویس NONE.\n\n"
        + text
    )
    fact = ask_ai(prompt).strip()
    if fact and fact != "NONE":
        link = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
        with open("drafts.txt", "a", encoding="utf-8") as f:
            f.write(f"{fact}\nمنبع: {link}\n\n")


def job_make_drafts():
    for _ in range(AI_DRAFTS_PER_DAY):
        try:
            make_fact_draft()
        except Exception as ex:
            print("[خطای هوش مصنوعی]", ex)
        time.sleep(8)  # فاصله بین درخواست‌ها برای اینکه سقف رایگان پر نشه


# =====================================================================
# زمان‌بندی
# =====================================================================

def build_schedule():
    schedule = {
        TIMES["onepiece"]: post_onepiece,
        TIMES["anime"]: post_anime,
        TIMES["movies"]: post_movies,
        TIMES["watch"]: post_watch,
        TIMES["quiz"]: post_quiz,
        TIMES["poll"]: post_poll,
    }
    if USE_AI:
        schedule[AI_DRAFT_TIME] = job_make_drafts
    return schedule


# =====================================================================
# سرور کوچک (فقط برای اینکه Render و UptimeRobot بتونن سرویس رو زنده نگه دارن)
# =====================================================================

class PingHandler(BaseHTTPRequestHandler):
    def _ok(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        self._ok()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self._ok()

    def log_message(self, *args):
        pass  # لاگ‌های اضافه چاپ نشه


def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), PingHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"سرور کوچک روی پورت {port} روشن شد.", flush=True)


def main():
    schedule = build_schedule()

    if TEST:
        for func in schedule.values():
            try:
                func()
            except Exception as ex:
                print(f"[خطا] {func.__name__}: {ex}")
        print("تست تموم شد.")
        return

    start_web_server()
    print("ربات روشن شد.", flush=True)
    done = set()
    while True:
        now = datetime.now(ZoneInfo(TIMEZONE))
        today = now.strftime("%Y-%m-%d")
        key = now.strftime("%H:%M")
        done = {d for d in done if d[0] == today}  # فقط امروز رو نگه می‌داره
        if key in schedule and (today, key) not in done:
            done.add((today, key))
            try:
                schedule[key]()
            except Exception as ex:
                print(f"[خطا] {schedule[key].__name__}: {ex}")
        time.sleep(20)


if __name__ == "__main__":
    main()

