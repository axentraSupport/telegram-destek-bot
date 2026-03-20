import telebot
import sqlite3
import datetime
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- [ 🌐 RENDER AKTİF TUTUCU ] ---
app = Flask('')
@app.route('/')
def home(): return "Axentra V33 SISTEM AKTIF!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True 
    t.start()

# --- [ 👑 AYARLAR & TOKEN ] ---
TOKEN = "8723920846:AAH7t5GOTogArVjk7ipZ66iAJqRm1HytTls"
ADMIN_ID = 8561815348
DB_NAME = "axentra_v33_fix.db"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- [ 🗄️ VERİTABANI MOTORU ] ---
def db_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_NAME, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(query, params)
        if fetch: return c.fetchall()
        conn.commit()

# Tabloları Kur (Level, XP, Ref, Spent hepsi dahil)
db_query("""CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 15.0, 
           spent REAL DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
           status TEXT DEFAULT 'NORMAL ÜYE', ref_by INTEGER DEFAULT 0)""")
db_query("CREATE TABLE IF NOT EXISTS stock (key_data TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS inventory (uid INTEGER, key_val TEXT, date TEXT)")

# --- [ 📱 ANA MENÜ DÜZENİ - GÖRSELDEKİYLE BİREBİR ] ---
def get_main_menu(uid):
    u = db_query("SELECT * FROM users WHERE id=?", (uid,), fetch=True)[0]
    stok_c = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
    
    markup = InlineKeyboardMarkup(row_width=2)
    # GÖRSELDEKİ TUŞLARIN TAM KARŞILIĞI (callback_data'lara dikkat!)
    markup.add(InlineKeyboardButton(f"🚀 SATIN AL (350₺) [Stok: {stok_c}]", callback_data="buy_now"))
    
    markup.add(InlineKeyboardButton("🌟 KEY İLE VIP AKTİF ET", callback_data="use_coupon"),
               InlineKeyboardButton("🎰 SLOT (HAPPY HOUR)", callback_data="slot"))
    
    markup.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="deposit"),
               InlineKeyboardButton("🎡 ÇARKIFELEK", callback_data="wheel"))
    
    markup.add(InlineKeyboardButton("🏆 LİDERLER", callback_data="top"),
               InlineKeyboardButton("📦 ENVANTERİM", callback_data="inv"))
    
    markup.add(InlineKeyboardButton("🛠️ DESTEK", url="https://t.me/AxentraStore"),
               InlineKeyboardButton("📅 GÜNLÜK ÖDÜL", callback_data="daily"))
    
    markup.add(InlineKeyboardButton("👥 REFERANS SİSTEMİ", callback_data="referral"),
               InlineKeyboardButton("🪙 YAZI-TURA", callback_data="coin_flip"))

    if uid == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 ADMİN PANELİ", callback_data="admin_p"))

    # Alt Bilgi Barı
    s_icon = "✨" if u['status'] == "VIP ÜYE" else "👤"
    markup.add(InlineKeyboardButton(f"{s_icon} {u['balance']}₺ | LVL: {u['level']} | XP: {u['xp']}", callback_data="stats"))
    return markup

# --- [ ⚙️ TUŞLARIN ÇALIŞMASINI SAĞLAYAN BEYİN ] ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    uid, mid = call.message.chat.id, call.message.message_id
    # Butona basınca "saat" dönmesini engellemek için:
    bot.answer_callback_query(call.id)
    
    u = db_query("SELECT * FROM users WHERE id=?", (uid,), fetch=True)[0]

    # ANA MENÜYE DÖNÜŞ
    if call.data == "home":
        bot.edit_message_text(f"🏠 **{MARKA_ADI} Ana Menü**", uid, mid, reply_markup=get_main_menu(uid))

    # TUŞ 1: SATIN AL
    elif call.data == "buy_now":
        stok = db_query("SELECT key_data FROM stock LIMIT 1", fetch=True)
        if u['balance'] >= 350 and stok:
            key = stok[0]['key_data']
            db_query("DELETE FROM stock WHERE key_data=?", (key,))
            db_query("UPDATE users SET balance = balance - 350, spent = spent + 350, xp = xp + 300 WHERE id=?", (uid,))
            db_query("INSERT INTO inventory VALUES (?, ?, ?)", (uid, key, str(datetime.date.today())))
            bot.edit_message_text(f"✅ **KEY ALINDI!**\n\n🔑 `{key}`", uid, mid, reply_markup=get_main_menu(uid))
        else: bot.send_message(uid, "❌ Bakiye yetersiz veya stok bitti!")

    # TUŞ 2: SLOT
    elif call.data == "slot":
        if u['balance'] >= 10:
            db_query("UPDATE users SET balance = balance - 10 WHERE id=?", (uid,))
            dice = bot.send_dice(uid, '🎰')
            time.sleep(4)
            if dice.dice.value in [1, 22, 43, 64]:
                win = 200 if u['status'] == "VIP ÜYE" else 100
                db_query("UPDATE users SET balance = balance + ? WHERE id=?", (win, uid))
                bot.send_message(uid, f"🎊 **KAZANDIN! +{win}₺**")
            bot.send_message(uid, "Menüye dönüldü:", reply_markup=get_main_menu(uid))
        else: bot.send_message(uid, "❌ 10₺ bakiye lazım!")

    # TUŞ 3: REF SİSTEMİ (35₺ BONUS)
    elif call.data == "referral":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.edit_message_text(f"👥 **REF SİSTEMİ**\n\nArkadaşın ödeme yapınca **35₺** kap!\n\nLinkin: `{link}`", uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    # DİĞER TUŞLAR (Liderler, Envanter vb.)
    elif call.data == "top":
        top = db_query("SELECT name, balance FROM users ORDER BY balance DESC LIMIT 5", fetch=True)
        msg = "🏆 **LİDERLER**\n\n" + "\n".join([f"{i+1}. {x['name']} - {x['balance']}₺" for i, x in enumerate(top)])
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "inv":
        inv = db_query("SELECT key_val FROM inventory WHERE uid=?", (uid,), fetch=True)
        msg = "📦 **ENVANTER**\n\n" + ("\n".join([f"`{x['key_val']}`" for x in inv]) if inv else "Boş.")
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

# --- [ 🛡️ START KOMUTU ] ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.chat.id
    if not db_query("SELECT id FROM users WHERE id=?", (uid,), fetch=True):
        args = message.text.split()
        ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        db_query("INSERT INTO users (id, name, balance, ref_by) VALUES (?, ?, 15.0, ?)", (uid, message.from_user.first_name, 15.0, ref))
    
    bot.send_message(uid, "🔱 **AxentraStore İmparatorluğu Aktif!**", reply_markup=get_main_menu(uid))

# --- [ 📸 DEKONT SİSTEMİ ] ---
@bot.message_handler(content_types=['photo'])
def pay_msg(message):
    if message.chat.id == ADMIN_ID: return
    mk = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (+350₺)", callback_data=f"ok_{message.chat.id}"))
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(ADMIN_ID, f"🕵️ DEKONT ID: `{message.chat.id}`", reply_markup=mk)
    bot.reply_to(message, "⏳ İletildi, patron onaylayınca para yatar.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("ok_"))
def admin_ok(call):
    tid = int(call.data.split("_")[1])
    u = db_query("SELECT * FROM users WHERE id=?", (tid,), fetch=True)[0]
    new_spent = u['spent'] + 350
    new_status = "VIP ÜYE" if new_spent >= 380 else "NORMAL ÜYE"
    db_query("UPDATE users SET balance = balance + 350, spent = ?, status = ? WHERE id=?", (new_spent, new_status, tid))
    
    if u['ref_by'] != 0:
        db_query("UPDATE users SET balance = balance + 35 WHERE id=?", (u['ref_by'],))
        try: bot.send_message(u['ref_by'], "🎊 Arkadaşın yükleme yaptı, 35₺ kaptın!")
        except: pass
    
    bot.send_message(tid, "✅ Ödemeniz onaylandı!")
    bot.delete_message(ADMIN_ID, call.message.message_id)

# --- [ 🚀 RENDER ATEŞLEME ] ---
if __name__ == "__main__":
    keep_alive()
    print("Bot dinlemeye başladı...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
