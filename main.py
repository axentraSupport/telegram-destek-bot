import telebot
import sqlite3
import datetime
import random
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# --- [ 🌐 RENDER AKTİF TUTUCU ] ---
app = Flask('')
@app.route('/')
def home(): return "Axentra V37 - FULL SISTEM ONLINE"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- [ 👑 AYARLAR & TOKEN ] ---
TOKEN = "8723920846:AAH7t5GOTogArVjk7ipZ66iAJqRm1HytTls"
ADMIN_ID = 8561815348
MARKA_ADI = "AxentraStore"
DB_NAME = "axentra_v37_empire.db" # Her şeyin sıfır ve temiz olması için yeni isim

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- [ 🗄️ VERİTABANI MOTORU ] ---
def db_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_NAME, timeout=30) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(query, params)
        if fetch: return c.fetchall()
        conn.commit()

# Veritabanı Mimarisi (XP, Level, Spent, Ref hepsi dahil)
db_query("""CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 15.0, 
           spent REAL DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
           status TEXT DEFAULT 'NORMAL ÜYE', daily_claim TEXT DEFAULT '0', ref_by INTEGER DEFAULT 0)""")
db_query("CREATE TABLE IF NOT EXISTS inventory (uid INTEGER, key_val TEXT, date TEXT)")
db_query("CREATE TABLE IF NOT EXISTS stock (key_data TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, amount REAL)")

# --- [ 📱 ANA MENÜ (GÖRSELDEKİ DİZİLİM) ] ---
def get_main_menu(uid):
    u_res = db_query("SELECT * FROM users WHERE id=?", (uid,), fetch=True)
    if not u_res: return None
    u = u_res[0]
    stok_c = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
    
    markup = InlineKeyboardMarkup(row_width=2)
    # 1. Satır: Satın Al
    markup.add(InlineKeyboardButton(f"🚀 SATIN AL (350₺) [Stok: {stok_c}]", callback_data="buy_now"))
    # 2. Satır: VIP & Slot
    markup.add(InlineKeyboardButton("🌟 KEY İLE VIP AKTİF ET", callback_data="use_coupon"),
               InlineKeyboardButton("🎰 SLOT (HAPPY HOUR)", callback_data="slot"))
    # 3. Satır: Bakiye & Çark
    markup.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="deposit"),
               InlineKeyboardButton("🎡 ÇARKIFELEK", callback_data="wheel"))
    # 4. Satır: Liderler & Envanter
    markup.add(InlineKeyboardButton("🏆 LİDERLER", callback_data="top"),
               InlineKeyboardButton("📦 ENVANTERİM", callback_data="inv"))
    # 5. Satır: Destek & Referans
    markup.add(InlineKeyboardButton("🛠️ DESTEK", url="https://t.me/AxentraStore"),
               InlineKeyboardButton("👥 REFERANS SİSTEMİ", callback_data="referral"))
    # 6. Satır: Günlük & Yazı-Tura
    markup.add(InlineKeyboardButton("📅 GÜNLÜK ÖDÜL", callback_data="daily"),
               InlineKeyboardButton("🪙 YAZI-TURA", callback_data="coin_flip"))
    
    # Alt Bilgi Çubuğu (XP ve Level)
    s_icon = "✨" if u['status'] == "VIP ÜYE" else "👤"
    markup.add(InlineKeyboardButton(f"{s_icon} {u['balance']}₺ | LVL: {u['level']} | XP: {u['xp']}", callback_data="stats"))
    return markup

# --- [ 🛡️ KOMUTLAR VE TUŞLAR ] ---
@bot.message_handler(commands=['start'])
def start_command(message):
    uid = message.chat.id
    if not db_query("SELECT id FROM users WHERE id=?", (uid,), fetch=True):
        args = message.text.split()
        ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        db_query("INSERT INTO users (id, name, balance, ref_by) VALUES (?, ?, 15.0, ?)", (uid, message.from_user.first_name, 15.0, ref))
    
    bot.send_message(uid, f"🔱 **{MARKA_ADI} İmparatorluğu Aktif!**\n\nHoşgeldin kanka!", reply_markup=get_main_menu(uid))

@bot.callback_query_handler(func=lambda call: True)
def btn_manager(call):
    uid, mid = call.message.chat.id, call.message.message_id
    bot.answer_callback_query(call.id)
    u_res = db_query("SELECT * FROM users WHERE id=?", (uid,), fetch=True)
    if not u_res: return
    u = u_res[0]

    if call.data == "home":
        bot.edit_message_text(f"🏠 **{MARKA_ADI} Ana Menü**", uid, mid, reply_markup=get_main_menu(uid))

    elif call.data == "slot":
        if u['balance'] >= 10:
            db_query("UPDATE users SET balance = balance - 10 WHERE id=?", (uid,))
            dice = bot.send_dice(uid, '🎰')
            time.sleep(4)
            if dice.dice.value in [1, 22, 43, 64]:
                win = 200 if u['status'] == "VIP ÜYE" else 100
                db_query("UPDATE users SET balance = balance + ?, xp = xp + 50 WHERE id=?", (win, uid))
                bot.send_message(uid, f"🎊 **KAZANDIN! +{win}₺**")
            bot.send_message(uid, "Menü:", reply_markup=get_main_menu(uid))
        else: bot.send_message(uid, "❌ Slot için 10₺ bakiye lazım!")

    elif call.data == "referral":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.edit_message_text(f"👥 **REFERANS SİSTEMİ**\n\nArkadaşını davet et, ödeme yaptığında **35₺** nakit kap!\n\nSenin Linkin: `{link}`", uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "deposit":
        bot.send_message(uid, "💳 **Bakiyeni yüklemek için dekont fotoğrafını buraya gönder kanka.**")

    elif call.data == "top":
        top = db_query("SELECT name, balance FROM users ORDER BY balance DESC LIMIT 5", fetch=True)
        msg = "🏆 **LİDERLER**\n\n" + "\n".join([f"{i+1}. {x['name']} - {x['balance']}₺" for i, x in enumerate(top)])
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "inv":
        inv = db_query("SELECT key_val FROM inventory WHERE uid=?", (uid,), fetch=True)
        msg = "📦 **ENVANTER**\n\n" + ("\n".join([f"`{x['key_val']}`" for x in inv]) if inv else "Henüz bir şey almadın.")
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

# --- [ 📸 DEKONT VE 35₺ REF BONUSU ] ---
@bot.message_handler(content_types=['photo'])
def receipt_check(message):
    if message.chat.id == ADMIN_ID: return
    mk = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (+350₺)", callback_data=f"payok_{message.chat.id}"))
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(ADMIN_ID, f"🕵️ DEKONT ID: `{message.chat.id}`", reply_markup=mk)
    bot.reply_to(message, "⏳ İletildi, kontrol ediliyor...")

@bot.callback_query_handler(func=lambda call: call.data.startswith("payok_"))
def admin_action(call):
    tid = int(call.data.split("_")[1])
    u = db_query("SELECT * FROM users WHERE id=?", (tid,), fetch=True)[0]
    
    # 350₺ Ekle & VIP Kontrol (380₺ sınırı)
    new_spent = u['spent'] + 350
    status = "VIP ÜYE" if new_spent >= 380 else "NORMAL ÜYE"
    db_query("UPDATE users SET balance = balance + 350, spent = ?, status = ? WHERE id=?", (new_spent, status, tid))
    
    # 35₺ Referans Bonusu Dağıtımı
    if u['ref_by'] != 0:
        db_query("UPDATE users SET balance = balance + 35 WHERE id=?", (u['ref_by'],))
        try: bot.send_message(u['ref_by'], "🎊 Ref bonusun (35₺) yattı! Arkadaşın bakiye yükledi.")
        except: pass
    
    bot.send_message(tid, "✅ Ödemeniz onaylandı, bakiyeniz eklendi!")
    bot.delete_message(ADMIN_ID, call.message.message_id)

# --- [ 🚀 ASLA DURMAYAN SİSTEM ] ---
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Sistem Ateşlendi! Render donmalarına karşı zırhlı mod aktif.")
    
    while True:
        try:
            bot.infinity_polling(timeout=25, long_polling_timeout=15)
        except Exception as e:
            print(f"Hata: {e}. 5 saniye içinde geri dönülüyor...")
            time.sleep(5)
    
