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
def home(): return "<h1>AxentraStore Mega Sistem Aktif!</h1>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- [ 👑 KRALİYET AYARLARI ] ---
TOKEN = "8723920846:AAENQIGDgrt9LXUN7VmqiWqxCvoLBYqB_WI" 
ADMIN_ID = 8561815348 
MARKA_ADI = "AxentraStore"

# ÖZEL ÖDEME BİLGİLERİ
IBAN_ADRESI = "TR10 0006 2000 9100 0006 9697 09"
AD_SOYAD = "Garanti Ödeme ve Elektronik Para Hizmetleri A.Ş."
ZORUNLU_ACIKLAMA = "TAMİ7987919953449959"

DB_NAME = "axentra_final_v5.db"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- [ 🗄️ VERİTABANI MOTORU ] ---
def db_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if fetch: return c.fetchall()
        conn.commit()

# Tüm Tabloları Eksiksiz İnşa Et
db_query("""CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, 
           spent REAL DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
           ref_by INTEGER DEFAULT 0, daily_claim TEXT DEFAULT '0')""")
db_query("CREATE TABLE IF NOT EXISTS inventory (uid INTEGER, key_val TEXT, date TEXT)")
db_query("CREATE TABLE IF NOT EXISTS stock (key_data TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS vault (dna_hash TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS vip_keys (key_code TEXT PRIMARY KEY, status TEXT DEFAULT 'active')")

# --- [ 📱 ANA MENÜ FONKSİYONU ] ---
def main_menu(uid):
    user_res = db_query("SELECT balance, xp, level FROM users WHERE id=?", (uid,), fetch=True)
    if not user_res: return None
    u = user_res[0]
    stok_count = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
    hour = datetime.datetime.now().hour
    
    # Gece İndirimi & Dinamik Fiyat Kontrolü
    fiyat = 315 if (0 <= hour <= 6) else (350 if stok_count > 10 else 380)
    
    markup = InlineKeyboardMarkup(row_width=2)
    label = f"🚀 SATIN AL ({fiyat}₺) [Stok: {stok_count}]"
    if 0 <= hour <= 6: label = "🌙 " + label

    markup.add(InlineKeyboardButton(label, callback_data="buy_now"))
    markup.add(InlineKeyboardButton("🌟 KEY İLE VIP AKTİF ET", callback_data="use_vip"))
    markup.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="deposit"), 
               InlineKeyboardButton("🎰 SLOT (HAPPY HOUR)", callback_data="slot"))
    markup.add(InlineKeyboardButton("🏆 LİDERLER", callback_data="top"),
               InlineKeyboardButton("📦 ENVANTERİM", callback_data="inv"))
    markup.add(InlineKeyboardButton("🛠️ DESTEK", callback_data="ticket"),
               InlineKeyboardButton("📆 GÜNLÜK ÖDÜL", callback_data="daily"))
    
    if uid == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 ADMİN PANELİ", callback_data="admin_p"))

    markup.add(InlineKeyboardButton(f"👤 {u[0]}₺ | LVL: {u[2]} | XP: {u[1]}", callback_data="stats"))
    return markup

# --- [ ⚙️ TÜM BUTONLARIN MANTIĞI (CALLBACKS) ] ---
@bot.callback_query_handler(func=lambda call: True)
def callback_logic(call):
    uid, mid = call.message.chat.id, call.message.message_id
    u_res = db_query("SELECT balance, daily_claim, level, xp, ref_by FROM users WHERE id=?", (uid,), fetch=True)
    if not u_res: return
    u = u_res[0]

    if call.data == "home":
        bot.edit_message_text(f"🏠 **{MARKA_ADI} Ana Menü**", uid, mid, reply_markup=main_menu(uid))

    elif call.data == "buy_now":
        hour = datetime.datetime.now().hour
        stok_res = db_query("SELECT key_data FROM stock LIMIT 1", fetch=True)
        stok_c = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
        fiyat = 315 if (0 <= hour <= 6) else (350 if stok_c > 10 else 380)

        if u[0] >= fiyat and stok_res:
            key_val = stok_res[0][0]
            cashback = fiyat * 0.05 # %5 Cashback İadesi
            db_query("DELETE FROM stock WHERE key_data=?", (key_val,))
            db_query("UPDATE users SET balance = balance - ? + ?, spent = spent + ?, xp = xp + 500 WHERE id=?", (fiyat, cashback, fiyat, uid))
            db_query("INSERT INTO inventory VALUES (?, ?, ?)", (uid, key_val, "Yeni"))
            db_query("INSERT INTO vip_keys VALUES (?, 'active')", (key_val,))
            
            # Seviye Atlama Kontrolü (Her 1000 XP'de bir Level)
            new_level = (u[3] + 500) // 1000 + 1
            db_query("UPDATE users SET level = ? WHERE id = ?", (new_level, uid))
            
            # Referans Bonusu (35₺)
            if u[4] != 0:
                db_query("UPDATE users SET balance = balance + 35.0 WHERE id=?", (u[4],))

            bot.edit_message_text(f"✅ **SATIN ALIM BAŞARILI!**\n\n🔑 Key: `{key_val}`\n💸 Cashback: {cashback}₺ iade edildi!\n\nBu keyi 'VIP AKTİF ET' menüsünde kullanabilirsin.", uid, mid, reply_markup=main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ Bakiye yetersiz veya Stok bitti!", show_alert=True)

    elif call.data == "deposit":
        msg = (f"💰 **BAKİYE YÜKLE**\n\n🏦 **IBAN:** `{IBAN_ADRESI}`\n"
               f"👤 **Alıcı:** `{AD_SOYAD}`\n📝 **Açıklama:** `{ZORUNLU_ACIKLAMA} {uid}`\n\n📸 Ödeme sonrası DEKONT gönderin.")
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "slot":
        # Happy Hour Kontrolü (Saat 20:00'de x2 Kazanç)
        if u[0] >= 10:
            db_query("UPDATE users SET balance = balance - 10 WHERE id=?", (uid,))
            dice = bot.send_dice(uid, '🎰')
            time.sleep(3)
            if dice.dice.value in [1, 22, 43, 64]:
                kazanc = 200 if datetime.datetime.now().hour == 20 else 100
                db_query("UPDATE users SET balance = balance + ? WHERE id=?", (kazanc, uid))
                bot.send_message(uid, f"🎊 **TEBRİKLER! {kazanc}₺ KAZANDIN!**")
        else: bot.answer_callback_query(call.id, "❌ 10₺ bakiyen olması lazım!", show_alert=True)

    elif call.data == "daily":
        bugun = datetime.datetime.now().strftime("%Y-%m-%d")
        if u[1] == bugun: bot.answer_callback_query(call.id, "❌ Bugün ödülünü zaten aldın!", show_alert=True)
        else:
            odul = 3.0 + (u[2] * 0.5) # Level arttıkça ödül artar
            db_query("UPDATE users SET balance = balance + ?, daily_claim = ? WHERE id=?", (odul, bugun, uid))
            bot.answer_callback_query(call.id, f"✅ {odul}₺ Günlük Ödül Eklendi!", show_alert=True)
            bot.edit_message_text("Güncelleniyor...", uid, mid, reply_markup=main_menu(uid))

    elif call.data == "use_vip":
        msg = bot.send_message(uid, "🔑 Lütfen VIP aktif etmek için Key kodunu girin:")
        bot.register_next_step_handler(msg, process_vip_key)

    elif call.data == "admin_p" and uid == ADMIN_ID:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("💾 YEDEK AL (.db)", callback_data="backup")).add(InlineKeyboardButton("⬅️ GERİ", callback_data="home"))
        bot.edit_message_text("👑 **ADMİN PANELİ**\nSistem durumu aktif.", uid, mid, reply_markup=markup)

    elif call.data == "backup":
        with open(DB_NAME, 'rb') as f: bot.send_document(ADMIN_ID, f, caption="📂 Sistem Veritabanı Yedeği")

    elif call.data.startswith("confirm_"):
        target_id = int(call.data.split("_")[1])
        db_query("UPDATE users SET balance = balance + 350 WHERE id=?", (target_id,))
        bot.send_message(target_id, "✅ **ÖDEMENİZ ONAYLANDI! 350₺ YÜKLENDİ.**")
        bot.edit_message_text(f"✅ {target_id} Onaylandı.", ADMIN_ID, mid)

# --- [ 🔑 VIP ANAHTAR KONTROLÜ ] ---
def process_vip_key(message):
    uid = message.chat.id
    input_key = message.text.strip()
    check = db_query("SELECT status FROM vip_keys WHERE key_code=?", (input_key,), fetch=True)
    if check and check[0][0] == 'active':
        db_query("UPDATE vip_keys SET status='used' WHERE key_code=?", (input_key,))
        bot.send_message(uid, "🎊 **VIP BAŞARIYLA AKTİF EDİLDİ!**\n\n🔗 [VIP KANALINA GİRİŞ YAP](https://t.me/axentravip)", reply_markup=main_menu(uid))
    else: bot.send_message(uid, "❌ HATA: Geçersiz veya kullanılmış anahtar!", reply_markup=main_menu(uid))

# --- [ 🛡️ START & DEKONT SİSTEMİ ] ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.chat.id
    if not db_query("SELECT id FROM users WHERE id=?", (uid,), fetch=True):
        args = message.text.split()
        ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        db_query("INSERT INTO users (id, name, balance, ref_by) VALUES (?, ?, 15.0, ?)", (uid, message.from_user.first_name, ref))
    bot.send_message(uid, f"🔱 **{MARKA_ADI} MAĞAZASINA HOŞGELDİN**", reply_markup=main_menu(uid))

@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    if message.chat.id == ADMIN_ID: return
    # Dekont DNA Kontrolü (Sahte dekont önleme)
    dna = hashlib.md5(str(message.photo[-1].file_size).encode()).hexdigest()
    if not db_query("SELECT * FROM vault WHERE dna_hash=?", (dna,), fetch=True):
        db_query("INSERT INTO vault VALUES (?)", (dna,))
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (+350₺)", callback_data=f"confirm_{message.chat.id}"))
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.send_message(ADMIN_ID, f"🕵️ **YENİ DEKONT BİLDİRİMİ**\nKullanıcı ID: `{message.chat.id}`", reply_markup=markup)
        bot.reply_to(message, "⏳ Ödemeniz iletildi, patron onaylayınca bakiye yüklenecek.")

if __name__ == "__main__":
    # Otomatik Stok Doldurma (Format: AXNT-XXX-XXXX)
    s_cnt = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
    if s_cnt < 30:
        for _ in range(30 - s_cnt):
            k = f"AXNT-{random.randint(100,999)}-{random.randint(1000,9999)}"
            db_query("INSERT OR IGNORE INTO stock VALUES (?)", (k,))
    
    keep_alive()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
