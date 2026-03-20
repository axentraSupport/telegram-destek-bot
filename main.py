import telebot, sqlite3, time, threading, os, random, string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# --- 🌐 SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "AXENTRA V7000 FINAL BOSS IS ONLINE 🚀"

def run_flask(): 
    app.run(host='0.0.0.0', port=8080)

# --- 👑 AYARLAR ---
TOKEN = "8723920846:AAEVvBVge4VRrEmzGPcmBmYd9LlFqZvoNz4"
ADMIN = 8561815348 
ALICI_AD = "Garanti Ödeme ve Elektronik Para Hizmetleri A.Ş."
ACIKLAMA_KODU = "TAMİ7987919953449959"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- 🗄️ DATABASE MOTORU (GÜÇLENDİRİLMİŞ) ---
def db_exe(q, p=(), f=0):
    db_path = "axentra_final_v7.db"
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        cur = conn.cursor()
        cur.execute(q, p)
        if f: return cur.fetchall()
        conn.commit()
    except Exception as e: print(f"DB Hatası: {e}")
    finally: conn.close()

# Tabloları oluştur
db_exe("CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, balance REAL DEFAULT 100, xp INT DEFAULT 0, ref_by INT DEFAULT 0)")
db_exe("CREATE TABLE IF NOT EXISTS stock (k TEXT UNIQUE)") 
db_exe("CREATE TABLE IF NOT EXISTS inv (uid INT, k TEXT)")
db_exe("CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, amount REAL, uses INT)")

# Stok kontrolü (Yoksa 100 tane ekle)
if not db_exe("SELECT k FROM stock", f=1):
    for _ in range(100):
        k = "AX-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db_exe("INSERT OR IGNORE INTO stock (k) VALUES (?)", (k,))

# --- 📱 ANA MENÜ ---
def main_menu(id):
    u_data = db_exe("SELECT balance, xp FROM users WHERE id=?", (id,), 1)
    if not u_data:
        db_exe("INSERT OR IGNORE INTO users (id, balance) VALUES (?,?)", (id, 100.0))
        u_data = [(100.0, 0)]
    
    bal, xp = u_data[0]
    st = len(db_exe("SELECT k FROM stock", f=1))
    
    m = InlineKeyboardMarkup(row_width=2)
    m.add(InlineKeyboardButton(f"🚀 SATIN AL (350₺) [Stok: {st}]", callback_data="buy"))
    m.add(InlineKeyboardButton("🎰 SLOT", callback_data="g_slot"), InlineKeyboardButton("🔴 RULET", callback_data="g_roul"))
    m.add(InlineKeyboardButton("🪙 YAZI-TURA", callback_data="g_coin"), InlineKeyboardButton("🎡 ÇARKIFELEK", callback_data="g_wheel"))
    m.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="dep"), InlineKeyboardButton("📦 ENVANTER", callback_data="inv"))
    m.add(InlineKeyboardButton("👥 REFERANS", callback_data="ref"), InlineKeyboardButton("🎫 KUPON KULLAN", callback_data="coupon_btn"))
    
    if int(id) == int(ADMIN):
        m.add(InlineKeyboardButton("👑 ADMİN PANELİ 👑", callback_data="admin_panel"))
    
    m.add(InlineKeyboardButton(f"💵 {bal}₺ | ✨ {xp} XP", callback_data="stats"))
    return m

# --- 🛡️ START ---
@bot.message_handler(commands=['start'])
def welcome(m):
    uid = m.chat.id
    ref_id = 0
    if len(m.text.split()) > 1:
        p_ref = m.text.split()[1]
        if p_ref.isdigit() and int(p_ref) != uid: ref_id = int(p_ref)

    # Kullanıcı varsa bakiyesine DOKUNMA, yoksa ekle
    if not db_exe("SELECT id FROM users WHERE id=?", (uid,), 1):
        db_exe("INSERT INTO users (id, balance, ref_by) VALUES (?,?,?)", (uid, 100.0, ref_id))
        if ref_id != 0: bot.send_message(ref_id, "👥 **Tebrikler!** Yeni bir referans kazandın.")
    
    bot.send_message(uid, "🔱 **Axentra Store V7000**\nBakiye ve Sistemler Sabitlendi!", reply_markup=main_menu(uid))

# --- ⚙️ MASTER CALLBACK ---
@bot.callback_query_handler(func=lambda c: True)
def master_callback(c):
    uid = c.message.chat.id
    bot.answer_callback_query(c.id)
    u_data = db_exe("SELECT balance, ref_by FROM users WHERE id=?", (uid,), 1)[0]
    bal, ref_id = u_data

    # --- 🕹️ OYUNLAR ---
    if c.data == "g_wheel":
        if bal < 50: return bot.send_message(uid, "❌ 50₺ lazım!")
        db_exe("UPDATE users SET balance = balance - 50 WHERE id=?", (uid,))
        win = random.choices([0, 20, 150, 600], weights=[60, 25, 12, 3])[0]
        db_exe("UPDATE users SET balance = balance + ? WHERE id=?", (win, uid))
        bot.send_message(uid, f"🎡 Çark döndü: **{win}₺** kazandın!", reply_markup=main_menu(uid))

    elif c.data == "g_slot":
        if bal < 50: return bot.send_message(uid, "❌ 50₺ lazım!")
        em = ["🍒", "💎", "7️⃣", "🔔"]
        res = [random.choice(em) for _ in range(3)]
        db_exe("UPDATE users SET balance = balance - 50 WHERE id=?", (uid,))
        is_win = res[0] == res[1] == res[2]
        if is_win: db_exe("UPDATE users SET balance = balance + 800 WHERE id=?", (uid,))
        bot.send_message(uid, f"🎰 | {res[0]} | {res[1]} | {res[2]} |\n" + ("🔥 **JACKPOT +800₺**" if is_win else "💀 Kaybettin."), reply_markup=main_menu(uid))

    elif c.data == "g_coin":
        m = InlineKeyboardMarkup().add(InlineKeyboardButton("🪙 YAZI", callback_data="yt_y"), InlineKeyboardButton("🪙 TURA", callback_data="yt_t"))
        bot.send_message(uid, "🪙 Tarafını seç (100₺):", reply_markup=m)

    elif c.data.startswith("yt_"):
        if bal < 100: return bot.send_message(uid, "❌ Yetersiz bakiye!")
        sec = "yazi" if c.data == "yt_y" else "tura"
        son = random.choice(["yazi", "tura"])
        db_exe("UPDATE users SET balance = balance - 100 WHERE id=?", (uid,))
        if sec == son:
            db_exe("UPDATE users SET balance = balance + 200 WHERE id=?", (uid,))
            bot.send_message(uid, f"🪙 **{son.upper()}** geldi! +200₺ Kazandın!", reply_markup=main_menu(uid))
        else: bot.send_message(uid, f"🪙 **{son.upper()}** geldi! Kaybettin.", reply_markup=main_menu(uid))

    elif c.data == "g_roul":
        m = InlineKeyboardMarkup().add(InlineKeyboardButton("🔴 KIRMIZI", callback_data="rl_r"), InlineKeyboardButton("⚫️ SİYAH", callback_data="rl_b"))
        bot.send_message(uid, "🔴 Rulet Renk Seç (100₺):", reply_markup=m)

    elif c.data.startswith("rl_"):
        if bal < 100: return bot.send_message(uid, "❌ Yetersiz bakiye!")
        bet, win = ("red" if c.data == "rl_r" else "black"), random.choice(["red", "black"])
        db_exe("UPDATE users SET balance = balance - 100 WHERE id=?", (uid,))
        if bet == win:
            db_exe("UPDATE users SET balance = balance + 200 WHERE id=?", (uid,))
            bot.send_message(uid, f"🎡 **{win.upper()}** geldi! +200₺ kazandın!", reply_markup=main_menu(uid))
        else: bot.send_message(uid, f"🎡 **{win.upper()}** geldi! Kaybettin.", reply_markup=main_menu(uid))

    # --- 🚨 DİĞERLERİ ---
    elif c.data == "admin_panel" and int(uid) == int(ADMIN):
        bot.send_message(ADMIN, "👑 ADMİN: `/ver ID Miktar` veya `/kupon KOD Miktar Adet` kullanabilirsin kanka.")

    elif c.data == "dep":
        bot.send_message(uid, f"🏦 **IBAN:** `TR10 0006 2000 9100 0006 9697 09` \n👤 `{ALICI_AD}`\n📝 Açıklama: `{ACIKLAMA_KODU}`\n📸 Dekont at.")

    elif c.data == "buy":
        st = db_exe("SELECT k FROM stock LIMIT 1", f=1)
        if not st: return bot.send_message(uid, "❌ Stok yok!")
        if bal < 350: return bot.send_message(uid, "❌ 350₺ lazım!")
        key = st[0][0]
        db_exe("DELETE FROM stock WHERE k=?", (key,))
        db_exe("UPDATE users SET balance = balance - 350 WHERE id=?", (uid,))
        db_exe("INSERT INTO inv VALUES (?,?)", (uid, key))
        if ref_id != 0:
            db_exe("UPDATE users SET balance = balance + 50 WHERE id=?", (ref_id,))
            bot.send_message(ref_id, "💰 Ref bonusu: +50₺!")
        bot.send_message(uid, f"✅ Keyin: `{key}`", reply_markup=main_menu(uid))

    elif c.data == "inv":
        inv = db_exe("SELECT k FROM inv WHERE uid=?", (uid,), 1)
        bot.send_message(uid, "📦 **Envanter:**\n" + ("\n".join([f"`{x[0]}`" for x in inv]) if inv else "Boş."))

    elif c.data == "ref":
        bot.send_message(uid, f"👥 **Referans Linkin:**\n`https://t.me/{(bot.get_me().username)}?start={uid}`")

    elif c.data == "coupon_btn":
        bot.send_message(uid, "🎫 `/kupon KOD` şeklinde yaz kanka.")

# --- ⌨️ KOMUTLAR ---
@bot.message_handler(func=lambda m: True)
def text_cmds(m):
    uid, text = m.chat.id, m.text
    if text.startswith("/kupon"):
        if uid == ADMIN and len(text.split()) > 2:
            _, c, a, u = text.split()
            db_exe("INSERT INTO coupons VALUES (?,?,?)", (c.upper(), float(a), int(u)))
            bot.send_message(ADMIN, "✅ Kupon eklendi.")
        else:
            try:
                code = text.split()[1].upper()
                res = db_exe("SELECT amount, uses FROM coupons WHERE code=?", (code,), 1)
                if res and res[0][1] > 0:
                    db_exe("UPDATE coupons SET uses = uses - 1 WHERE code=?", (code,))
                    db_exe("UPDATE users SET balance = balance + ? WHERE id=?", (res[0][0], uid))
                    bot.send_message(uid, f"✅ +{res[0][0]}₺ bakiye eklendi!", reply_markup=main_menu(uid))
                else: bot.send_message(uid, "❌ Geçersiz kupon.")
            except: pass

    elif uid == ADMIN and text.startswith("/ver"):
        try:
            _, tid, amt = text.split()
            db_exe("UPDATE users SET balance = balance + ? WHERE id=?", (float(amt), tid))
            bot.send_message(ADMIN, f"✅ {tid} nolu hesaba {amt}₺ verildi.")
            bot.send_message(int(tid), f"💰 Hesabınıza {amt}₺ bakiye eklendi!", reply_markup=main_menu(int(tid)))
        except: pass

# --- 📸 DEKONT ONAY ---
@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    if m.chat.id == ADMIN: return
    btn = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (350₺)", callback_data=f"ok_{m.chat.id}"))
    bot.forward_message(ADMIN, m.chat.id, m.message_id)
    bot.send_message(ADMIN, f"🕵️ Yeni Dekont! ID: `{m.chat.id}`", reply_markup=btn)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_"))
def confirm(c):
    tid = c.data.split("_")[1]
    db_exe("UPDATE users SET balance = balance + 350 WHERE id=?", (tid,))
    bot.send_message(int(tid), "✅ Ödemeniz onaylandı!", reply_markup=main_menu(int(tid)))
    bot.edit_message_text(f"✅ {tid} onaylandı.", ADMIN, c.message.message_id)

# --- 🚀 RUN ---
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    while True:
        try: bot.infinity_polling(timeout=30)
        except: time.sleep(5)
            
