import telebot, sqlite3, time, threading, os, random, string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# --- 🌐 SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "AXENTRA V11K FINAL BOSS IS ONLINE 🚀"

def run_flask(): 
    app.run(host='0.0.0.0', port=8080)

# --- 👑 KRİTİK AYARLAR ---
TOKEN = "8723920846:AAEVvBVge4VRrEmzGPcmBmYd9LlFqZvoNz4"
ADMIN = 8561815348 
CHANNEL_ID = -1003577335395 # <--- VIP KANAL ID'SİNİ BURAYA YAZ KANKA
ALICI_AD = "Garanti Ödeme ve Elektronik Para Hizmetleri A.Ş."
ACIKLAMA_KODU = "TAMİ7987919953449959"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- 🗄️ DATABASE MOTORU ---
def db_exe(q, p=(), f=0):
    db_path = "axentra_final_v11.db"
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        cur = conn.cursor()
        cur.execute(q, p)
        if f: return cur.fetchall()
        conn.commit()
    except Exception as e: print(f"DB Hatası: {e}")
    finally: conn.close()

# Tablolar
db_exe("CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, balance REAL DEFAULT 100, is_vip INT DEFAULT 0, xp INT DEFAULT 0, ref_by INT DEFAULT 0)")
db_exe("CREATE TABLE IF NOT EXISTS stock (k TEXT UNIQUE)") 
db_exe("CREATE TABLE IF NOT EXISTS inv (uid INT, k TEXT)")
db_exe("CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, amount REAL, uses INT)")

# Stok Otomasyonu
if not db_exe("SELECT k FROM stock", f=1):
    for _ in range(100):
        k = "AX-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db_exe("INSERT OR IGNORE INTO stock (k) VALUES (?)", (k,))

# --- 📱 ANA MENÜ ---
def main_menu(id):
    u_data = db_exe("SELECT balance, is_vip, xp FROM users WHERE id=?", (id,), 1)
    if not u_data:
        db_exe("INSERT OR IGNORE INTO users (id, balance) VALUES (?,?)", (id, 100.0))
        u_data = [(100.0, 0, 0)]
    
    bal, vip, xp = u_data[0]
    st = len(db_exe("SELECT k FROM stock", f=1))
    tag = "💎 VIP" if vip else "👤 ÜYE"
    
    m = InlineKeyboardMarkup(row_width=2)
    m.add(InlineKeyboardButton(f"🚀 VIP KEY SATIN AL (350₺) [Stok: {st}]", callback_data="buy"))
    m.add(InlineKeyboardButton("🎰 SLOT", callback_data="g_slot"), InlineKeyboardButton("🔴 RULET", callback_data="g_roul"))
    m.add(InlineKeyboardButton("🪙 YAZI-TURA", callback_data="g_coin"), InlineKeyboardButton("🎡 ÇARKIFELEK", callback_data="g_wheel"))
    m.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="dep"), InlineKeyboardButton("📦 ENVANTER", callback_data="inv"))
    m.add(InlineKeyboardButton("👥 REFERANS", callback_data="ref"), InlineKeyboardButton("🎫 KUPON KULLAN", callback_data="coupon_btn"))
    
    if int(id) == int(ADMIN):
        m.add(InlineKeyboardButton("👑 ADMİN PANELİ 👑", callback_data="admin_panel"))
    
    m.add(InlineKeyboardButton(f"💵 {bal}₺ | {tag} | ✨ {xp} XP", callback_data="stats"))
    return m

# --- 🛡️ START ---
@bot.message_handler(commands=['start'])
def welcome(m):
    uid = m.chat.id
    ref_id = 0
    if len(m.text.split()) > 1:
        p_ref = m.text.split()[1]
        if p_ref.isdigit() and int(p_ref) != uid: ref_id = int(p_ref)

    if not db_exe("SELECT id FROM users WHERE id=?", (uid,), 1):
        db_exe("INSERT INTO users (id, balance, ref_by) VALUES (?,?,?)", (uid, 100.0, ref_id))
        if ref_id != 0: bot.send_message(ref_id, "👥 **Tebrikler!** Yeni bir referans kazandın.")
    
    bot.send_message(uid, "🔱 **Axentra Ultimate V11**\nHoş geldin kral! Tüm sistemler aktif.", reply_markup=main_menu(uid))

# --- ⚙️ MASTER CALLBACK ---
@bot.callback_query_handler(func=lambda c: True)
def master_callback(c):
    uid, data = c.message.chat.id, c.data
    bot.answer_callback_query(c.id)
    u_data = db_exe("SELECT balance, is_vip, ref_by FROM users WHERE id=?", (uid,), 1)[0]
    bal, is_vip, ref_id = u_data

    # --- 💎 VIP KANAL & KEY SİSTEMİ ---
    if data == "inv":
        inv = db_exe("SELECT k FROM inv WHERE uid=?", (uid,), 1)
        if not inv: return bot.send_message(uid, "📦 Envanterin boş kanka.")
        m = InlineKeyboardMarkup()
        for x in inv:
            m.add(InlineKeyboardButton(f"🔑 {x[0]} (KANALA KATIL)", callback_data=f"join_{x[0]}"))
        bot.send_message(uid, "📦 **VIP Keylerin:**\nKanala giriş linki için keye tıkla:", reply_markup=m)

    elif data.startswith("join_"):
        key = data.replace("join_", "")
        try:
            link = bot.create_chat_invite_link(CHANNEL_ID, member_limit=1, expire_date=int(time.time())+3600).invite_link
            db_exe("DELETE FROM inv WHERE uid=? AND k=?", (uid, key))
            db_exe("UPDATE users SET is_vip = 1 WHERE id=?", (uid,))
            bot.send_message(uid, f"🎉 **VIP KANAL ERİŞİMİ!**\n\n🔑 Key: `{key}`\n🔗 Davet Linkin: {link}\n\n*Link 1 kişiliktir ve 1 saat geçerlidir!*", reply_markup=main_menu(uid))
        except:
            bot.send_message(uid, "❌ Hata: Botun kanalda admin olduğundan ve CHANNEL_ID'nin doğruluğundan emin ol!")

    # --- 🕹️ OYUNLAR (VIP ŞANSI DAHİL) ---
    elif data == "g_wheel":
        if bal < 50: return bot.send_message(uid, "❌ 50₺ lazım!")
        db_exe("UPDATE users SET balance = balance - 50 WHERE id=?", (uid,))
        w = [60, 25, 12, 3] if not is_vip else [40, 40, 15, 5]
        win = random.choices([0, 25, 150, 800], weights=w)[0]
        db_exe("UPDATE users SET balance = balance + ? WHERE id=?", (win, uid))
        bot.send_message(uid, f"🎡 Çark döndü: **{win}₺** kazandın!", reply_markup=main_menu(uid))

    elif data == "g_slot":
        if bal < 50: return bot.send_message(uid, "❌ 50₺ lazım!")
        em = ["🍒", "💎", "7️⃣", "🔔"]
        res = [random.choice(em) for _ in range(3)]
        db_exe("UPDATE users SET balance = balance - 50 WHERE id=?", (uid,))
        is_win = res[0] == res[1] == res[2]
        if is_win: db_exe("UPDATE users SET balance = balance + 1000 WHERE id=?", (uid,))
        bot.send_message(uid, f"🎰 | {res[0]} | {res[1]} | {res[2]} |\n" + ("🔥 **JACKPOT +1000₺**" if is_win else "💀 Kaybettin."), reply_markup=main_menu(uid))

    elif data.startswith("yt_") or data == "g_coin":
        if data == "g_coin":
            m = InlineKeyboardMarkup().add(InlineKeyboardButton("🪙 YAZI", callback_data="yt_y"), InlineKeyboardButton("🪙 TURA", callback_data="yt_t"))
            return bot.send_message(uid, "🪙 Yazı mı Tura mı? (100₺):", reply_markup=m)
        if bal < 100: return bot.send_message(uid, "❌ 100₺ bakiye lazım!")
        sec, son = ("yazi" if data == "yt_y" else "tura"), random.choice(["yazi", "tura"])
        db_exe("UPDATE users SET balance = balance - 100 WHERE id=?", (uid,))
        if sec == son:
            db_exe("UPDATE users SET balance = balance + 200 WHERE id=?", (uid,))
            bot.send_message(uid, f"🪙 **{son.upper()}**! +200₺ kazandın!", reply_markup=main_menu(uid))
        else: bot.send_message(uid, f"🪙 **{son.upper()}**! Kaybettin.", reply_markup=main_menu(uid))

    elif data.startswith("rl_") or data == "g_roul":
        if data == "g_roul":
            m = InlineKeyboardMarkup().add(InlineKeyboardButton("🔴 KIRMIZI", callback_data="rl_r"), InlineKeyboardButton("⚫️ SİYAH", callback_data="rl_b"))
            return bot.send_message(uid, "🔴 Rulet Renk Seç (100₺):", reply_markup=m)
        if bal < 100: return bot.send_message(uid, "❌ 100₺ bakiye lazım!")
        bet, win = ("red" if data == "rl_r" else "black"), random.choice(["red", "black"])
        db_exe("UPDATE users SET balance = balance - 100 WHERE id=?", (uid,))
        if bet == win:
            db_exe("UPDATE users SET balance = balance + 200 WHERE id=?", (uid,))
            bot.send_message(uid, f"🎡 **{win.upper()}**! +200₺ kazandın!", reply_markup=main_menu(uid))
        else: bot.send_message(uid, f"🎡 **{win.upper()}**! Kaybettin.", reply_markup=main_menu(uid))

    # --- 💰 SİSTEM ---
    elif data == "buy":
        st = db_exe("SELECT k FROM stock LIMIT 1", f=1)
        if not st: return bot.send_message(uid, "❌ Stok kalmadı!")
        if bal < 350: return bot.send_message(uid, "❌ 350₺ bakiyen yok.")
        key = st[0][0]
        db_exe("DELETE FROM stock WHERE k=?", (key,))
        db_exe("UPDATE users SET balance = balance - 350 WHERE id=?", (uid,))
        db_exe("INSERT INTO inv VALUES (?,?)", (uid, key))
        if ref_id != 0: db_exe("UPDATE users SET balance = balance + 50 WHERE id=?", (ref_id,))
        bot.send_message(uid, f"✅ Key satın alındı! Envanterine bak kanka.", reply_markup=main_menu(uid))

    elif data == "dep":
        bot.send_message(uid, f"🏦 **IBAN:** `TR10 0006 2000 9100 0006 9697 09` \n👤 `{ALICI_AD}`\n📝 Açıklama: `{ACIKLAMA_KODU}`\n📸 Dekont at onaylayalım.")

    elif data == "ref":
        bot.send_message(uid, f"👥 **Ref Linkin:**\n`https://t.me/{(bot.get_me().username)}?start={uid}`")

# --- ⌨️ KOMUTLAR ---
@bot.message_handler(func=lambda m: True)
def text_cmds(m):
    uid, text = m.chat.id, m.text
    if text.startswith("/ver") and uid == ADMIN:
        try:
            _, tid, amt = text.split(); db_exe("UPDATE users SET balance = balance + ? WHERE id=?", (float(amt), tid))
            bot.send_message(int(tid), f"💰 +{amt}₺ bakiye yüklendi!", reply_markup=main_menu(int(tid)))
        except: pass
    elif text.startswith("/kupon"):
        if uid == ADMIN and len(text.split()) > 2:
            _, c, a, u = text.split(); db_exe("INSERT INTO coupons VALUES (?,?,?)", (c.upper(), float(a), int(u)))
            bot.send_message(ADMIN, "✅ Kupon kuruldu.")
        else:
            try:
                code = text.split()[1].upper()
                res = db_exe("SELECT amount, uses FROM coupons WHERE code=?", (code,), 1)
                if res and res[0][1] > 0:
                    db_exe("UPDATE coupons SET uses = uses - 1 WHERE code=?", (code,))
                    db_exe("UPDATE users SET balance = balance + ? WHERE id=?", (res[0][0], uid))
                    bot.send_message(uid, "✅ Kupon bakiye ekledi!", reply_markup=main_menu(uid))
            except: pass

# --- 📸 DEKONT ONAY ---
@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    if m.chat.id == ADMIN: return
    btn = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (350₺)", callback_data=f"ok_{m.chat.id}"))
    bot.forward_message(ADMIN, m.chat.id, m.message_id)
    bot.send_message(ADMIN, f"🕵️ Dekont! ID: `{m.chat.id}`", reply_markup=btn)

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
