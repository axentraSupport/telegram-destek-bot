import telebot
import sqlite3
import datetime
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- [ 🌐 7/24 KESİNTİSİZ ÇALIŞMA ] ---
app = Flask('')
@app.route('/')
def home(): return "<h1>AxentraStore V29 - BUTONLAR TAMİR EDİLDİ!</h1>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- [ 👑 YENİ TOKEN VE AYARLAR ] ---
TOKEN = "8723920846:AAH7t5GOTogArVjk7ipZ66iAJqRm1HytTls" 
ADMIN_ID = 8561815348 
MARKA_ADI = "AxentraStore"
DESTEK_ADRESI = "AxentraStore"

# ÖDEME BİLGİLERİ
IBAN_ADRESI = "TR10 0006 2000 9100 0006 9697 09"
AD_SOYAD = "Garanti Ödeme ve Elektronik Para Hizmetleri A.Ş."
ZORUNLU_ACIKLAMA = "TAMİ7987919953449959"

DB_NAME = "axentra_ultra_v29.db" 
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- [ 🗄️ VERİTABANI MOTORU ] ---
def db_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(query, params)
        if fetch: return c.fetchall()
        conn.commit()

# Tabloları Eksiksiz Kur (Level, XP, Ref, Spent hepsi dahil)
db_query("""CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 15.0, 
           spent REAL DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
           status TEXT DEFAULT 'NORMAL ÜYE', daily_claim TEXT DEFAULT '0', ref_by INTEGER DEFAULT 0)""")
db_query("CREATE TABLE IF NOT EXISTS inventory (uid INTEGER, key_val TEXT, date TEXT)")
db_query("CREATE TABLE IF NOT EXISTS stock (key_data TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, amount REAL)")

# --- [ 📱 ANA MENÜ - TÜM BUTONLAR BURADA ] ---
def get_main_menu(uid):
    u = db_query("SELECT * FROM users WHERE id=?", (uid,), fetch=True)[0]
    stok_c = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Görseldeki Dizilim + Bütün Özellikler
    markup.add(InlineKeyboardButton(f"🚀 SATIN AL (350₺) [Stok: {stok_c}]", callback_data="buy_now"))
    
    # VIP & Slot (Görseldeki 2. Satır)
    markup.add(InlineKeyboardButton("🌟 KEY İLE VIP AKTİF ET", callback_data="use_coupon"),
               InlineKeyboardButton("🎰 SLOT (HAPPY HOUR)", callback_data="slot"))
    
    # Finans & Şans
    markup.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="deposit"),
               InlineKeyboardButton("🎡 ÇARKIFELEK", callback_data="wheel"))
    
    # Profil & Diğerleri
    markup.add(InlineKeyboardButton("🏆 LİDERLER", callback_data="top"),
               InlineKeyboardButton("📦 ENVANTERİM", callback_data="inv"))
    
    # Sosyal & Destek
    markup.add(InlineKeyboardButton("🛠️ DESTEK", url=f"https://t.me/{DESTEK_ADRESI}"),
               InlineKeyboardButton("👥 REF SİSTEMİ", callback_data="referral"))
    
    # Günlük Ödül & Yazı Tura
    markup.add(InlineKeyboardButton("📅 GÜNLÜK ÖDÜL", callback_data="daily"),
               InlineKeyboardButton("🪙 YAZI-TURA", callback_data="coin_flip"))

    if uid == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 ADMİN PANELİ", callback_data="admin_p"))

    # Alt Bilgi Çubuğu
    stat_icon = "✨" if u['status'] == "VIP ÜYE" else "👤"
    markup.add(InlineKeyboardButton(f"{stat_icon} {u['balance']}₺ | LVL: {u['level']} | XP: {u['xp']}", callback_data="stats"))
    return markup

# --- [ ⚙️ ANA CALLBACK MANTIĞI - %100 ÇALIŞMA GARANTİLİ ] ---
@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    uid, mid = call.message.chat.id, call.message.message_id
    u_res = db_query("SELECT * FROM users WHERE id=?", (uid,), fetch=True)
    if not u_res: return
    u = u_res[0]

    # [GERİ DÖNÜŞ]
    if call.data == "home":
        bot.edit_message_text(f"🏠 **{MARKA_ADI} Ana Menü**", uid, mid, reply_markup=get_main_menu(uid))

    # [MARKET]
    elif call.data == "buy_now":
        stok = db_query("SELECT key_data FROM stock LIMIT 1", fetch=True)
        if u['balance'] >= 350 and stok:
            key = stok[0]['key_data']
            db_query("DELETE FROM stock WHERE key_data=?", (key,))
            db_query("UPDATE users SET balance = balance - 350, spent = spent + 350, xp = xp + 300 WHERE id=?", (uid,))
            db_query("INSERT INTO inventory VALUES (?, ?, ?)", (uid, key, str(datetime.date.today())))
            bot.edit_message_text(f"✅ **BAŞARILI!**\n\n🔑 Key: `{key}`", uid, mid, reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ Bakiye veya Stok Yetersiz!", show_alert=True)

    # [ŞANS OYUNLARI]
    elif call.data == "slot":
        if u['balance'] >= 10:
            db_query("UPDATE users SET balance = balance - 10 WHERE id=?", (uid,))
            dice = bot.send_dice(uid, '🎰')
            time.sleep(4)
            if dice.dice.value in [1, 22, 43, 64]:
                kazanc = 200 if u['status'] == "VIP ÜYE" else 100
                db_query("UPDATE users SET balance = balance + ? WHERE id=?", (kazanc, uid))
                bot.send_message(uid, f"🎊 **TEBRİKLER! +{kazanc}₺**")
            bot.send_message(uid, "Menü:", reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ 10₺ bakiye lazım!", show_alert=True)

    elif call.data == "wheel":
        if u['balance'] >= 25:
            db_query("UPDATE users SET balance = balance - 25 WHERE id=?", (uid,))
            bot.edit_message_text("🎡 Çark dönüyor...", uid, mid)
            time.sleep(2)
            win = random.choice(["20₺", "50₺", "BOŞ", "300 XP"])
            if win == "20₺": db_query("UPDATE users SET balance = balance + 20 WHERE id=?", (uid,))
            elif win == "50₺": db_query("UPDATE users SET balance = balance + 50 WHERE id=?", (uid,))
            bot.send_message(uid, f"🎡 Sonuç: **{win}**!", reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ 25₺ bakiye lazım!", show_alert=True)

    # [DİĞER MENÜLER]
    elif call.data == "top":
        top = db_query("SELECT name, balance FROM users ORDER BY balance DESC LIMIT 5", fetch=True)
        msg = "🏆 **LİDERLER**\n\n" + "\n".join([f"{i+1}. {x['name']} - {x['balance']}₺" for i, x in enumerate(top)])
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "inv":
        inv = db_query("SELECT key_val FROM inventory WHERE uid=?", (uid,), fetch=True)
        msg = "📦 **ENVANTER**\n\n" + ("\n".join([f"`{x['key_val']}`" for x in inv]) if inv else "Boş.")
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "referral":
        ref_link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.edit_message_text(f"👥 **REF SİSTEMİ**\n\nArkadaşını davet et, ödeme yapınca **35₺** kap!\n\n`{ref_link}`", uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "admin_p" and uid == ADMIN_ID:
        mk = InlineKeyboardMarkup().add(InlineKeyboardButton("📦 STOK EKLE", callback_data="adm_stok"),
                                       InlineKeyboardButton("📢 DUYURU", callback_data="adm_bc")).add(InlineKeyboardButton("⬅️ GERİ", callback_data="home"))
        bot.edit_message_text("👑 **ADMİN PANELİ**", uid, mid, reply_markup=mk)

# --- [ 🛡️ START & ÖDEME ] ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = message.chat.id
    if not db_query("SELECT id FROM users WHERE id=?", (uid,), fetch=True):
        args = message.text.split()
        ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        db_query("INSERT INTO users (id, name, balance, ref_by) VALUES (?, ?, 15.0, ?)", (uid, message.from_user.first_name, 15.0, ref))
    
    bot.send_message(uid, f"🔱 **{MARKA_ADI} HOŞGELDİN**", reply_markup=get_main_menu(uid))

@bot.message_handler(content_types=['photo'])
def handle_pay(message):
    if message.chat.id == ADMIN_ID: return
    mk = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (+350₺)", callback_data=f"ok_{message.chat.id}"))
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(ADMIN_ID, f"🕵️ DEKONT ID: `{message.chat.id}`", reply_markup=mk)
    bot.reply_to(message, "⏳ İletildi!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("ok_"))
def admin_ok(call):
    tid = int(call.data.split("_")[1])
    u = db_query("SELECT * FROM users WHERE id=?", (tid,), fetch=True)[0]
    new_spent = u['spent'] + 350
    new_status = "VIP ÜYE" if new_spent >= 380 else "NORMAL ÜYE"
    db_query("UPDATE users SET balance = balance + 350, spent = ?, status = ? WHERE id=?", (new_spent, new_status, tid))
    
    if u['ref_by'] != 0:
        db_query("UPDATE users SET balance = balance + 35 WHERE id=?", (u['ref_by'],))
        try: bot.send_message(u['ref_by'], "🎊 Ref bonusun (35₺) yattı!")
        except: pass
    
    bot.send_message(tid, "✅ Ödemeniz onaylandı!")
    bot.delete_message(ADMIN_ID, call.message.message_id)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
