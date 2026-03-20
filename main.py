import telebot
import sqlite3
import datetime
import hashlib
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- [ 🌐 7/24 AKTİF TUTMA ] ---
app = Flask('')
@app.route('/')
def home(): return "<h1>AxentraStore Sistemi Aktif!</h1>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- [ 👑 AYARLAR ] ---
TOKEN = "8723920846:AAENQIGDgrt9LXUN7VmqiWqxCvoLBYqB_WI" 
ADMIN_ID = 8561815348 
MARKA_ADI = "AxentraStore"
IBAN_ADRESI = "TR10 0006 2000 9100 0006 9697 09"
AD_SOYAD = "Garanti Ödeme ve Elektronik Para Hizmetleri A.Ş."
ZORUNLU_ACIKLAMA = "TAMİ7987919953449959"

DB_NAME = "axentra_final_v6.db"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- [ 🗄️ VERİTABANI ] ---
def db_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if fetch: return c.fetchall()
        conn.commit()

# Tablo Kurulumu
db_query("""CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, 
           spent REAL DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
           ref_by INTEGER DEFAULT 0, daily_claim TEXT DEFAULT '0')""")
db_query("CREATE TABLE IF NOT EXISTS inventory (uid INTEGER, key_val TEXT, date TEXT)")
db_query("CREATE TABLE IF NOT EXISTS stock (key_data TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS vault (dna_hash TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS vip_keys (key_code TEXT PRIMARY KEY, status TEXT DEFAULT 'active')")

# --- [ 📱 MENÜLER ] ---
def main_menu(uid):
    u = db_query("SELECT balance, xp, level FROM users WHERE id=?", (uid,), fetch=True)[0]
    stok = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
    hour = datetime.datetime.now().hour
    fiyat = 315 if (0 <= hour <= 6) else (350 if stok > 10 else 380)
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(f"🚀 SATIN AL ({fiyat}₺) [Stok: {stok}]", callback_data="buy_now"))
    markup.add(InlineKeyboardButton("🌟 KEY İLE VIP AKTİF ET", callback_data="use_vip"))
    markup.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="deposit"), 
               InlineKeyboardButton("🎰 SLOT (HAPPY HOUR)", callback_data="slot"))
    markup.add(InlineKeyboardButton("🏆 LİDERLER", callback_data="top"),
               InlineKeyboardButton("📦 ENVANTERİM", callback_data="inv"))
    markup.add(InlineKeyboardButton("🛠️ DESTEK", callback_data="ticket"),
               InlineKeyboardButton("📆 GÜNLÜK ÖDÜL", callback_data="daily"))
    markup.add(InlineKeyboardButton("👥 REF SİSTEMİ", callback_data="referral"))
    
    if uid == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 ADMİN PANELİ", callback_data="admin_p"))

    markup.add(InlineKeyboardButton(f"👤 {u[0]}₺ | LVL: {u[2]} | XP: {u[1]}", callback_data="stats"))
    return markup

# --- [ ⚙️ CALLBACK MANTIĞI ] ---
@bot.callback_query_handler(func=lambda call: True)
def callback_logic(call):
    uid, mid = call.message.chat.id, call.message.message_id
    user_res = db_query("SELECT balance, daily_claim, level, xp, ref_by FROM users WHERE id=?", (uid,), fetch=True)
    if not user_res: return
    u = user_res[0]

    if call.data == "home":
        bot.edit_message_text(f"🏠 **{MARKA_ADI} Ana Menü**", uid, mid, reply_markup=main_menu(uid))

    elif call.data == "top":
        top = db_query("SELECT name, balance FROM users ORDER BY balance DESC LIMIT 5", fetch=True)
        msg = "🏆 **LİDERLİK TABLOSU**\n\n" + "\n".join([f"{i+1}. {x[0]} - {x[1]}₺" for i, x in enumerate(top)])
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "inv":
        inv = db_query("SELECT key_val FROM inventory WHERE uid=?", (uid,), fetch=True)
        msg = "📦 **ENVANTERİM**\n\n" + ("\n".join([f"`{x[0]}`" for x in inv]) if inv else "Henüz bir key almadın.")
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "ticket":
        bot.edit_message_text("🛠️ **DESTEK**\nBir sorun mu var? Kurucuya ulaş: @senin_kullanici_adin", uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "referral":
        bot.edit_message_text(f"👥 **REF SİSTEMİ**\n\nArkadaşını davet et, her alımından 35₺ kazan!\n\n`https://t.me/{bot.get_me().username}?start={uid}`", uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "admin_p" and uid == ADMIN_ID:
        # DETAYLI ADMİN PANELİ
        total_u = db_query("SELECT COUNT(*) FROM users", fetch=True)[0][0]
        total_cash = db_query("SELECT SUM(balance) FROM users", fetch=True)[0][0]
        stok_c = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
        sold_c = db_query("SELECT COUNT(*) FROM inventory", fetch=True)[0][0]
        
        panel_msg = (f"👑 **GELİŞMİŞ ADMİN PANELİ**\n\n"
                     f"👥 Toplam Üye: `{total_u}`\n"
                     f"💰 Cüzdanlardaki Para: `{total_cash}₺`\n"
                     f"📦 Aktif Stok: `{stok_c}`\n"
                     f"🛒 Toplam Satış: `{sold_c}`")
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 DUYURU GÖNDER", callback_data="admin_broadcast"))
        markup.add(InlineKeyboardButton("💾 YEDEK AL (.db)", callback_data="backup"))
        markup.add(InlineKeyboardButton("⬅️ GERİ", callback_data="home"))
        bot.edit_message_text(panel_msg, uid, mid, reply_markup=markup)

    elif call.data == "admin_broadcast":
        msg = bot.send_message(uid, "📢 Göndermek istediğiniz mesajı yazın (İptal için /cancel):")
        bot.register_next_step_handler(msg, process_broadcast)

    # ... (Diğer satın alım, slot, daily ve onay butonları önceki kodla aynı, hepsi fixlendi) ...
    elif call.data == "buy_now":
        stok_res = db_query("SELECT key_data FROM stock LIMIT 1", fetch=True)
        if u[0] >= 350 and stok_res:
            key_val = stok_res[0][0]
            db_query("DELETE FROM stock WHERE key_data=?", (key_val,))
            db_query("UPDATE users SET balance = balance - 350, spent = spent + 350, xp = xp + 500 WHERE id=?", (uid,))
            db_query("INSERT INTO inventory VALUES (?, ?, ?)", (uid, key_val, "Şimdi"))
            db_query("INSERT INTO vip_keys VALUES (?, 'active')", (key_val,))
            bot.edit_message_text(f"✅ **KEY ALINDI:** `{key_val}`", uid, mid, reply_markup=main_menu(uid))
        else: bot.answer_callback_query(call.id, "Bakiyen yetersiz veya stok yok!", show_alert=True)

    elif call.data == "deposit":
        bot.edit_message_text(f"🏦 IBAN: `{IBAN_ADRESI}`\nAlıcı: `{AD_SOYAD}`\nKod: `{ZORUNLU_ACIKLAMA} {uid}`", uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "slot":
        if u[0] >= 10:
            db_query("UPDATE users SET balance = balance - 10 WHERE id=?", (uid,))
            bot.send_dice(uid, '🎰')
        else: bot.answer_callback_query(call.id, "10₺ lazım!", show_alert=True)

    elif call.data == "daily":
        bugun = datetime.datetime.now().strftime("%Y-%m-%d")
        if u[1] == bugun: bot.answer_callback_query(call.id, "Bugün aldın zaten!", show_alert=True)
        else:
            db_query("UPDATE users SET balance = balance + 5, daily_claim = ? WHERE id=?", (bugun, uid))
            bot.answer_callback_query(call.id, "5₺ eklendi!", show_alert=True)
            bot.edit_message_text("Güncellendi!", uid, mid, reply_markup=main_menu(uid))

    elif call.data == "use_vip":
        msg = bot.send_message(uid, "🔑 Key kodunu girin:")
        bot.register_next_step_handler(msg, process_vip)

    elif call.data == "backup":
        with open(DB_NAME, 'rb') as f: bot.send_document(ADMIN_ID, f, caption="📂 DB Yedeği")

    elif call.data.startswith("confirm_"):
        tid = int(call.data.split("_")[1])
        db_query("UPDATE users SET balance = balance + 350 WHERE id=?", (tid,))
        bot.send_message(tid, "✅ Ödeme onaylandı!")
        bot.delete_message(ADMIN_ID, mid)

# --- [ 📢 DUYURU SİSTEMİ ] ---
def process_broadcast(message):
    if message.text == "/cancel": return
    users = db_query("SELECT id FROM users", fetch=True)
    count = 0
    for user in users:
        try:
            bot.send_message(user[0], f"🔔 **DUYURU**\n\n{message.text}")
            count += 1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Duyuru {count} kişiye iletildi.")

# ... (process_vip, start_cmd ve handle_receipt fonksiyonlarını eklemeyi unutma) ...
def process_vip(message):
    key = message.text.strip()
    check = db_query("SELECT status FROM vip_keys WHERE key_code=?", (key,), fetch=True)
    if check and check[0][0] == 'active':
        db_query("UPDATE vip_keys SET status='used' WHERE key_code=?", (key,))
        bot.send_message(message.chat.id, "🎊 VIP Aktif! Link: https://t.me/axentravip")
    else: bot.send_message(message.chat.id, "Geçersiz key!")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.chat.id
    if not db_query("SELECT id FROM users WHERE id=?", (uid,), fetch=True):
        args = message.text.split()
        ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        db_query("INSERT INTO users (id, name, balance, ref_by) VALUES (?, ?, 15.0, ?)", (uid, message.from_user.first_name, ref))
    bot.send_message(uid, f"🔱 {MARKA_ADI} Hoşgeldin!", reply_markup=main_menu(uid))

@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    if message.chat.id == ADMIN_ID: return
    dna = hashlib.md5(str(message.photo[-1].file_size).encode()).hexdigest()
    if not db_query("SELECT * FROM vault WHERE dna_hash=?", (dna,), fetch=True):
        db_query("INSERT INTO vault VALUES (?)", (dna,))
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (+350₺)", callback_data=f"confirm_{message.chat.id}"))
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.send_message(ADMIN_ID, f"🕵️ Dekont Geldi ID: {message.chat.id}", reply_markup=markup)
        bot.reply_to(message, "⏳ İletildi.")

if __name__ == "__main__":
    s_cnt = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
    if s_cnt < 30:
        for _ in range(30-s_cnt): db_query("INSERT OR IGNORE INTO stock VALUES (?)", (f"AXNT-{random.randint(100,999)}-{random.randint(1000,9999)}",))
    keep_alive()
    bot.infinity_polling()
