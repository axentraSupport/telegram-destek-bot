import telebot
import sqlite3
import datetime
import hashlib
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread
import os

# --- [ 🌐 7/24 AKTİF TUTMA SİSTEMİ ] ---
app = Flask('')
@app.route('/')
def home(): return "<h1>AxentraStore Key Sistemi Aktif!</h1>"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive():
    t = Thread(target=run).start()

# --- [ 👑 KRALİYET AYARLARI ] ---
TOKEN = "8723920846:AAEwjNsklKizeN1DY2alFIwo8k5oz7dJ1Hg" 
ADMIN_ID = 8561815348 
MARKA_ADI = "AxentraStore"

IBAN_ADRESI = "TR10 0006 2000 9100 0006 9697 09"
AD_SOYAD = "Garanti Ödeme ve Elektronik Para Hizmetleri A.Ş."
ZORUNLU_ACIKLAMA = "TAMİ7987919953449959"

DB_NAME = "axentra_final.db"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- [ 🗄️ VERİTABANI MOTORU ] ---
def db_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if fetch: return c.fetchall()
        conn.commit()

# Tabloları Güncelleme (Key sistemi için yeni tablo)
db_query("""CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, daily_claim TEXT DEFAULT '0')""")
db_query("CREATE TABLE IF NOT EXISTS keys (key_code TEXT PRIMARY KEY, status TEXT DEFAULT 'active', owner_id INTEGER DEFAULT 0)")
db_query("CREATE TABLE IF NOT EXISTS vault (dna_hash TEXT PRIMARY KEY)")

# --- [ 📱 ANA MENÜ ] ---
def main_menu(uid):
    u = db_query("SELECT balance FROM users WHERE id=?", (uid,), fetch=True)[0]
    markup = InlineKeyboardMarkup(row_width=2)
    
    markup.add(InlineKeyboardButton(f"🚀 SATIN AL (350₺)", callback_data="buy_now"))
    markup.add(InlineKeyboardButton("🌟 KEY İLE VIP KANAL AL", callback_data="use_key"))
    markup.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="deposit"), 
               InlineKeyboardButton("🎰 SLOT MAKİNESİ", callback_data="slot"))
    markup.add(InlineKeyboardButton("🎁 ŞANSLI KASA", callback_data="box"),
               InlineKeyboardButton("🏆 LİDERLER", callback_data="top"))
    markup.add(InlineKeyboardButton("🛠️ DESTEK", callback_data="ticket"),
               InlineKeyboardButton("📆 GÜNLÜK ÖDÜL", callback_data="daily"))
    
    if uid == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 ADMİN PANELİ", callback_data="admin_panel"))

    markup.add(InlineKeyboardButton(f"👤 Bakiyen: {u[0]}₺", callback_data="stats"))
    return markup

# --- [ ⚙️ TÜM İŞLEMLER ] ---
@bot.callback_query_handler(func=lambda call: True)
def callback_logic(call):
    uid, mid = call.message.chat.id, call.message.message_id
    u_data = db_query("SELECT balance, daily_claim FROM users WHERE id=?", (uid,), fetch=True)[0]

    if call.data == "home":
        bot.edit_message_text(f"🏠 **{MARKA_ADI} Ana Menü**", uid, mid, reply_markup=main_menu(uid))

    elif call.data == "buy_now":
        if u_data[0] >= 350:
            # Rastgele Key Üret
            new_key = f"AXN-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
            db_query("INSERT INTO keys (key_code, status, owner_id) VALUES (?, 'active', ?)", (new_key, uid))
            db_query("UPDATE users SET balance = balance - 350 WHERE id=?", (uid,))
            
            bot.edit_message_text(f"✅ **SATIN ALIM BAŞARILI!**\n\n🔑 Keyiniz: `{new_key}`\n\nBu Key'i 'Key ile VIP Kanal Al' menüsünde kullanabilirsiniz.", uid, mid, 
                                 reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))
        else:
            bot.answer_callback_query(call.id, "❌ Bakiyen yetersiz kanka! (350₺ lazım)", show_alert=True)

    elif call.data == "use_key":
        msg = bot.send_message(uid, "🔑 Lütfen elinizdeki **Key kodunu** buraya yazın:")
        bot.register_next_step_handler(msg, process_key_activation)

    elif call.data == "deposit":
        msg = (f"💰 **BAKİYE YÜKLEME**\n\n🏦 **IBAN:** `{IBAN_ADRESI}`\n👤 **Alıcı:** `{AD_SOYAD}`\n"
               f"📝 **Açıklama:** `{ZORUNLU_ACIKLAMA} {uid}`\n\n📸 Ödeme sonrası **DEKONT** gönderin.")
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    # ... (Diğer Slot, Kasa ve Admin callback'leri buraya gelecek - Alan daralmasın diye en önemli kısımları tutuyorum)

# --- [ 🔑 KEY DOĞRULAMA SİSTEMİ ] ---
def process_key_activation(message):
    uid = message.chat.id
    input_key = message.text.strip()
    
    # Key veritabanında var mı ve aktif mi kontrol et
    key_check = db_query("SELECT status FROM keys WHERE key_code=?", (input_key,), fetch=True)
    
    if key_check and key_check[0][0] == 'active':
        # Key'i kullanıldı yap
        db_query("UPDATE keys SET status='used', owner_id=? WHERE key_code=?", (uid, input_key))
        
        bot.send_message(uid, "🎊 **TEBRİKLER!**\nKey başarıyla doğrulandı. VIP Kanal linkiniz hazırlanıyor...\n\n🔗 [VIP KANALINA GİRİŞ YAP](https://t.me/axentravip)", 
                         reply_markup=main_menu(uid))
        
        # Yönetime haber ver
        bot.send_message(ADMIN_ID, f"🔔 **BİLGİ:** {uid} ID'li kullanıcı bir Key kullandı ve VIP oldu!")
    else:
        bot.send_message(uid, "❌ **HATA:** Geçersiz veya daha önce kullanılmış bir Key girdiniz!", reply_markup=main_menu(uid))

# --- [ 🛡️ START & DEKONT ] ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.chat.id
    if not db_query("SELECT id FROM users WHERE id=?", (uid,), fetch=True):
        db_query("INSERT INTO users (id, name, balance) VALUES (?, ?, 10.0)", (uid, message.from_user.first_name))
    bot.send_message(uid, f"🔱 **{MARKA_ADI} HOŞGELDİN**", reply_markup=main_menu(uid))

@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    if message.chat.id == ADMIN_ID: return
    dna = hashlib.md5(str(message.photo[-1].file_size).encode()).hexdigest()
    if db_query("SELECT * FROM vault WHERE dna_hash=?", (dna,), fetch=True):
        bot.reply_to(message, "🚨 Bu dekont kullanılmış!")
    else:
        db_query("INSERT INTO vault VALUES (?)", (dna,))
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (+350₺)", callback_data=f"confirm_{message.chat.id}"))
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.send_message(ADMIN_ID, f"🕵️ **YENİ DEKONT**\nID: `{message.chat.id}`", reply_markup=markup)
        bot.reply_to(message, "⏳ Dekontunuz iletildi.")

# Dekont Onaylama Callback'i
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_payment(call):
    if call.message.chat.id == ADMIN_ID:
        target_id = int(call.data.split("_")[1])
        db_query("UPDATE users SET balance = balance + 350 WHERE id=?", (target_id,))
        bot.send_message(target_id, "✅ **Ödemeniz onaylandı! 350₺ yüklendi.**")
        bot.edit_message_text(f"✅ {target_id} Onaylandı.", ADMIN_ID, call.message.message_id)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
