import telebot, sqlite3, time, threading, os, random, string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# --- 🌐 WEB SERVER (RENDER İÇİN) ---
app = Flask(__name__)
@app.route('/')
def home(): return "AXENTRA V5000 FINAL BOSS IS ONLINE 🚀"

def run_flask(): 
    app.run(host='0.0.0.0', port=8080)

# --- 👑 KRİTİK AYARLAR (ID SABİTLENDİ) ---
TOKEN = "8723920846:AAEVvBVge4VRrEmzGPcmBmYd9LlFqZvoNz4"
ADMIN = 8561815348 # Senin verdiğin kesin ID kanka
ALICI_AD = "Garanti Ödeme ve Elektronik Para Hizmetleri A.Ş."
ACIKLAMA_KODU = "TAMİ7987919953449959"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- 🗄️ DATABASE MOTORU ---
def db_exe(q, p=(), f=0):
    with sqlite3.connect("axentra_final_boss.db", timeout=30) as conn:
        cur = conn.cursor()
        cur.execute(q, p)
        if f: return cur.fetchall()
        conn.commit()

# Tablo Kurulumları
db_exe("CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, balance REAL DEFAULT 100, xp INT DEFAULT 0, spent REAL DEFAULT 0, ref_by INT DEFAULT 0)")
db_exe("CREATE TABLE IF NOT EXISTS stock (k TEXT UNIQUE)") 
db_exe("CREATE TABLE IF NOT EXISTS inv (uid INT, k TEXT)")
db_exe("CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, amount REAL, uses INT)")

# 🔑 OTOMATİK 100 STOK ÜRETİMİ
if not db_exe("SELECT k FROM stock", f=1):
    for _ in range(100):
        k = "AX-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db_exe("INSERT OR IGNORE INTO stock (k) VALUES (?)", (k,))

# --- 📱 ANA MENÜ FONKSİYONU ---
def main_menu(id):
    u = db_exe("SELECT balance, xp FROM users WHERE id=?", (id,), 1)[0]
    st = len(db_exe("SELECT k FROM stock", f=1))
    m = InlineKeyboardMarkup(row_width=2)
    m.add(InlineKeyboardButton(f"🚀 SATIN AL (350₺) [Stok: {st}]", callback_data="buy"))
    m.add(InlineKeyboardButton("🎰 SLOT", callback_data="g_slot"), 
          InlineKeyboardButton("🔴 RULET", callback_data="g_roul"))
    m.add(InlineKeyboardButton("🪙 YAZI-TURA", callback_data="g_coin"), 
          InlineKeyboardButton("🎡 ÇARKIFELEK", callback_data="g_wheel"))
    m.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="dep"), 
          InlineKeyboardButton("📦 ENVANTER", callback_data="inv"))
    m.add(InlineKeyboardButton("👥 REFERANS", callback_data="ref"), 
          InlineKeyboardButton("🎫 KUPON KULLAN", callback_data="coupon_btn"))
    
    # 🚨 ADMİN PANELİ GÖRÜNÜRLÜK KONTROLÜ
    if int(id) == int(ADMIN):
        m.add(InlineKeyboardButton("👑 ADMİN PANELİ 👑", callback_data="admin_panel"))
    
    m.add(InlineKeyboardButton(f"💵 {u[0]}₺ | ✨ {u[1]} XP", callback_data="stats"))
    return m

# --- 🛡️ START & REFERANS ---
@bot.message_handler(commands=['start'])
def welcome(m):
    uid = m.chat.id
    ref_id = 0
    if len(m.text.split()) > 1:
        p_ref = m.text.split()[1]
        if p_ref.isdigit() and int(p_ref) != uid: ref_id = int(p_ref)

    if not db_exe("SELECT id FROM users WHERE id=?", (uid,), 1):
        db_exe("INSERT INTO users (id, balance, ref_by) VALUES (?,?,?)", (uid, 100.0, ref_id))
        if ref_id != 0: bot.send_message(ref_id, "👥 **Tebrikler!** Linkinle yeni bir üye katıldı.")
    
    bot.send_message(uid, "🔱 **Axentra Store V5000**\nSistem kusursuz hale getirildi!", reply_markup=main_menu(uid))

# --- ⚙️ MASTER CALLBACK HANDLER (TÜM BUTONLAR) ---
@bot.callback_query_handler(func=lambda c: True)
def master_callback(c):
    uid = c.message.chat.id
    bot.answer_callback_query(c.id)
    u_data = db_exe("SELECT balance, ref_by FROM users WHERE id=?", (uid,), 1)[0]
    bal, ref_id = u_data

    # --- 🕹️ OYUNLAR ---
    if c.data == "g_coin":
        m = InlineKeyboardMarkup().add(InlineKeyboardButton("🪙 YAZI", callback_data="yt_y"), InlineKeyboardButton("🪙 TURA", callback_data="yt_t"))
        bot.send_message(uid, "🪙 **Bahis: 100₺**\nTarafını seç:", reply_markup=m)

    elif c.data.startswith("yt_"):
        if bal < 100: return bot.send_message(uid, "❌ Bakiye yetersiz.")
        secim = "yazi" if c.data == "yt_y" else "tura"
        sonuc = random.choice(["yazi", "tura"])
        db_exe("UPDATE users SET balance = balance - 100 WHERE id=?", (uid,))
        if secim == sonuc:
            db_exe("UPDATE users SET balance = balance + 200 WHERE id=?", (uid,))
            bot.send_message(uid, f"🪙 **{sonuc.upper()}** geldi! +200₺ Kazandın! 🔥")
        else: bot.send_message(uid, f"🪙 **{sonuc.upper()}** geldi. Kaybettin! 💀")

    elif c.data == "g_roul":
        m = InlineKeyboardMarkup().add(InlineKeyboardButton("🔴 KIRMIZI", callback_data="rl_r"), InlineKeyboardButton("⚫️ SİYAH", callback_data="rl_b"))
        bot.send_message(uid, "🔴 **Rulet (100₺)**\nRenk seç:", reply_markup=m)

    elif c.data.startswith("rl_"):
        if bal < 100: return bot.send_message(uid, "❌ Bakiye yetersiz.")
        bet = "red" if c.data == "rl_r" else "black"
        win = random.choice(["red", "black"])
        db_exe("UPDATE users SET balance = balance - 100 WHERE id=?", (uid,))
        if bet == win:
            db_exe("UPDATE users SET balance = balance + 200 WHERE id=?", (uid,))
            bot.send_message(uid, f"🎡 Top **{win.upper()}** üzerinde! +200₺ Kazandın! 🔥")
        else: bot.send_message(uid, f"🎡 Top **{win.upper()}** üzerinde. Kaybettin! 💀")

    elif c.data == "g_wheel":
        if bal < 50: return bot.send_message(uid, "❌ 50₺ lazım!")
        db_exe("UPDATE users SET balance = balance - 50 WHERE id=?", (uid,))
        odul = random.choices([0, 20, 100, 500], weights=[65, 20, 12, 3])[0]
        db_exe("UPDATE users SET balance = balance + ? WHERE id=?", (odul, uid))
        bot.send_message(uid, f"🎡 Çark döndü: **{odul}₺** kazandın!")

    elif c.data == "g_slot":
        if bal < 50: return bot.send_message(uid, "❌ 50₺ lazım!")
        em = ["🍒", "💎", "7️⃣", "🔔"]
        res = [random.choice(em) for _ in range(3)]
        db_exe("UPDATE users SET balance = balance - 50 WHERE id=?", (uid,))
        if res[0] == res[1] == res[2]:
            db_exe("UPDATE users SET balance = balance + 750 WHERE id=?", (uid,))
            bot.send_message(uid, f"🎰 | {res[0]} | {res[1]} | {res[2]} |\n🔥 JACKPOT! +750₺")
        else: bot.send_message(uid, f"🎰 | {res[0]} | {res[1]} | {res[2]} |\n💀 Kaybettin.")

    # --- 🚨 DİĞER BUTONLAR ---
    elif c.data == "admin_panel" and int(uid) == int(ADMIN):
        m = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 ANA MENÜ", callback_data="back_home"))
        bot.edit_message_text("🚨 **ADMIN PANELİ**\n\nKomutlar:\n- `/ver ID Miktar` (Bakiye)\n- `/kupon KOD Miktar Adet` (Kupon)\n- `/duyuru MESAJ` (Global)", uid, c.message.message_id, reply_markup=m)

    elif c.data == "back_home":
        bot.edit_message_text("🔱 **Axentra Store** Ana Menü", uid, c.message.message_id, reply_markup=main_menu(uid))

    elif c.data == "dep":
        bot.send_message(uid, f"🏦 **IBAN:** `TR10 0006 2000 9100 0006 9697 09` \n👤 `{ALICI_AD}`\n📝 Açıklama: `{ACIKLAMA_KODU}`\n📸 Dekont at kanka.")

    elif c.data == "buy":
        st = db_exe("SELECT k FROM stock LIMIT 1", f=1)
        if not st: return bot.send_message(uid, "❌ Stok yok!")
        if bal < 350: return bot.send_message(uid, "❌ 350₺ lazım.")
        key = st[0][0]
        db_exe("DELETE FROM stock WHERE k=?", (key,))
        db_exe("UPDATE users SET balance=balance-350, spent=spent+350 WHERE id=?", (uid,))
        db_exe("INSERT INTO inv VALUES (?,?)", (uid, key))
        if ref_id != 0:
            db_exe("UPDATE users SET balance=balance+50 WHERE id=?", (ref_id,))
            bot.send_message(ref_id, "💰 Referansın alışveriş yaptı! +50₺ kazandın.")
        bot.send_message(uid, f"✅ Satın Alındı!\n📦 Keyin: `{key}`")

    elif c.data == "inv":
        inv = db_exe("SELECT k FROM inv WHERE uid=?", (uid,), 1)
        bot.send_message(uid, "📦 **Envanterin:**\n" + ("\n".join([f"`{x[0]}`" for x in inv]) if inv else "Boş."))

    elif c.data == "ref":
        bot.send_message(uid, f"👥 **Referans Linkin:**\n`https://t.me/{(bot.get_me().username)}?start={uid}`")

    elif c.data == "coupon_btn":
        bot.send_message(uid, "🎫 Kupon kodunu `/kupon KOD` şeklinde yazıp gönder.")

# --- ⌨️ METİN KOMUTLARI ---
@bot.message_handler(func=lambda m: True)
def text_commands(m):
    uid, text = m.chat.id, m.text
    if text.startswith("/kupon"):
        if uid == ADMIN and len(text.split()) > 2: # Kupon Oluşturma
            try:
                _, code, amt, uses = text.split()
                db_exe("INSERT INTO coupons VALUES (?,?,?)", (code.upper(), float(amt), int(uses)))
                bot.send_message(ADMIN, f"🎫 Kupon `{code}` başarıyla eklendi.")
            except: pass
        else: # Kupon Kullanma
            try:
                code = text.split()[1].upper()
                res = db_exe("SELECT amount, uses FROM coupons WHERE code=?", (code,), 1)
                if res and res[0][1] > 0:
                    db_exe("UPDATE coupons SET uses=uses-1 WHERE code=?", (code,))
                    db_exe("UPDATE users SET balance=balance+? WHERE id=?", (res[0][0], uid))
                    bot.send_message(uid, f"✅ Kupon kabul edildi! +{res[0][0]}₺")
                else: bot.send_message(uid, "❌ Geçersiz veya bitmiş kupon.")
            except: pass

    elif uid == ADMIN and text.startswith("/ver"):
        try:
            _, tid, amt = text.split()
            db_exe("UPDATE users SET balance=balance+? WHERE id=?", (float(amt), tid))
            bot.send_message(ADMIN, f"✅ {tid} ID'sine {amt}₺ verildi.")
            bot.send_message(int(tid), f"💰 Hesabınıza {amt}₺ bakiye eklendi!")
        except: pass

# --- 📸 DEKONT SİSTEMİ ---
@bot.message_handler(content_types=['photo'])
def handle_receipt(m):
    if m.chat.id == ADMIN: return
    btn = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (350₺)", callback_data=f"ok_{m.chat.id}"))
    bot.forward_message(ADMIN, m.chat.id, m.message_id)
    bot.send_message(ADMIN, f"🕵️ Yeni Dekont! ID: `{m.chat.id}`", reply_markup=btn)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_"))
def confirm(c):
    tid = c.data.split("_")[1]
    db_exe("UPDATE users SET balance=balance+350 WHERE id=?", (tid,))
    bot.send_message(int(tid), "✅ Ödemeniz onaylandı! Bakiyeniz yüklendi.")
    bot.edit_message_text(f"✅ {tid} onaylandı.", ADMIN, c.message.message_id)

# --- 🚀 RUN ---
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    while True:
        try: bot.infinity_polling(timeout=30)
        except: time.sleep(5)
                            
