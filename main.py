import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("8444472609:AAGuvazsikXGTb262Hw9MBI15eZflh-dw-o")
ADMIN_ID = 8561815348

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba Hoşgeldiniz 

H!le Almak İçin Veya Bir Soru Sormak İçin Yazdığınız Düşünüyorum 

H!le Almak İçin 
1- Cihazının Modeli Ve Markası 
2- Tercih Ettiğin H!le Varsa Onu Yaz

Önemli Not - Ücretsiz H!le Yoktur

Sormak İstediğin Soruyu Detaylı Şekilde Yazabilirsin.

Yetkililer En Kısa Sürede Dönüş Yapacaktır.")

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 {user.first_name}\n🆔 {user.id}\n\n{update.message.text}"
    )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))

app.run_polling()
