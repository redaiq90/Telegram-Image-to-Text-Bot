import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters
from config import TOKEN, OCR_API_KEY 

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    user_info = update.message.from_user
    first_name = user_info.first_name
    await update.message.reply_text(f'''
{first_name} مرحباً

**⚡️ البوت لإستخراج النصوص من الصور** \n \n **قم بإرسال صورة لاستخراج النص منها**

:الأوامر

/start - أمر البداية
/help - للحصول على مساعدة
''')

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text('''
أرسل صورة لاستخراج النص منها !
''')

async def ocr_image(update: Update, context: CallbackContext):
    photo_file = await update.message.photo[-1].get_file()
    photo_path = 'temp_photo.jpg'
    await photo_file.download_to_drive(photo_path)

    try:
        message = await update.message.reply_text('👀⏳انتضر .... جارٍ الاستخراج')
        message_id = message.message_id

        # Send the image to OCR.Space API
        with open(photo_path, 'rb') as image_file:
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files={photo_path: image_file},
                data={'apikey': OCR_API_KEY}
            )

        result = response.json()
        if result['IsErroredOnProcessing']:
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=message_id,
                text='حدث خطأ ، حاول مرة اخرى'
            )
            logger.error(f"OCR Error: {result.get('ErrorMessage', 'Unknown error')}")
        else:
            parsed_text = result['ParsedResults'][0]['ParsedText']
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=message_id,
                text=f':النص المُستخرَج\n\n`{parsed_text}`'
            )

    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=message_id,
            text=f'حدث خطأ:\n {str(e)}\n@ri2da قم يإعادة توجيه الرسالة للمطور'
        )
        logger.error(f'Exception: {e}')
    finally:
        os.remove(photo_path)
        await update.message.reply_text('شكرا لاستخدامك بوتنا !\n\nللمزيد انظم للقناة\n@iqbots0\n\n@ri2da المطور')

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, ocr_image))

    logger.info('Starting bot')
    application.run_polling()

if __name__ == '__main__':
    main()
