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
def home(): return "<h1>AxentraStore Mega Birleşik Sistem Aktif!</h1>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- [ 👑 AYARLAR ] ---
TOKEN = "8723920846:AAENQIGDgrt9LXUN7VmqiWqxCvoLBYqB_WI" 
ADMIN_ID = 8561815348 
MARKA_ADI = "AxentraStore"
DESTEK_ADRESI = "AxentraStore"
IBAN_ADRESI = "TR10 0006 2000 9100 0006 9697 09"
AD_SOYAD = "Garanti Ödeme ve Elektronik Para Hizmetleri A.Ş."
ZORUNLU_ACIKLAMA = "TAMİ7987919953449959"

DB_NAME = "axentra_mega_v11.db"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- [ 🗄️ VERİTABANI ] ---
def db_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if fetch: return c.fetchall()
        conn.commit()

# Tablolar (Tüm geçmiş verilerle uyumlu)
db_query("""CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, 
           spent REAL DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
           status TEXT DEFAULT 'Normal', daily_claim TEXT DEFAULT '0', ref_by INTEGER DEFAULT 0)""")
db_query("CREATE TABLE IF NOT EXISTS inventory (uid INTEGER, key_val TEXT, date TEXT)")
db_query("CREATE TABLE IF NOT EXISTS stock (key_data TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS vault (dna_hash TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS vip_keys (key_code TEXT PRIMARY KEY, status TEXT DEFAULT 'active')")

# --- [ 📱 DİNAMİK MENÜ (ÜYELİK AYRIMLI) ] ---
def get_main_menu(uid):
    u = db_query("SELECT balance, level, status, xp FROM users WHERE id=?", (uid,), fetch=True)[0]
    stok_c = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
    hour = datetime.datetime.now().hour
    
    # [GECE İNDİRİMİ MANTIĞI]
    fiyat = 315 if (0 <= hour <= 6) else (350 if stok_c > 10 else 380)
    
    markup = InlineKeyboardMarkup(row_width=2)
    # Üst Kısım
    label = f"🚀 SATIN AL ({fiyat}₺)"
    if 0 <= hour <= 6: label = "🌙 " + label
    
    markup.add(InlineKeyboardButton(label, callback_data=f"buy_{fiyat}"))
    
    if u[2] == "Normal":
        markup.add(InlineKeyboardButton("🌟 VIP ÜYE OL (500₺)", callback_data="upgrade_vip"))
    else:
        markup.add(InlineKeyboardButton("💎 VIP PANELİ", callback_data="vip_panel"))

    # Orta Kısım
    markup.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="deposit"), 
               InlineKeyboardButton("🎰 SLOT MAKİNESİ", callback_data="slot"))
    markup.add(InlineKeyboardButton("🏆 LİDERLER", callback_data="top"),
               InlineKeyboardButton("📦 ENVANTERİM", callback_data="inv"))
    markup.add(InlineKeyboardButton("🛠️ DESTEK", url=f"https://t.me/{DESTEK_ADRESI}"),
               InlineKeyboardButton("📆 GÜNLÜK ÖDÜL", callback_data="daily"))
    markup.add(InlineKeyboardButton("👥 REF SİSTEMİ", callback_data="referral"))
    
    if uid == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 ADMİN PANELİ", callback_data="admin_p"))

    # Alt Bilgi
    stat_label = f"✨ VIP | {u[0]}₺" if u[2] == "VIP" else f"👤 {u[0]}₺ | LVL: {u[1]}"
    markup.add(InlineKeyboardButton(stat_label, callback_data="stats"))
    return markup

# --- [ ⚙️ ANA MANTIK (CALLBACKS) ] ---
@bot.callback_query_handler(func=lambda call: True)
def process_callbacks(call):
    uid, mid = call.message.chat.id, call.message.message_id
    user = db_query("SELECT balance, status, level, xp, ref_by, daily_claim FROM users WHERE id=?", (uid,), fetch=True)[0]

    if call.data == "home":
        bot.edit_message_text(f"🏠 **{MARKA_ADI} Ana Menü**", uid, mid, reply_markup=get_main_menu(uid))

    elif call.data.startswith("buy_"):
        fiyat = float(call.data.split("_")[1])
        stok = db_query("SELECT key_data FROM stock LIMIT 1", fetch=True)
        if user[0] >= fiyat and stok:
            key = stok[0][0]
            cashback = fiyat * 0.05 # [%5 CASHBACK]
            db_query("DELETE FROM stock WHERE key_data=?", (key,))
            db_query("UPDATE users SET balance = balance - ? + ?, spent = spent + ?, xp = xp + 500 WHERE id=?", (fiyat, cashback, fiyat, uid))
            db_query("INSERT INTO inventory VALUES (?, ?, ?)", (uid, key, "Şimdi"))
            
            # [REF BONUSU]
            if user[4] != 0:
                db_query("UPDATE users SET balance = balance + 35 WHERE id=?", (user[4],))
            
            # [LEVEL KONTROL]
            new_lvl = (user[3] + 500) // 1000 + 1
            db_query("UPDATE users SET level = ? WHERE id = ?", (new_lvl, uid))
            
            bot.edit_message_text(f"✅ **BAŞARILI!**\n\n🔑 Key: `{key}`\n💸 {cashback}₺ İade yapıldı!", uid, mid, reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ Bakiye yetersiz veya stok yok!", show_alert=True)

    elif call.data == "slot":
        if user[0] >= 10:
            db_query("UPDATE users SET balance = balance - 10 WHERE id=?", (uid,))
            d = bot.send_dice(uid, '🎰')
            time.sleep(3)
            if d.dice.value in [1, 22, 43, 64]:
                kazanc = 200 if datetime.datetime.now().hour == 20 else 100
                if user[1] == "VIP": kazanc += 50 # [VIP SLOT BONUSU]
                db_query("UPDATE users SET balance = balance + ? WHERE id=?", (kazanc, uid))
                bot.send_message(uid, f"🎊 **TEBRİKLER! {kazanc}₺ KAZANDIN!**")
            bot.send_message(uid, "Menüye Dön:", reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ 10₺ Bakiye lazım!", show_alert=True)

    elif call.data == "admin_p" and uid == ADMIN_ID:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("👥 KULLANICI YÖNET", callback_data="adm_user_find"),
                   InlineKeyboardButton("📦 STOK EKLE", callback_data="adm_add_stok"))
        markup.add(InlineKeyboardButton("📢 DUYURU GÖNDER", callback_data="adm_bc"),
                   InlineKeyboardButton("💾 YEDEK AL", callback_data="backup"))
        markup.add(InlineKeyboardButton("⬅️ GERİ", callback_data="home"))
        bot.edit_message_text("👑 **GELİŞMİŞ PANEL**", uid, mid, reply_markup=markup)

    elif call.data == "adm_user_find":
        m = bot.send_message(uid, "Yöneteceğiniz kullanıcının ID'sini yazın:")
        bot.register_next_step_handler(m, admin_user_control)

    elif call.data == "adm_add_stok":
        m = bot.send_message(uid, "Keyleri virgülle ayırarak atın (Örn: key1, key2):")
        bot.register_next_step_handler(m, admin_add_stok_process)

    # ... (Onay, Daily, Top, Inv butonları bir öncekiyle aynı mantıkta devam eder)

# --- [ 🛠️ ADMİN İŞLEMLERİ ] ---
def admin_user_control(message):
    target = message.text.strip()
    res = db_query("SELECT name, balance, status FROM users WHERE id=?", (target,), fetch=True)
    if res:
        mk = InlineKeyboardMarkup()
        mk.add(InlineKeyboardButton("+100₺ Ver", callback_data=f"adm_give_100_{target}"),
               InlineKeyboardButton("VIP Yap", callback_data=f"adm_make_vip_{target}"))
        bot.send_message(ADMIN_ID, f"👤 {res[0][0]}\n💰 Bakiye: {res[0][1]}₺\n💎 Durum: {res[0][2]}", reply_markup=mk)
    else: bot.send_message(ADMIN_ID, "Kullanıcı bulunamadı.")

def admin_add_stok_process(message):
    keys = [k.strip() for k in message.text.split(",")]
    for k in keys: db_query("INSERT OR IGNORE INTO stock VALUES (?)", (k,))
    bot.send_message(ADMIN_ID, f"✅ {len(keys)} Adet Stok Eklendi!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_quick_actions(call):
    data = call.data.split("_")
    if "give" in data:
        db_query("UPDATE users SET balance = balance + 100 WHERE id=?", (data[3],))
        bot.answer_callback_query(call.id, "100₺ Eklendi.")
    elif "make" in data:
        db_query("UPDATE users SET status = 'VIP' WHERE id=?", (data[3],))
        bot.answer_callback_query(call.id, "Artık VIP.")

# --- [ 🛡️ START & DEKONT ] ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = message.chat.id
    if not db_query("SELECT id FROM users WHERE id=?", (uid,), fetch=True):
        args = message.text.split()
        ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        db_query("INSERT INTO users (id, name, balance, ref_by) VALUES (?, ?, 15.0, ?)", (uid, message.from_user.first_name, ref))
    bot.send_message(uid, f"🔱 **{MARKA_ADI} HOŞGELDİN!**", reply_markup=get_main_menu(uid))

@bot.message_handler(content_types=['photo'])
def receipt_handler(message):
    if message.chat.id == ADMIN_ID: return
    mk = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (+350₺)", callback_data=f"confirm_{message.chat.id}"))
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(ADMIN_ID, f"🕵️ DEKONT GELDİ\nID: `{message.chat.id}`", reply_markup=mk)
    bot.reply_to(message, "⏳ İletildi, patron bakıyor.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_payment(call):
    tid = int(call.data.split("_")[1])
    db_query("UPDATE users SET balance = balance + 350 WHERE id=?", (tid,))
    bot.send_message(tid, "✅ **ÖDEMENİZ ONAYLANDI! 350₺ YÜKLENDİ.**")
    bot.delete_message(ADMIN_ID, call.message.message_id)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
    
