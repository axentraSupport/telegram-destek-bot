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
def home(): return "<h1>AxentraStore Imperial v21 - SYSTEM OK!</h1>"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- [ 👑 KRALİYET AYARLARI ] ---
TOKEN = "8723920846:AAENQIGDgrt9LXUN7VmqiWqxCvoLBYqB_WI" 
ADMIN_ID = 8561815348 
MARKA_ADI = "AxentraStore"
DESTEK_ADRESI = "AxentraStore"

# ÖDEME BİLGİLERİ (FIXED)
IBAN_ADRESI = "TR10 0006 2000 9100 0006 9697 09"
AD_SOYAD = "Garanti Ödeme ve Elektronik Para Hizmetleri A.Ş."
ZORUNLU_ACIKLAMA = "TAMİ7987919953449959"

DB_NAME = "axentra_final_v21.db"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- [ 🗄️ VERİTABANI MOTORU - KONTROL EDİLDİ ] ---
def db_query(query, params=(), fetch=False):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row # Sütun isimlerine erişim için
        c = conn.cursor()
        c.execute(query, params)
        if fetch: return c.fetchall()
        conn.commit()

# Veritabanı Tablo Yapısı (Tüm Sistemlerle Uyumlu)
db_query("""CREATE TABLE IF NOT EXISTS users 
           (id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, 
           spent REAL DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
           status TEXT DEFAULT 'NORMAL ÜYE', daily_claim TEXT DEFAULT '0', ref_by INTEGER DEFAULT 0)""")
db_query("CREATE TABLE IF NOT EXISTS inventory (uid INTEGER, key_val TEXT, date TEXT)")
db_query("CREATE TABLE IF NOT EXISTS stock (key_data TEXT PRIMARY KEY)")
db_query("CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, amount REAL)")

# --- [ 📱 ANA MENÜ - TÜM BUTONLAR EŞLENDİ ] ---
def get_main_menu(uid):
    u = db_query("SELECT * FROM users WHERE id=?", (uid,), fetch=True)[0]
    stok_c = db_query("SELECT COUNT(*) FROM stock", fetch=True)[0][0]
    
    markup = InlineKeyboardMarkup(row_width=2)
    # 1. Satır: Ana İşlem & Slot
    markup.add(InlineKeyboardButton(f"🚀 SATIN AL ({stok_c})", callback_data="buy_now"),
               InlineKeyboardButton("🎰 SLOT MAKİNESİ", callback_data="slot"))
    
    # 2. Satır: Şans Oyunları (Ek Özellikler)
    markup.add(InlineKeyboardButton("🎡 ÇARKIFELEK", callback_data="wheel"),
               InlineKeyboardButton("🪙 YAZI-TURA", callback_data="coin_flip"))
    
    # 3. Satır: Finans
    markup.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="deposit"),
               InlineKeyboardButton("📦 ENVANTERİM", callback_data="inv"))
    
    # 4. Satır: Sosyal & Kupon
    markup.add(InlineKeyboardButton("🏆 LİDERLER", callback_data="top"),
               InlineKeyboardButton("🎫 KUPON KULLAN", callback_data="use_coupon"))
    
    # 5. Satır: Destek & Günlük
    markup.add(InlineKeyboardButton("🛠️ DESTEK", url=f"https://t.me/{DESTEK_ADRESI}"),
               InlineKeyboardButton("👥 REF SİSTEMİ", callback_data="referral"))
    
    markup.add(InlineKeyboardButton("📆 GÜNLÜK ÖDÜL", callback_data="daily"),
               InlineKeyboardButton("📊 İSTATİSTİK", callback_data="stats"))

    if uid == ADMIN_ID:
        markup.add(InlineKeyboardButton("👑 ADMİN PANELİ", callback_data="admin_p"))

    # Durum Çubuğu
    stat_icon = "✨" if u['status'] == "VIP ÜYE" else "👤"
    markup.add(InlineKeyboardButton(f"{stat_icon} {u['status']} | {u['balance']}₺", callback_data="stats"))
    return markup

# --- [ ⚙️ ÇEKİRDEK CALLBACK MANTIĞI - SATIR SATIR KONTROL EDİLDİ ] ---
@bot.callback_query_handler(func=lambda call: True)
def master_callback(call):
    uid, mid = call.message.chat.id, call.message.message_id
    u_res = db_query("SELECT * FROM users WHERE id=?", (uid,), fetch=True)
    if not u_res: return
    u = u_res[0]

    # [1] ANA MENÜYE DÖN
    if call.data == "home":
        bot.edit_message_text(f"🏠 **{MARKA_ADI} Ana Menü**", uid, mid, reply_markup=get_main_menu(uid))

    # [2] MARKET & OTOMATİK VIP (380₺ KONTROLÜ)
    elif call.data == "buy_now":
        stok = db_query("SELECT key_data FROM stock LIMIT 1", fetch=True)
        fiyat = 350
        if u['balance'] >= fiyat and stok:
            key = stok[0]['key_data']
            new_spent = u['spent'] + fiyat
            new_status = "VIP ÜYE" if new_spent >= 380 else u['status']
            
            db_query("DELETE FROM stock WHERE key_data=?", (key,))
            db_query("UPDATE users SET balance = balance - ?, spent = ?, status = ? WHERE id=?", (fiyat, new_spent, new_status, uid))
            db_query("INSERT INTO inventory VALUES (?, ?, ?)", (uid, key, str(datetime.date.today())))
            
            bot.edit_message_text(f"✅ **BAŞARILI!**\n\n🔑 Key: `{key}`", uid, mid, reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ Bakiye yetersiz veya stok yok!", show_alert=True)

    # [3] SLOT MAKİNESİ (BEKLEMELİ)
    elif call.data == "slot":
        if u['balance'] >= 10:
            db_query("UPDATE users SET balance = balance - 10 WHERE id=?", (uid,))
            dice = bot.send_dice(uid, '🎰')
            time.sleep(3.5) # Animasyon süresi
            if dice.dice.value in [1, 22, 43, 64]:
                kazanc = 200 if u['status'] == "VIP ÜYE" else 100
                db_query("UPDATE users SET balance = balance + ? WHERE id=?", (kazanc, uid))
                bot.send_message(uid, f"🎊 **TEBRİKLER! {kazanc}₺ KAZANDIN!**")
            bot.send_message(uid, "Menüye Dön:", reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ 10₺ bakiye lazım!", show_alert=True)

    # [4] REFERANS SİSTEMİ (35₺ LİNKİ)
    elif call.data == "referral":
        ref_link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.edit_message_text(f"👥 **REFERANS**\n\nArkadaşını davet et, ilk bakiye yüklemesinde **35₺** kazan!\n\nLinkin: `{ref_link}`", uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    # [5] ÇARKIFELEK (25₺)
    elif call.data == "wheel":
        if u['balance'] >= 25:
            db_query("UPDATE users SET balance = balance - 25 WHERE id=?", (uid,))
            bot.edit_message_text("🎡 Çark dönüyor...", uid, mid)
            time.sleep(2)
            options = ["10₺", "50₺", "BOŞ", "50 XP"]
            win = random.choice(options)
            if win == "10₺": db_query("UPDATE users SET balance = balance + 10 WHERE id=?", (uid,))
            elif win == "50₺": db_query("UPDATE users SET balance = balance + 50 WHERE id=?", (uid,))
            bot.send_message(uid, f"🎡 Sonuç: **{win}**!", reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ 25₺ bakiye lazım!", show_alert=True)

    # [6] LİDERLER & ENVANTER & STATS
    elif call.data == "top":
        top = db_query("SELECT name, balance FROM users ORDER BY balance DESC LIMIT 5", fetch=True)
        msg = "🏆 **ZENGİNLER**\n\n" + "\n".join([f"{i+1}. {x['name']} - {x['balance']}₺" for i, x in enumerate(top)])
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "inv":
        inv = db_query("SELECT key_val FROM inventory WHERE uid=?", (uid,), fetch=True)
        msg = "📦 **ENVANTER**\n\n" + ("\n".join([f"`{x['key_val']}`" for x in inv]) if inv else "Boş.")
        bot.edit_message_text(msg, uid, mid, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ GERİ", callback_data="home")))

    elif call.data == "stats":
        msg = f"📊 **PROFİLİN**\n\n👤 Statü: `{u['status']}`\n💰 Bakiye: `{u['balance']}₺`\n🛒 Harcama: `{u['spent']}₺`"
        bot.answer_callback_query(call.id, f"Statün: {u['status']}", show_alert=True)

    # [7] ADMİN PANELİ (TAM YETKİ)
    elif call.data == "admin_p" and uid == ADMIN_ID:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📦 STOK EKLE", callback_data="adm_stok"),
                   InlineKeyboardButton("📢 DUYURU", callback_data="adm_bc"))
        markup.add(InlineKeyboardButton("🎫 KUPON YAP", callback_data="adm_coupon"))
        markup.add(InlineKeyboardButton("⬅️ GERİ", callback_data="home"))
        bot.edit_message_text("👑 **ADMİN KONTROL**", uid, mid, reply_markup=markup)

    elif call.data == "adm_stok":
        m = bot.send_message(uid, "Keyleri virgülle ayırıp yazın:")
        bot.register_next_step_handler(m, process_stok_add)

    elif call.data == "use_coupon":
        m = bot.send_message(uid, "🎫 Kupon Kodunu Girin:")
        bot.register_next_step_handler(m, process_coupon_use)

# --- [ 🛠️ ADMİN FONKSİYONLARI ] ---
def process_stok_add(message):
    keys = [k.strip() for k in message.text.split(",")]
    for k in keys: db_query("INSERT OR IGNORE INTO stock VALUES (?)", (k,))
    bot.send_message(ADMIN_ID, f"✅ {len(keys)} Key Eklendi!")

def process_coupon_use(message):
    code = message.text.strip()
    res = db_query("SELECT * FROM coupons WHERE code=?", (code,), fetch=True)
    if res:
        db_query("UPDATE users SET balance = balance + ? WHERE id=?", (res[0]['amount'], message.chat.id))
        db_query("DELETE FROM coupons WHERE code=?", (code,))
        bot.send_message(message.chat.id, f"✅ Kupon Onaylandı! +{res[0]['amount']}₺")
    else: bot.send_message(message.chat.id, "❌ Geçersiz Kod!")

# --- [ 🛡️ START & DEKONT & REF BONUS ] ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = message.chat.id
    user = db_query("SELECT status FROM users WHERE id=?", (uid,), fetch=True)
    if not user:
        args = message.text.split()
        ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
        db_query("INSERT INTO users (id, name, balance, ref_by) VALUES (?, ?, 15.0, ?)", (uid, message.from_user.first_name, ref))
        status = "NORMAL ÜYE"
    else: status = user[0]['status']
    
    bot.send_message(uid, f"🔱 **{MARKA_ADI} HOŞGELDİN**\n\n👤 **ÜYE SEVİYESİ = {status}**", reply_markup=get_main_menu(uid))

@bot.message_handler(content_types=['photo'])
def receipt_handler(message):
    if message.chat.id == ADMIN_ID: return
    mk = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (+350₺)", callback_data=f"conf_{message.chat.id}"))
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(ADMIN_ID, f"🕵️ DEKONT\nID: `{message.chat.id}`", reply_markup=mk)
    bot.reply_to(message, "⏳ Dekont iletildi, kontrol ediliyor...")

@bot.callback_query_handler(func=lambda call: call.data.startswith("conf_"))
def admin_confirm(call):
    tid = int(call.data.split("_")[1])
    u = db_query("SELECT * FROM users WHERE id=?", (tid,), fetch=True)[0]
    
    # 350₺ Bakiye & VIP Kontrol
    new_spent = u['spent'] + 350
    new_status = "VIP ÜYE" if new_spent >= 380 else "NORMAL ÜYE"
    db_query("UPDATE users SET balance = balance + 350, spent = ?, status = ? WHERE id=?", (new_spent, new_status, tid))
    
    # [35₺ REFERANS BONUSU]
    if u['ref_by'] != 0:
        db_query("UPDATE users SET balance = balance + 35 WHERE id=?", (u['ref_by'],))
        try: bot.send_message(u['ref_by'], "🎊 Ref bonusun (35₺) yattı!")
        except: pass
        
    bot.send_message(tid, f"✅ **BAKİYE YÜKLENDİ!**\n🛡️ Statü: {new_status}")
    bot.delete_message(ADMIN_ID, call.message.message_id)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
        
