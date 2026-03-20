import telebot, sqlite3, time, threading, os, random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# --- 🌐 RENDER ---
app = Flask(__name__)
@app.route('/')
def home(): return "ONLINE"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT",8080)))

# --- AYAR ---
TOKEN = "8723920846:AAH7t5GOTogArVjk7ipZ66iAJqRm1HytTls"
ADMIN = 8561815348
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- DB ---
def db(q,p=(),f=0):
    with sqlite3.connect("db.db") as c:
        cur=c.cursor(); cur.execute(q,p)
        if f: return cur.fetchall()
        c.commit()

db("CREATE TABLE IF NOT EXISTS users (id INT, balance REAL, xp INT, ref INT DEFAULT 0, vip INT DEFAULT 0)")
db("CREATE TABLE IF NOT EXISTS stock (k TEXT)")
db("CREATE TABLE IF NOT EXISTS inv (uid INT, k TEXT)")

# --- MENU ---
def menu(id):
    u=db("SELECT * FROM users WHERE id=?",(id,),1)[0]
    stok=len(db("SELECT * FROM stock",f=1))
    m=InlineKeyboardMarkup(row_width=2)

    m.add(InlineKeyboardButton(f"🚀 SATIN AL (350₺) [{stok}]",callback_data="buy"))
    m.add(InlineKeyboardButton("💰 BAKİYE",callback_data="dep"),
          InlineKeyboardButton("🎰 SLOT",callback_data="slot"))
    m.add(InlineKeyboardButton("📦 ENVANTER",callback_data="inv"),
          InlineKeyboardButton("👥 REFERANS",callback_data="ref"))
    m.add(InlineKeyboardButton("📅 GÜNLÜK",callback_data="daily"),
          InlineKeyboardButton("🪙 YAZI-TURA",callback_data="coin"))

    if id==ADMIN:
        m.add(InlineKeyboardButton("👑 ADMIN PANEL",callback_data="admin"),
              InlineKeyboardButton("📊 İSTATİSTİK",callback_data="stats_admin"))

    vip = "💎" if u[4]==1 else "👤"
    m.add(InlineKeyboardButton(f"{vip} {u[1]}₺ | XP {u[2]}",callback_data="none"))
    return m

# --- START ---
@bot.message_handler(commands=['start'])
def start(m):
    id=m.chat.id
    args=m.text.split()
    ref=int(args[1]) if len(args)>1 and args[1].isdigit() else 0

    if not db("SELECT * FROM users WHERE id=?",(id,),1):
        db("INSERT INTO users VALUES (?,?,?,?,?)",(id,15,0,ref,0))

    bot.send_message(id,"🔥 AXENTRA STORE'A HOŞGELDİN!",reply_markup=menu(id))

# --- BUTTON ---
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    id=c.message.chat.id
    bot.answer_callback_query(c.id)
    u=db("SELECT * FROM users WHERE id=?",(id,),1)[0]

    # --- BAKİYE ---
    if c.data=="dep":
        m=InlineKeyboardMarkup()
        m.add(
            InlineKeyboardButton("📋 IBAN KOPYALA",callback_data="iban"),
            InlineKeyboardButton("📋 AÇIKLAMA KOPYALA",callback_data="desc")
        )
        bot.send_message(id,f"""💳 *ÖDEME BİLGİLERİ*

IBAN:
`TR10 0006 2000 9100 0006 9697 09`

Alıcı:
Garanti Ödeme ve Elektronik Para Hizmetleri A.Ş.

Açıklama:
`TAMİ7987919953449959`

📸 Ödeme sonrası dekont gönder.
""",reply_markup=m)

    elif c.data=="iban":
        bot.send_message(id,"`TR10 0006 2000 9100 0006 9697 09`")

    elif c.data=="desc":
        bot.send_message(id,"`TAMİ7987919953449959`")

    # --- SLOT ---
    elif c.data=="slot":
        if u[1]>=10:
            db("UPDATE users SET balance=balance-10 WHERE id=?",(id,))
            if random.randint(1,4)==2:
                db("UPDATE users SET balance=balance+120,xp=xp+10 WHERE id=?",(id,))
                bot.send_message(id,"🎉 +120₺ kazandın!")
            else:
                bot.send_message(id,"❌ Kaybettin")
        else:
            bot.send_message(id,"❌ Bakiye yok")

    # --- COIN ---
    elif c.data=="coin":
        if u[1]>=10:
            db("UPDATE users SET balance=balance-10 WHERE id=?",(id,))
            if random.choice([0,1]):
                db("UPDATE users SET balance=balance+20 WHERE id=?",(id,))
                bot.send_message(id,"🪙 Kazandın!")
            else:
                bot.send_message(id,"❌ Kaybettin")

    # --- DAILY ---
    elif c.data=="daily":
        db("UPDATE users SET balance=balance+25,xp=xp+5 WHERE id=?",(id,))
        bot.send_message(id,"🎁 +25₺ aldın!")

    # --- BUY ---
    elif c.data=="buy":
        stok=db("SELECT * FROM stock",f=1)
        if u[1]>=350 and stok:
            k=stok[0][0]
            db("DELETE FROM stock WHERE k=?",(k,))
            db("INSERT INTO inv VALUES (?,?)",(id,k))
            db("UPDATE users SET balance=balance-350,xp=xp+20 WHERE id=?",(id,))

            if u[3]!=0:
                db("UPDATE users SET balance=balance+35 WHERE id=?",(u[3],))

            bot.send_message(id,f"🔑 KEY:\n`{k}`")
            bot.send_message(id,"⚠️ Son stoklar! Kaçırma!")

        else:
            bot.send_message(id,"❌ Bakiye veya stok yok")

    # --- ENVANTER ---
    elif c.data=="inv":
        data=db("SELECT k FROM inv WHERE uid=?",(id,),1)
        txt="\n".join([x[0] for x in data]) or "Boş"
        bot.send_message(id,f"📦 ENVANTER:\n{txt}")

    # --- REF ---
    elif c.data=="ref":
        link=f"https://t.me/{bot.get_me().username}?start={id}"
        bot.send_message(id,f"👥 Referans linkin:\n{link}")

    # --- ADMIN ---
    elif c.data=="admin" and id==ADMIN:
        bot.send_message(id,"🔑 Keyleri satır satır gönder")

    elif c.data=="stats_admin" and id==ADMIN:
        users=len(db("SELECT * FROM users",f=1))
        total=sum([x[1] for x in db("SELECT * FROM users",f=1)])
        stock=len(db("SELECT * FROM stock",f=1))

        bot.send_message(id,f"""📊 İSTATİSTİK

👥 Kullanıcı: {users}
💸 Toplam Para: {total}₺
📦 Stok: {stock}
""")

# --- ADMIN KEY EKLE ---
@bot.message_handler(func=lambda m: m.chat.id==ADMIN)
def add(m):
    for k in m.text.split("\n"):
        db("INSERT INTO stock VALUES (?)",(k,))
    bot.send_message(ADMIN,"✅ Stok eklendi")

# --- AUTO REPLY (SATIŞ BOTU) ---
@bot.message_handler(func=lambda m: True)
def auto(m):
    t=m.text.lower()

    if "fiyat" in t:
        bot.reply_to(m,"💸 350₺\n🔥 Stoklar tükeniyor!")

    elif "nasıl" in t:
        bot.reply_to(m,"🚀 Menüden SATIN AL bas")

    elif "güven" in t:
        bot.reply_to(m,"✅ Güvenli sistem\n⚡ Anında teslim")

    elif "indirim" in t:
        bot.reply_to(m,"💎 VIP ol indirim kazan!")

# --- RUN ---
if __name__=="__main__":
    threading.Thread(target=run).start()
    print("LEVEL 100 AKTİF 🚀")

    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except:
            time.sleep(5)
