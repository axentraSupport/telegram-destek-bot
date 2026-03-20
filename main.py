import telebot, sqlite3, time, threading, os, random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# --- 🌐 RENDER AKTİF TUTUCU ---
app = Flask(__name__)
@app.route('/')
def home(): return "AXENTRA V120 ONLINE 🚀"

def run_flask(): 
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 👑 AYARLAR ---
TOKEN = "8723920846:AAH7t5GOTogArVjk7ipZ66iAJqRm1HytTls"
ADMIN = 8561815348
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- 🗄️ VERİTABANI MOTORU ---
def db(q, p=(), f=0):
    try:
        with sqlite3.connect("axentra_v120.db", timeout=20) as c:
            cur = c.cursor()
            cur.execute(q, p)
            if f: return cur.fetchall()
            c.commit()
    except Exception as e:
        print(f"DB Hatası: {e}")
        return []

# Tablolar (XP, Harcama, VIP, Stok ve Envanter)
db("CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, balance REAL, xp INT, spent REAL DEFAULT 0, ref INT DEFAULT 0, vip INT DEFAULT 0)")
db("CREATE TABLE IF NOT EXISTS stock (k TEXT)") 
db("CREATE TABLE IF NOT EXISTS inv (uid INT, k TEXT)") 

# --- 📱 ANA MENÜ (GÖRSELDEKİ %100 AYNI DİZİLİM) ---
def menu(id):
    res = db("SELECT balance, xp, vip FROM users WHERE id=?", (id,), 1)
    if not res: return None
    u = res[0]
    stok_count = len(db("SELECT * FROM stock", f=1))
    
    m = InlineKeyboardMarkup(row_width=2)
    # 1. Satır: Ana Ürün
    m.add(InlineKeyboardButton(f"🚀 KEY SATIN AL (350₺) [{stok_count}]", callback_data="buy"))
    # 2. Satır: VIP Aktivasyon & Slot
    m.add(InlineKeyboardButton("🌟 KEY İLE VIP AKTİF ET", callback_data="activate_vip"),
          InlineKeyboardButton("🎰 SLOT (HAPPY HOUR)", callback_data="slot"))
    # 3. Satır: Bakiye & Çark
    m.add(InlineKeyboardButton("💰 BAKİYE YÜKLE", callback_data="dep"),
          InlineKeyboardButton("🎡 ÇARKIFELEK", callback_data="wheel"))
    # 4. Satır: Profil/Liderler
    m.add(InlineKeyboardButton("🏆 LİDERLER", callback_data="top"),
          InlineKeyboardButton("📦 ENVANTERİM", callback_data="inv"))
    # 5. Satır: Destek & Referans
    m.add(InlineKeyboardButton("🛠️ DESTEK", url="https://t.me/AxentraStore"),
          InlineKeyboardButton("👥 REFERANS SİSTEMİ", callback_data="ref"))
    # 6. Satır: Günlük & Yazı-Tura
    m.add(InlineKeyboardButton("📅 GÜNLÜK ÖDÜL", callback_data="daily"),
          InlineKeyboardButton("🪙 YAZI-TURA", callback_data="coin"))

    if id == ADMIN:
        m.add(InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin_p"))

    vip_status = "✨ VIP" if u[2] == 1 else "👤 ÜYE"
    m.add(InlineKeyboardButton(f"{vip_status} | {u[0]}₺ | XP: {u[1]}", callback_data="stats"))
    return m

# --- 🛡️ START ---
@bot.message_handler(commands=['start'])
def start(m):
    id = m.chat.id
    args = m.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
    if not db("SELECT id FROM users WHERE id=?", (id,), 1):
        db("INSERT INTO users (id, balance, xp, spent, ref, vip) VALUES (?,?,?,?,?,?)", (id, 15.0, 0, 0, ref_id, 0))
    bot.send_message(id, "🔱 **Axentra Store İmparatorluğu Aktif!**", reply_markup=menu(id))

# --- ⚙️ BUTON İŞLEMLERİ (Callback Answer Zırhlı) ---
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    id = c.message.chat.id
    bot.answer_callback_query(c.id) # Tuş takılma fixi
    res = db("SELECT balance, xp, ref, spent, vip FROM users WHERE id=?", (id,), 1)
    if not res: return
    u = res[0]

    # KEY SATIN AL
    if c.data == "buy":
        stok = db("SELECT k FROM stock", f=1)
        if u[0] >= 350 and stok:
            k = stok[0][0]
            db("DELETE FROM stock WHERE k=?", (k,))
            db("INSERT INTO inv VALUES (?,?)", (id, k))
            new_spent = u[3] + 350
            # 380 harcama yapan otomatik VIP olur
            is_vip = 1 if new_spent >= 380 else u[4]
            db("UPDATE users SET balance=balance-350, spent=?, vip=?, xp=xp+50 WHERE id=?", (new_spent, is_vip, id))
            # 35₺ Referans Bonusu
            if u[2] != 0:
                db("UPDATE users SET balance=balance+35 WHERE id=?", (u[2],))
                try: bot.send_message(u[2], "🎊 Ref bonusun (35₺) yattı! Arkadaşın anahtar aldı.")
                except: pass
            bot.send_message(id, f"✅ Key Satın Alındı!\n🔑 KEY: `{k}`\n\n*Envanterinden VIP aktivasyonu yapabilirsin.*", reply_markup=menu(id))
        else: bot.send_message(id, "❌ Bakiye yetersiz veya stok yok!")

    # KEY İLE VIP AKTİF ET
    elif c.data == "activate_vip":
        if u[4] == 1:
            bot.send_message(id, "✨ Zaten VIP üyesiniz!")
        else:
            keys = db("SELECT k FROM inv WHERE uid=?", (id,), 1)
            if keys:
                key_to_use = keys[0][0]
                db("DELETE FROM inv WHERE uid=? AND k=? LIMIT 1", (id, key_to_use))
                db("UPDATE users SET vip=1 WHERE id=?", (id,))
                bot.send_message(id, "🎊 **TEBRİKLER!** Envanterindeki key kullanıldı ve **VIP ÜYELİĞİN** aktif edildi!", reply_markup=menu(id))
            else:
                bot.send_message(id, "❌ Envanterinde key yok! Önce 'Key Satın Al' yapmalısın.")

    elif c.data == "dep":
        bot.send_message(id, "💳 **IBAN:** `TR10 0006 2000 9100 0006 9697 09` \n**Açıklama:** `TAMİ7987919953449959` \n\n📸 Dekontu fotoğraf olarak buraya at kanka.")

    elif c.data == "inv":
        data = db("SELECT k FROM inv WHERE uid=?", (id,), 1)
        txt = "\n".join([f"🔑 `{x[0]}`" for x in data]) if data else "Envanterin boş kanka."
        bot.send_message(id, f"📦 **ENVANTERİM:**\n\n{txt}")

    elif c.data == "ref":
        link = f"https://t.me/{bot.get_me().username}?start={id}"
        bot.send_message(id, f"👥 **REFERANS SİSTEMİ**\nHer yüklemede **35₺** kazan!\n`{link}`")

    elif c.data == "slot":
        if u[0] >= 10:
            db("UPDATE users SET balance=balance-10 WHERE id=?", (id,))
            if random.randint(1, 4) == 2:
                db("UPDATE users SET balance=balance+120, xp=xp+20 WHERE id=?", (id,))
                bot.send_message(id, "🎉 **KAZANDIN! +120₺**", reply_markup=menu(id))
            else: bot.send_message(id, "❌ Kaybettin...", reply_markup=menu(id))
        else: bot.send_message(id, "❌ Bakiye yetersiz!")

# --- 📸 DEKONT ONAY ---
@bot.message_handler(content_types=['photo'])
def handle_receipt(m):
    if m.chat.id == ADMIN: return
    mk = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ ONAYLA (+350₺)", callback_data=f"ok_{m.chat.id}"))
    bot.forward_message(ADMIN, m.chat.id, m.message_id)
    bot.send_message(ADMIN, f"🕵️ ID: `{m.chat.id}`", reply_markup=mk)
    bot.reply_to(m, "⏳ İletildi, patron onaylayınca para yatar.")

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_"))
def admin_confirm(c):
    tid = int(c.data.split("_")[1])
    db("UPDATE users SET balance=balance+350 WHERE id=?", (tid,))
    bot.send_message(tid, "✅ Bakiyeniz patron tarafından onaylandı!")
    bot.delete_message(ADMIN, c.message.message_id)

# --- 🚀 RUN ---
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("AXENTRA V120 SİSTEMİ ATEŞLENDİ! 🚀")
    while True:
        try:
            bot.infinity_polling(timeout=25, long_polling_timeout=15)
        except:
            time.sleep(5)
    
