import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import cursor, conn

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMINS = list(map(int, os.getenv("ADMINS").split(",")))


def is_admin(user_id):
    return user_id in ADMINS


async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yetkin yok.")
        return

    try:
        # İsim ve soyisim birleştir (son argüman tarih)
        date = context.args[-1]
        name = " ".join(context.args[:-1])

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
            "Kullanım: /ekle İsim Soyisim YYYY-MM-DD"
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


async def check_birthdays(app):
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m-%d")

    cursor.execute("SELECT name, date, chat_id FROM birthdays")
    for name, date, chat_id in cursor.fetchall():
        if datetime.strptime(date, "%Y-%m-%d").strftime("%m-%d") == tomorrow:
            await app.bot.send_message(
                chat_id,
                f"🎉 Yarın {name}'in doğum günü! 🎂"
            )


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("liste", liste))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(check_birthdays(app)), "cron", hour=9)
    scheduler.start()

    print("🤖 Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()