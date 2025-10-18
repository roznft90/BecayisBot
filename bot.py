import telebot
import sqlite3
from datetime import datetime, timedelta

# Bot tokeni buraya yapıştır
TOKEN = "8036133277:AAH5Te359TQjFITqGMrUKUiX7M5bw_S0ub4"
bot = telebot.TeleBot(TOKEN)

# Veritabanı bağlantısı
conn = sqlite3.connect('ilanlar.db', check_same_thread=False)
c = conn.cursor()

# Tablo oluştur
c.execute('''
CREATE TABLE IF NOT EXISTS ilanlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici TEXT,
    vermek TEXT,
    almak TEXT,
    tarih TIMESTAMP
)
''')
conn.commit()

# Eski ilanları temizleme (6 ay)
def temizle_eski_ilanlar():
    six_months_ago = datetime.now() - timedelta(days=180)
    c.execute("DELETE FROM ilanlar WHERE tarih < ?", (six_months_ago,))
    conn.commit()

# /ilan komutu
@bot.message_handler(commands=['ilan'])
def ilan_handler(message):
    temizle_eski_ilanlar()
    try:
        # Mesaj formatını al
        text = message.text.replace('/ilan ', '')
        if ' verilir - ' not in text or ' alınır' not in text:
            bot.reply_to(message, "Lütfen doğru format kullan: /ilan Bursa Merkez verilir - Sinop Gerze alınır")
            return

        vermek = text.split(' verilir - ')[0].strip()
        almak = text.split(' verilir - ')[1].replace(' alınır','').strip()
        kullanici = message.from_user.username

        # İlanı kaydet
        tarih = datetime.now()
        c.execute("INSERT INTO ilanlar (kullanici, vermek, almak, tarih) VALUES (?, ?, ?, ?)",
                  (kullanici, vermek, almak, tarih))
        conn.commit()

        # Eşleşme kontrolü
        c.execute("SELECT kullanici FROM ilanlar WHERE vermek=? AND almak=? AND kullanici!=?", (almak, vermek, kullanici))
        eslesenler = c.fetchall()

        if eslesenler:
            for e in eslesenler:
                mesaj = f"🎉 Eşleşme bulundu: @{kullanici} ↔ @{e[0]}"
                bot.send_message(message.chat.id, mesaj)
        else:
            bot.reply_to(message, "İlan kaydedildi, eşleşme bulunamadı. 🕒")
    except Exception as ex:
        bot.reply_to(message, f"Hata: {ex}")

# Botu çalıştır
print("BecayisBot aktif!...")
bot.polling(none_stop=True)

