import os
import asyncio
import csv
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import execute_query, fetch_all, fetch_one, conn

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMINS = list(map(int, os.getenv("ADMINS").split(",")))
#sa

def is_admin(user_id):
    return user_id in ADMINS


async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yetkin yok.")
        return

    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "Kullanım: /ekle İsim Soyisim YYYY-MM-DD"
            )
            return
        
        # İsim ve soyisim birleştir (son argüman tarih)
        date = context.args[-1]
        name = " ".join(context.args[:-1])

        # Tarih formatı kontrolü
        datetime.strptime(date, "%Y-%m-%d")

        # Veritabanına ekle
        execute_query(
            "INSERT INTO birthdays (name, date, chat_id) VALUES (?, ?, ?)",
            (name, date, update.effective_chat.id)
        )

        await update.message.reply_text(
            f"✅ {name} için doğum günü eklendi: {date}"
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Geçersiz tarih formatı! Kullanım: /ekle İsim Soyisim YYYY-MM-DD"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Hata oluştu: {str(e)}\nKullanım: /ekle İsim Soyisim YYYY-MM-DD"
        )


async def toplu_ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """CSV dosyası yüklemek için talimat gönder"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yetkin yok.")
        return
    
    text = """
📋 **Toplu Ekleme**

CSV veya TXT dosyası yükleyin.

**Format:**
```
isim,tarih
Ahmet Yılmaz,2000-05-15
Ayşe Demir,1998-08-20
Mehmet Kaya,1995-03-10
```

📝 **Excel'den nasıl oluşturulur:**
1. Excel'de liste hazırlayın
2. A sütunu: İsim Soyisim
3. B sütunu: Tarih (YYYY-MM-DD)
4. İlk satır: isim,tarih
5. Farklı Kaydet → CSV (virgülle ayrılmış)

📤 Dosyayı buraya yükleyin!
    """
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yüklenen CSV dosyasını işle"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yetkin yok.")
        return
    
    # Dosya türü kontrolü
    file_name = update.message.document.file_name
    if not (file_name.endswith('.csv') or file_name.endswith('.txt')):
        await update.message.reply_text("❌ Sadece .csv veya .txt dosyası yükleyin!")
        return
    
    await update.message.reply_text("⏳ Dosya işleniyor...")
    
    file_path = None
    try:
        # Dosyayı indir
        file = await context.bot.get_file(update.message.document.file_id)
        file_path = f"temp_{file_name}"
        await file.download_to_drive(file_path)
        
        # CSV'yi oku ve veritabanına ekle
        added = 0
        errors = []
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Başlık satırını atla
            
            for i, row in enumerate(reader, start=2):
                try:
                    if len(row) < 2:
                        errors.append(f"Satır {i}: Eksik veri")
                        continue
                    
                    name = row[0].strip()
                    date = row[1].strip()
                    
                    # Tarih formatı kontrolü
                    datetime.strptime(date, "%Y-%m-%d")
                    
                    # Veritabanına ekle
                    execute_query(
                        "INSERT INTO birthdays (name, date, chat_id) VALUES (?, ?, ?)",
                        (name, date, update.effective_chat.id)
                    )
                    added += 1
                    
                except ValueError:
                    errors.append(f"Satır {i}: Hatalı tarih formatı ({date})")
                except Exception as e:
                    errors.append(f"Satır {i}: {str(e)}")
        
        # Geçici dosyayı sil
        os.remove(file_path)
        
        # Sonuç mesajı
        result = f"✅ **{added}** kişi başarıyla eklendi!\n\n"
        
        if errors:
            result += "⚠️ **Hatalar:**\n"
            for error in errors[:10]:  # İlk 10 hatayı göster
                result += f"• {error}\n"
            if len(errors) > 10:
                result += f"\n... ve {len(errors) - 10} hata daha"
        
        await update.message.reply_text(result, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Dosya işlenirken hata oluştu:\n{str(e)}")
        # Hata durumunda dosyayı temizle
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = fetch_all(
        "SELECT name, date FROM birthdays WHERE chat_id=?",
        (update.effective_chat.id,)
    )

    if not rows:
        await update.message.reply_text("📭 Kayıt yok.")
        return

    text = "🎂 Doğum Günleri:\n\n"
    for name, date in rows:
        text += f"• {name} → {date}\n"

    await update.message.reply_text(text)


async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Yetkin yok.")
        return

    try:
        if not context.args:
            await update.message.reply_text("Kullanım: /sil İsim Soyisim")
            return
            
        name = " ".join(context.args)

        cur = execute_query(
            "DELETE FROM birthdays WHERE name=? AND chat_id=?",
            (name, update.effective_chat.id)
        )

        if cur.rowcount > 0:
            await update.message.reply_text(f"✅ {name} silindi.")
        else:
            await update.message.reply_text(f"❌ {name} bulunamadı.")
    except Exception as e:
        await update.message.reply_text(f"❌ Hata: {str(e)}\nKullanım: /sil İsim Soyisim")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🎂 **Doğum Günü Hatırlatıcı Bot**

📋 **Komutlar:**

🔹 `/ekle İsim Soyisim YYYY-MM-DD`
   Yeni doğum günü ekle

🔹 `/toplu_ekle`
   CSV dosyası ile toplu ekleme

🔹 `/liste`
   Tüm doğum günlerini listele

🔹 `/sil İsim Soyisim`
   Doğum gününü sil

🔹 `/stats`
   İstatistikleri göster

🔹 `/help`
   Bu yardım menüsü

⏰ **Otomatik Hatırlatma:**
Her gün saat 09:00'da, yarın doğum günü olanları hatırlatırım! 🎉
    """
    await update.message.reply_text(text, parse_mode="Markdown")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = fetch_all(
        "SELECT name, date FROM birthdays WHERE chat_id=?",
        (update.effective_chat.id,)
    )

    if not rows:
        await update.message.reply_text("📭 Henüz kayıt yok.")
        return

    total = len(rows)
    
    # Bu ay doğum günü olanlar
    current_month = datetime.now().strftime("%m")
    this_month = sum(1 for _, date in rows if datetime.strptime(date, "%Y-%m-%d").strftime("%m") == current_month)
    
    # Önümüzdeki 30 gün içinde doğum günü olanlar
    upcoming = 0
    today = datetime.now()
    for _, date in rows:
        bd = datetime.strptime(date, "%Y-%m-%d")
        # Bu yılki doğum günü
        bd_this_year = bd.replace(year=today.year)
        if bd_this_year < today:
            bd_this_year = bd.replace(year=today.year + 1)
        
        days_until = (bd_this_year - today).days
        if 0 <= days_until <= 30:
            upcoming += 1

    text = f"""
📊 **İstatistikler**

👥 Toplam kayıt: **{total}** kişi
📅 Bu ay: **{this_month}** kişi
🎯 Önümüzdeki 30 gün: **{upcoming}** kişi
    """
    await update.message.reply_text(text, parse_mode="Markdown")


async def check_birthdays(app):
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m-%d")

    rows = fetch_all("SELECT name, date, chat_id FROM birthdays")
    for name, date, chat_id in rows:
        if datetime.strptime(date, "%Y-%m-%d").strftime("%m-%d") == tomorrow:
            await app.bot.send_message(
                chat_id,
                f"🎉 Yarın {name}'in doğum günü! 🎂"
            )


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("toplu_ekle", toplu_ekle))
    app.add_handler(CommandHandler("liste", liste))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("stats", stats))
    
    # CSV dosyası yükleme handler'ı
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: check_birthdays(app),
        "cron",
        hour=9,
        minute=0,
        timezone="Europe/Istanbul"
    )
    scheduler.start()

    print("🤖 Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()