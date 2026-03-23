import os
import threading
import http.server
import socketserver
import logging
import re
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. RENDER'I UYANIK TUTMA KODU (HAYALET SUNUCU) ---
def run_dummy_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        handler = http.server.SimpleHTTPRequestHandler
        # Portun kullanımda olup olmadığını kontrol etmezse çökebilir, hata koruması ekledim.
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"✅ Hayalet sunucu {port} portunda aktif.")
            httpd.serve_forever()
    except Exception as e:
        print(f"⚠️ Hayalet sunucu başlatılamadı (Normal olabilir): {e}")

# --- 2. AYARLAR ---
BOT_TOKEN = "8776751359:AAHA80v4jtkNWWumR5dOOJBInsHcyD4vpTQ"
ADMIN_IDS = [8561815348] 

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
    if not update.message or not update.message.text:
        return

    text = update.message.text
    chat_id = update.message.chat_id
    user = update.message.from_user

    # --- BUTON KOMUTLARI ---
    if text == "🍎 Axentra Store":
        await update.message.reply_text("<b>⋆ PUBG Grubumuz:</b>\nhttps://t.me/+-38XKrEA73VhZTQ0", parse_mode="HTML")
        return
    elif text == "🛍️ Axentra Accounts":
        await update.message.reply_text("<b>• Hesap Alım Satım Kanalımız:</b>\nhttps://t.me/AxentraAccounts", parse_mode="HTML")
        return
    elif text == "📜 Axentra Vouch":
        await update.message.reply_text("<b>Axentra Store Güvence Kanalı:</b>\nhttps://t.me/AxentraGuvence", parse_mode="HTML")
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
            except Exception as e:
                logging.error(f"Admin {admin_id} mesaj iletilemedi: {e}")
        
        # Kullanıcıya mesajının gittiğini fısılda (isteğe bağlı ama sessiz olması daha iyi demiştin)
        # await update.message.reply_text("✅") 

    else:
        # Adminden gelen cevabı müşteriye ilet (Reply/Yanıtla yaparak)
        if update.message.reply_to_message:
            try:
                reply_text = update.message.reply_to_message.text
                # ID'yi çekmek için regex (ID: 12345 formatını arar)
                match = re.search(r"ID: (\d+)", reply_text)
                if match:
                    target_id = int(match.group(1))
                    await context.bot.send_message(chat_id=target_id, text=f"🎧 <b>Destek Ekibi:</b> {text}", parse_mode="HTML")
                    await update.message.reply_text(f"✅ <b>İletildi (ID: {target_id})</b>", parse_mode="HTML")
                else:
                    await update.message.reply_text("⚠️ <b>Hata:</b> Yanıtladığınız mesajda Kullanıcı ID bulunamadı!")
            except Exception as e:
                await update.message.reply_text(f"⚠️ <b>Hata:</b> {e}", parse_mode="HTML")

def main():
    # Hayalet sunucuyu thread ile başlat
    t = threading.Thread(target=run_dummy_server, daemon=True)
    t.start()
    
    # Bot kurulumu
    print("🚀 Axentra Destek Botu başlatılıyor...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handler'lar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Botu çalıştır (Pydroid uyumlu loop yönetimi)
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
