import telebot
import sqlite3
import datetime
import hashlib
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- [ 🌐 7/24 AKTİF TUTMA SİSTEMİ ] ---
app = Flask('')
@app.route('/')
def home(): return "<h1>AxentraStore Sistemi Aktif!</h1>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [ 👑 KRALİYET AYARLARI ] ---
TOKEN = "8723920846:AAEwjNsklKizeN1DY2alFIwo8k5oz7dJ1Hg" 
ADMIN_ID = 8561815348 
MARKA_ADI = "AxentraStore"
IBAN_ADRESI = "TR10 0006 2000 9100 0006 9697 09"
ZORUNLU_ACIKLAMA = "TAMİ7987919953449959"

DB_NAME = "axentra_final.db"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- [ 🗄️ VERİTABANI MOTORU ] ---
def db_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchall() if fetch else conn.commit()

# Tabloları İnşa Et
db_query("""CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, 
           spent REAL DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
           ref_by INTEGER DEFAULT 0, daily_claim TEXT DEFAULT '0')""")
db_query("CREATE TABLE IF NOT EXISTS inventory (uid INTEGER, key_val TEXT, date TEXT)")
db_query("CREATE TABLE IF NOT EXISTS stock (key_data TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS vault (dna_hash TEXT PRIMARY KEY)")

# Otomatik Stok Basımı
stok_say = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
if stok_say < 100:
    for _ in range(100 - stok_say):
        k = f"AXNT-{random.randint(100,999)}-{random.randint(1000,9999)}"
        db_query("INSERT OR IGNORE INTO stock (key_data) VALUES (?)", (k,))

# --- [ 📱 ANA MENÜ ] ---
def main_menu(uid):
    u = db_query("SELECT balance, xp, level FROM users WHERE id=?", (uid,), fetch=True)[0]
    stok = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
    hour = datetime.datetime.now().hour
    fiyat = 315 if (0 <= hour <= 6) else 350
    
    markup = InlineKeyboardMarkup(row_width=2)
    label = f"🚀 SATIN AL ({fiyat}₺) [Stok: {stok}]"
    if 0 <= hour <= 6: label = "🌙 " + label

    markup.add(InlineKeyboardButton(label, callback_data="buy_now"))
    markup.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="deposit"), 
               InlineKeyboardButton("🎰 SLOT MAKİNESİ", callback_data="slot"))
    markup.add(InlineKeyboardButton("👥 REF SİSTEMİ", callback_data="referral"),
               InlineKeyboardButton("🎁 ŞANSLI KASA", callback_data="box"))
    markup.add(InlineKeyboardButton("📦 ENVANTERİM", callback_data="inv"))
    markup.add(InlineKeyboardButton("📆 GÜNLÜK ÖDÜL", callback_data="daily"))
    
    # Admin Paneli Butonu (Sadece Sana Görünür)
    if uid == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 ADMİN PANELİ", callback_data="admin_panel"))

    markup.add(InlineKeyboardButton(f"👤 {u[0]}₺ | LVL: {u[2]} | XP: {u[1]}", callback_data="stats"))
    return markup

# --- [ ⚙️ TÜM İŞLEMLER ] ---
@bot.callback_query_handler(func=lambda call: True)
def callback_logic(call):
    uid, mid = call.message.chat.id, call.message.message_id
    
    # Kullanıcı verilerini çek
    user_res = db_query("SELECT balance, daily_claim, ref_by FROM users WHERE id=?", (uid,), fetch=True)
    if not user_res: return
    u_data = user_res[0]

    if call.data == "home":
        bot.edit_message_text(f"🏠 **{MARKA_ADI} Ana Menü**", uid, mid, reply_markup=main_menu(uid))

    elif call.data == "admin_panel" and uid == ADMIN_ID:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Herkese Duyuru", callback_data="admin_bc"))
        markup.add(InlineKeyboardButton("⬅️ Geri", callback_data="home"))
        bot.edit_message_text("👑 **ADMİN KONTROL PANELİ**\nHangi işlemi yapmak istersin patron?", uid, mid, reply_markup=markup)

    elif call.data.startswith("confirm_"):
        target_id = int(call.data.split("_")[1])
        db_query("UPDATE users SET balance = balance + 350 WHERE id=?", (target_id,))
        bot.send_message(target_id, "✅ **Ödemeniz onaylandı! 350₺ bakiyeniz yüklendi.**")
        bot.edit_message_text(f"✅ {target_id} ID'li kullanıcıya 350₺ yüklendi.", uid, mid)

    elif call.data == "daily":
        bugun = datetime.datetime.now().strftime("%Y-%m-%d")
        if u_data[1] == bugun:
            bot.answer_callback_query(call.id, "❌ Bugün ödül aldın!", show_alert=True)
        else:
            db_query("UPDATE users SET balance = balance + 3.0, daily_claim = ? WHERE id=?", (bugun, uid))
            bot.answer_callback_query(call.id, "✅ 3₺ eklendi!", show_alert=True)
            bot.edit_message_text("Güncelleniyor...", uid, mid, reply_markup=main_menu(uid))

    elif call.data == "slot":
        if u_data[0] >= 10:
            db_query("UPDATE users SET balance = balance - 10 WHERE id=?", (uid,))
            dice = bot.send_dice(uid, '🎰')
            time.sleep(3)
            if dice.dice.value in [1, 22, 43, 64]:
                db_query("UPDATE users SET balance = balance + 100 WHERE id=?", (uid,))
                bot.send_message(uid, "🎊 JACKPOT! 100₺ KAZANDIN!")
            else:
                bot.send_message(uid, "😢 Bu sefer olmadı kanka, tekrar dene!")
        else: bot.answer_callback_query(call.id, "❌ 10₺ lazım!", show_alert=True)

    elif call.data == "deposit":
        bot.edit_message_text(f"💰 **BAKİYE YÜKLE**\n\nIBAN: `{IBAN_ADRESI}`\nKod: `{ZORUNLU_ACIKLAMA} {uid}`\n\n📸 Dekont at.", uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

# --- [ 🛡️ START & DEKONT ] ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.chat.id
    if not db_query("SELECT id FROM users WHERE id=?", (uid,), fetch=True):
        args = message.text.split()
        ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        db_query("INSERT INTO users (id, name, balance, ref_by) VALUES (?, ?, 10.0, ?)", (uid, message.from_user.first_name, ref))
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
        bot.send_message(ADMIN_ID, f"🕵️ DEKONT GELDİ!\nKullanıcı: {message.from_user.first_name}\nID: `{message.chat.id}`", reply_markup=markup)
        bot.reply_to(message, "⏳ Ödemeniz iletildi, kontrol ediliyor...")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
    
