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

# SENİN VERDİĞİN ÖZEL BİLGİLER
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
        return c.fetchall() if fetch else conn.commit()

# Tabloları İnşa Et
db_query("""CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, 
           spent REAL DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
           ref_by INTEGER DEFAULT 0, daily_claim TEXT DEFAULT '0')""")
db_query("CREATE TABLE IF NOT EXISTS inventory (uid INTEGER, item_name TEXT, date TEXT)")
db_query("CREATE TABLE IF NOT EXISTS vault (dna_hash TEXT PRIMARY KEY)")

# --- [ 📱 ANA MENÜ ] ---
def main_menu(uid):
    user_data = db_query("SELECT balance, xp, level FROM users WHERE id=?", (uid,), fetch=True)
    if not user_data: return None
    u = user_data[0]
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    markup.add(InlineKeyboardButton("🚀 SATIN AL", callback_data="buy_now"))
    markup.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="deposit"), 
               InlineKeyboardButton("🎰 SLOT MAKİNESİ", callback_data="slot"))
    markup.add(InlineKeyboardButton("👥 REF SİSTEMİ", callback_data="referral"),
               InlineKeyboardButton("🎁 ŞANSLI KASA", callback_data="box"))
    markup.add(InlineKeyboardButton("🏆 LİDERLER", callback_data="top"),
               InlineKeyboardButton("📦 ENVANTERİM", callback_data="inv"))
    markup.add(InlineKeyboardButton("🛠️ DESTEK", callback_data="ticket"),
               InlineKeyboardButton("📆 GÜNLÜK ÖDÜL", callback_data="daily"))
    
    if uid == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 ADMİN PANELİ", callback_data="admin_panel"))

    markup.add(InlineKeyboardButton(f"👤 {u[0]}₺ | LVL: {u[2]} | XP: {u[1]}", callback_data="stats"))
    return markup

# --- [ ⚙️ TÜM İŞLEMLER ] ---
@bot.callback_query_handler(func=lambda call: True)
def callback_logic(call):
    uid, mid = call.message.chat.id, call.message.message_id
    user_res = db_query("SELECT balance, daily_claim, xp FROM users WHERE id=?", (uid,), fetch=True)
    if not user_res: return
    u_data = user_res[0]

    if call.data == "home":
        bot.edit_message_text(f"🏠 **{MARKA_ADI} Ana Menü**", uid, mid, reply_markup=main_menu(uid))

    elif call.data == "deposit":
        msg = (f"💰 **BAKİYE YÜKLEME**\n\n"
               f"🏦 **IBAN:** `{IBAN_ADRESI}`\n"
               f"👤 **Alıcı:** `{AD_SOYAD}`\n"
               f"📝 **Açıklama (Zorunlu):** `{ZORUNLU_ACIKLAMA} {uid}`\n\n"
               f"⚠️ **DİKKAT:** Açıklama kısmına yukarıdaki kodu mutlaka yazın.\n\n"
               f"📸 Ödeme sonrası **DEKONT (Fotoğraf)** gönderin.")
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "admin_panel" and uid == ADMIN_ID:
        bot.edit_message_text("👑 **ADMİN PANELİ**\n\nBakiye onayları için dekontları bekleyin. Manuel işlem için: `/ekle ID Miktar`", uid, mid, 
                             reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data.startswith("confirm_"):
        target_id = int(call.data.split("_")[1])
        db_query("UPDATE users SET balance = balance + 350 WHERE id=?", (target_id,))
        bot.send_message(target_id, "✅ **Ödemeniz onaylandı! 350₺ bakiyeniz yüklendi. İyi oyunlar!**")
        bot.edit_message_text(f"✅ {target_id} ID'li kullanıcıya 350₺ yüklendi.", uid, mid)

    elif call.data == "daily":
        bugun = datetime.datetime.now().strftime("%Y-%m-%d")
        if u_data[1] == bugun:
            bot.answer_callback_query(call.id, "❌ Bugün ödül aldın!", show_alert=True)
        else:
            db_query("UPDATE users SET balance = balance + 3.0, daily_claim = ? WHERE id=?", (bugun, uid))
            bot.answer_callback_query(call.id, "✅ 3₺ hesabına eklendi!", show_alert=True)
            bot.edit_message_text("Güncelleniyor...", uid, mid, reply_markup=main_menu(uid))

    elif call.data == "slot":
        if u_data[0] >= 10:
            db_query("UPDATE users SET balance = balance - 10 WHERE id=?", (uid,))
            dice = bot.send_dice(uid, '🎰')
            time.sleep(3)
            if dice.dice.value in [1, 22, 43, 64]:
                db_query("UPDATE users SET balance = balance + 150 WHERE id=?", (uid,))
                bot.send_message(uid, "🎊 **JACKPOT! 150₺ KAZANDIN!**")
            else:
                bot.send_message(uid, "😢 Şansına küs kanka, gel bir daha dene!")
        else: bot.answer_callback_query(call.id, "❌ 10₺ bakiye lazım!", show_alert=True)

    elif call.data == "inv":
        inv = db_query("SELECT item_name, date FROM inventory WHERE uid=?", (uid,), fetch=True)
        text = "📦 **ENVANTERİNİZ**\n\n"
        if not inv: text += "Henüz bir şey satın almadın."
        for i in inv: text += f"• {i[0]} ({i[1]})\n"
        bot.edit_message_text(text, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "ticket":
        bot.edit_message_text("🛠️ **CANLI DESTEK**\n\nBir sorun mu var kanka? Hemen yaz: @axentradestek", uid, mid, 
                             reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

# --- [ 🛡️ START & DEKONT ] ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.chat.id
    if not db_query("SELECT id FROM users WHERE id=?", (uid,), fetch=True):
        db_query("INSERT INTO users (id, name, balance) VALUES (?, ?, 10.0)", (uid, message.from_user.first_name))
    bot.send_message(uid, f"🔱 **{MARKA_ADI} HOŞGELDİN**\nSana 10₺ başlangıç bakiyesi verdim!", reply_markup=main_menu(uid))

@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    if message.chat.id == ADMIN_ID: return
    dna = hashlib.md5(str(message.photo[-1].file_size).encode()).hexdigest()
    if db_query("SELECT * FROM vault WHERE dna_hash=?", (dna,), fetch=True):
        bot.reply_to(message, "🚨 Bu dekont sistemde zaten var!")
    else:
        db_query("INSERT INTO vault VALUES (?)", (dna,))
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (+350₺)", callback_data=f"confirm_{message.chat.id}"))
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.send_message(ADMIN_ID, f"🕵️ **YENİ DEKONT**\nKullanıcı: {message.from_user.first_name}\nID: `{message.chat.id}`", reply_markup=markup)
        bot.reply_to(message, "⏳ Ödemeniz iletildi, patron onaylayınca bakiyen yüklenecek.")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
        
