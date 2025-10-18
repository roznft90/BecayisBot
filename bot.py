from flask import Flask
import threading

# Flask sunucusu
app = Flask(__name__)

@app.route("/")
def home():
    return "BecayisBot aktif!"

# Bot polling thread
def run_bot():
    import telebot
    from datetime import datetime, timedelta
    import sqlite3

    TOKEN = "8036133277:AAH5Te359TQjFITqGMrUKUiX7M5bw_S0ub4"
    bot = telebot.TeleBot(TOKEN)

    # Veritabanı ayarları
    conn = sqlite3.connect('ilanlar.db', check_same_thread=False)
    c = conn.cursor()
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

    # Eski ilanları temizleme
    def temizle_eski_ilanlar():
        six_months_ago = datetime.now() - timedelta(days=180)
        c.execute("DELETE FROM ilanlar WHERE tarih < ?", (six_months_ago,))
        conn.commit()

    # /ilan komutu
    @bot.message_handler(commands=['ilan'])
    def ilan_handler(message):
        temizle_eski_ilanlar()
        try:
            text = message.text.replace('/ilan ', '')
            if ' verilir - ' not in text or ' alınır' not in text:
                bot.reply_to(message, "Doğru format: /ilan Bursa Merkez verilir - Sinop Gerze alınır")
                return

            vermek = text.split(' verilir - ')[0].strip()
            almak = text.split(' verilir - ')[1].replace(' alınır','').strip()
            kullanici = message.from_user.username
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

    print("BecayisBot aktif!...")
    bot.polling(none_stop=True)

# Botu ayrı thread olarak çalıştır
threading.Thread(target=run_bot).start()

# Flask sunucusunu başlat
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
