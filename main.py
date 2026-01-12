import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Ortam değişkenleri
BOT_TOKEN = os.getenv("8444472609:AAGuvazsikXGTb262Hw9MBI15eZflh-dw-o")
ADMIN_ID = os.getenv("8561815348")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN bulunamadı (Environment Variable ekle)")

if not ADMIN_ID:
    raise ValueError("ADMIN_ID bulunamadı (Environment Variable ekle)")

ADMIN_ID = int(ADMIN_ID)

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Destek aktif.\nMesajını yaz, admin’e ileteyim."
    )

# Kullanıcı mesajları
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"📩 Yeni Mesaj\n\n"
            f"👤 İsim: {user.first_name}\n"
            f"🆔 ID: {user.id}\n\n"
            f"💬 Mesaj:\n{text}"
        )
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

    print("🤖 Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
