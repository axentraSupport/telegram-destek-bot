import os
import threading
import http.server
import socketserver
import logging
import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. RENDER'I UYANIK TUTMA KODU (HAYALET SUNUCU) ---
def run_dummy_server():
    # Render bir portun açık olduğunu görmezse botu kapatır.
    # Bu fonksiyon Render'a "ben bir web servisiyim" numarası yapar.
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Hayalet sunucu {port} portunda baslatildi.")
        httpd.serve_forever()

# --- 2. EKİP AYARLARI ---
BOT_TOKEN = "8776751359:AAHA80v4jtkNWWumR5dOOJBInsHcyD4vpTQ"
ADMIN_IDS = [8561815348] # Buraya diger adminlerin ID'lerini de ekleyebilirsin

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🍎 Axentra Store", "🛍️ Axentra Accounts"],
        ["📜 Axentra Vouch"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 <b>Axentra Store Destek Botuna Hoş Geldiniz!</b>\n\n"
        "<b>Aşağıdaki butonlardan kanallarımıza ulaşabilir veya bize direkt mesaj yazabilirsiniz.</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id
    user = update.message.from_user

    # --- BUTON KOMUTLARI ---
    if text == "🍎 Axentra Store":
        msg = "<b>⋆ PUBG Grubumuz:</b>\nhttps://t.me/+-38XKrEA73VhZTQ0"
        await update.message.reply_text(msg, parse_mode="HTML")
        return
    elif text == "🛍️ Axentra Accounts":
        msg = "<b>• Hesap Alım Satım Kanalımız:</b>\nhttps://t.me/AxentraAccounts"
        await update.message.reply_text(msg, parse_mode="HTML")
        return
    elif text == "📜 Axentra Vouch":
        msg = "<b>Axentra Store Güvence Kanalı:</b>\nhttps://t.me/AxentraGuvence"
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    # --- CANLI DESTEK TRAFİĞİ ---
    if chat_id not in ADMIN_IDS:
        # Müşteriden gelen mesajı adminlere ilet
        info_msg = (
            f"📩 <b>YENİ MESAJ</b>\n"
            f"👤 <b>İsim:</b> {user.first_name}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"💬 <b>Mesaj:</b> {text}"
        )
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=info_msg, parse_mode="HTML")
            except:
                continue
        
        # NOT: Buradaki otomatik onay mesajını sildim. Müşteri bir şey görmeyecek.

    else:
        # Adminden gelen cevabı müşteriye ilet (Reply/Yanıtla yaparak)
        if update.message.reply_to_message:
            try:
                reply_text = update.message.reply_to_message.text
                match = re.search(r"ID: (\d+)", reply_text)
                if match:
                    target_id = int(match.group(1))
                    await context.bot.send_message(chat_id=target_id, text=f"🎧 <b>Destek Ekibi:</b> {text}", parse_mode="HTML")
                    # Adminin ekranında iletildiğini teyit et
                    await update.message.reply_text(f"✅ <b>İletildi (ID: {target_id})</b>", parse_mode="HTML")
            except Exception as e:
                await update.message.reply_text(f"⚠️ <b>Hata:</b> {e}", parse_mode="HTML")

def main():
    # Render'ı uyanık tutan sunucuyu arka planda (thread) baslatıyoruz
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # Botu baslatıyoruz
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot uyanık ve Render desteği aktif!")
    app.run_polling()

if __name__ == "__main__":
    main()
    
