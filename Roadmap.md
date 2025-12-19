

⸻

🟢 PROJE: TELEGRAM DOĞUM GÜNÜ HATIRLATICI BOTU

Python + Railway + Grup Botu

⸻

0️⃣ BAŞLAMADAN ÖNCE (ÖNEMLİ)

Şunlara ihtiyacın var:
	•	✅ Telegram hesabı
	•	✅ GitHub hesabı
	•	✅ Bilgisayar (Windows / Mac / Linux)
	•	✅ Python 3.10+ kurulu

👉 Python kontrol:

python --version

3.x görüyorsan tamam.

⸻

1️⃣ TELEGRAM BOTUNU OLUŞTUR (KESİNLİKLE ATLAMA)

1.1 BotFather’a gir

Telegram → arama → @BotFather

1.2 Yeni bot oluştur

Mesaj olarak:

/newbot

1.3 Bot adı soracak

Örnek:

Topluluk Dogum Gunu Botu

1.4 Username soracak

⚠️ bot ile bitmek zorunda

topluluk_dg_bot

1.5 TOKEN gelecek

Şuna benzer:

1234567890:AAHsjshdJSHDjsjsjsh

🔴 BUNU BİR YERE KOPYALA – KAYBOLURSA BOT ÖLÜR

⸻

2️⃣ TELEGRAM USER ID’LERİ AL (ADMINS)

2.1 Telegram’da @userinfobot aç
	•	Kendine yaz → ID’ni al
	•	Başkan yardımcısı da aynısını yapsın

Örnek:

123456789
987654321

Bunlar ADMIN olacak.

⸻

3️⃣ PROJE KLASÖRÜ OLUŞTUR

3.1 Masaüstünde klasör

birthday_bot

3.2 İçine gir

cd birthday_bot


⸻

4️⃣ PYTHON SANAL ORTAM (ÇOK ÖNEMLİ)

python -m venv venv

Aktif et

Windows

venv\Scripts\activate

Mac / Linux

source venv/bin/activate

Terminal başında (venv) görüyorsan doğru.

⸻

5️⃣ GEREKLİ KÜTÜPHANELERİ KUR

pip install python-telegram-bot==20.7 apscheduler python-dotenv


⸻

6️⃣ DOSYA YAPISI (AYNI OLMALI)

Klasörün birebir böyle olacak:

birthday_bot/
│
├── main.py
├── db.py
├── requirements.txt
├── .env
└── .gitignore


⸻

7️⃣ DATABASE DOSYASI (db.py)

📄 db.py oluştur ve AYNEN yapıştır:

import sqlite3

conn = sqlite3.connect("birthdays.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS birthdays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    chat_id INTEGER NOT NULL
)
""")

conn.commit()


⸻

8️⃣ ENV DOSYASI (.env)

📄 .env oluştur:

TOKEN=BURAYA_BOT_TOKEN
ADMINS=123456789,987654321

⚠️
	•	TOKEN → BotFather’dan aldığın
	•	ADMINS → User ID’ler

⸻

9️⃣ ANA BOT KODU (main.py)

📄 main.py oluştur ve HİÇ DEĞİŞTİRMEDEN yapıştır:

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

from db import cursor, conn

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMINS = list(map(int, os.getenv("ADMINS").split(",")))

app = ApplicationBuilder().token(TOKEN).build()


def is_admin(user_id):
    return user_id in ADMINS


async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yetkin yok.")
        return

    try:
        name = context.args[0]
        date = context.args[1]

        datetime.strptime(date, "%Y-%m-%d")

        cursor.execute(
            "INSERT INTO birthdays (name, date, chat_id) VALUES (?, ?, ?)",
            (name, date, update.effective_chat.id)
        )
        conn.commit()

        await update.message.reply_text(
            f"✅ {name} için doğum günü eklendi: {date}"
        )
    except:
        await update.message.reply_text(
            "Kullanım: /ekle İsim YYYY-MM-DD"
        )


async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute(
        "SELECT name, date FROM birthdays WHERE chat_id=?",
        (update.effective_chat.id,)
    )
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("📭 Kayıt yok.")
        return

    text = "🎂 Doğum Günleri:\n\n"
    for name, date in rows:
        text += f"• {name} → {date}\n"

    await update.message.reply_text(text)


def check_birthdays():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m-%d")

    cursor.execute("SELECT name, date, chat_id FROM birthdays")
    for name, date, chat_id in cursor.fetchall():
        if datetime.strptime(date, "%Y-%m-%d").strftime("%m-%d") == tomorrow:
            app.bot.send_message(
                chat_id,
                f"🎉 Yarın {name}'in doğum günü! 🎂"
            )


scheduler = BackgroundScheduler()
scheduler.add_job(check_birthdays, "cron", hour=9)
scheduler.start()


app.add_handler(CommandHandler("ekle", ekle))
app.add_handler(CommandHandler("liste", liste))

print("🤖 Bot çalışıyor...")
app.run_polling()


⸻

🔟 requirements.txt

pip freeze > requirements.txt


⸻

1️⃣1️⃣ .gitignore

📄 .gitignore

.env
venv
birthdays.db


⸻

1️⃣2️⃣ LOKAL TEST (EN KRİTİK ADIM)

python main.py

Terminalde:

🤖 Bot çalışıyor...

Telegram’da botla özel sohbet:

/ekle Ahmet 2000-12-20
/liste

ÇALIŞIYORSA → %70 bitti 🔥

⸻

1️⃣3️⃣ GITHUB’A YÜKLE

git init
git add .
git commit -m "Telegram birthday reminder bot"
git branch -M main
git remote add origin REPO_URL
git push -u origin main


⸻

1️⃣4️⃣ RAILWAY DEPLOY (SON ADIM)

14.1 railway.app → GitHub ile giriş

14.2 New Project → Deploy from GitHub Repo

14.3 Repo’yu seç

⸻

14.4 ENV EKLE (ÇOK ÖNEMLİ)

Railway → Variables

TOKEN = bot token
ADMINS = 123456789,987654321


⸻

14.5 Start Command

Railway otomatik başlatır
Yoksa:

python main.py


⸻

1️⃣5️⃣ BOTU GRUBA EKLE
	1.	Telegram grubuna botu ekle
	2.	Yönetici yap
	3.	Mesaj atma izni ver

⸻

✅ PROJE BİTTİ

Artık:
	•	/ekle
	•	/liste
	•	Her gün 09:00’da
	•	Doğum gününden 1 gün önce mesaj

⸻

🎓 BU NOKTADA SEN ŞUNU BAŞARDIN:
	•	Python Telegram bot
	•	Admin yetkilendirme
	•	Scheduler
	•	Railway deploy
	•	Gerçek çalışan sistem

