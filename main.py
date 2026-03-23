import os
import threading
import http.server
import socketserver
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- RENDER İÇİN HAYALET SUNUCU (TIMEOUT HATASINI ÇÖZER) ---
def run_dummy_server():
    # Render bir portun açık olduğunu görmezse botu kapatır.
    # Bu kısım Render'a "bak ben buradayım" der ve 7/24 uyanık tutar.
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

# --- EKİP AYARLARI ---
# BotFather'dan aldığın en güncel tokeni buraya yapıştır:
BOT_TOKEN = "8776751359:AAHA80v4jtkNWWumR5dOOJBInsHcyD4vpTQ"

# Kendi ID'ni ve ekiptekilerin ID'lerini buraya ekle:
ADMIN_IDS = [8561815348] 

# Sohbet takibi için hafıza
user_sessions = {} 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot /start alınca butonları dizer."""
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

    # --- BUTON KOMUTLARI (KALIN HTML) ---
    if text == "🍎 Axentra Store":
        msg = (
            "<b>⋆ Pubg Mobile Eklentilerimizi Görüntülemek, Mevcut Ürünlerimizi Görüntülemek, "
            "Alışveriş Yapmak için Aşağıdaki Linkten PUBG Grubumuza Katılabilir ⋆</b>\n\n"
            "https://t.me/+-38XKrEA73VhZTQ0"
        )
        await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)
        return

    elif text == "🛍️ Axentra Accounts":
        msg = (
            "<b>• Hesap Alım Satım</b>\n"
            "<b>• Klan Alım Satım</b>\n"
            "<b>• Random Hesaplar</b>\n"
            "<b>• Yüksek Ranklı Hesaplar</b>\n\n"
            "<b>Gibi Ürünlerimizle İlgilenirseniz Kanala İstek Atmanız Yeterlidir Şimdiden Hoşgeldiniz!</b>\n\n"
            "https://t.me/AxentraAccounts"
        )
        await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)
        return

    elif text == "📜 Axentra Vouch":
        msg = (
            "<b>Axentra Store ile İlgili Güvence Almak ve Güven Problemlerinizi Ortadan Kaldırmak için "
            "Güvence Kanalımızı Aşağıdaki Linkten Görüntüleyebilirsiniz</b>\n\n"
            "https://t.me/AxentraGuvence"
        )
        await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)
        return

    # --- CANLI DESTEK TRAFİĞİ (EKİP YÖNETİMİ) ---
    
    # KULLANICIDAN GELEN MESAJ (ADMİNLERE İLET)
    if chat_id not in ADMIN_IDS:
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
        
        await update.message.reply_text("<b>✅ Mesajınız iletildi, ekibimiz birazdan dönüş yapacak.</b>", parse_mode="HTML")

    # ADMİNDEN GELEN MESAJ (KULLANICIYA CEVAP VER)
    else:
        if update.message.reply_to_message:
            try:
                reply_text = update.message.reply_to_message.text
                import re
                # ID'yi mesajdan düzenli ifade ile çekiyoruz
                match = re.search(r"ID: (\d+)", reply_text)
                if match:
                    target_id = int(match.group(1))
                    await context.bot.send_message(chat_id=target_id, text=f"🎧 <b>Destek Ekibi:</b> {text}", parse_mode="HTML")
                    await update.message.reply_text(f"✅ <b>Mesaj iletildi (ID: {target_id})</b>", parse_mode="HTML")
                else:
                    await update.message.reply_text("⚠️ <b>Hata: Lütfen ID içeren mesajı yanıtla.</b>", parse_mode="HTML")
            except Exception as e:
                await update.message.reply_text(f"⚠️ <b>Hata:</b> {e}", parse_mode="HTML")

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 <b>Senin Chat ID'n:</b> <code>{update.message.chat_id}</code>", parse_mode="HTML")

def main():
    # 1. Hayalet sunucuyu arka planda başlat (Render için)
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # 2. Botu başlat
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_my_id))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Axentra Ekip Botu Aktif! Adminler hazır.")
    app.run_polling()

if __name__ == "__main__":
    main()
                    
