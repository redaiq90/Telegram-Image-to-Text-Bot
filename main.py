import os
import logging
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler
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
    # Download the photo
    photo_file = await update.message.photo[-1].get_file()
    photo_path = 'temp_photo.jpg'
    await photo_file.download(photo_path)

    try:
        # Ask user to choose language
        message = await update.message.reply_text('اختر اللغة المراد استخراجها:',
                                                 reply_markup=InlineKeyboardMarkup([
                                                     [
                                                         InlineKeyboardButton("العربية", callback_data="ara"),
                                                         InlineKeyboardButton("البلغارية", callback_data="bul"),
                                                         InlineKeyboardButton("الصينية المبسطة", callback_data="chs"),
                                                     ],
                                                     [
                                                         InlineKeyboardButton("الصينية التقليدية", callback_data="cht"),
                                                         InlineKeyboardButton("الكرواتية", callback_data="hrv"),
                                                         InlineKeyboardButton("التشيكية", callback_data="cze"),
                                                     ],
                                                     [
                                                         InlineKeyboardButton("الدانماركية", callback_data="dan"),
                                                         InlineKeyboardButton("الهولندية", callback_data="dut"),
                                                         InlineKeyboardButton("الإنجليزية", callback_data="eng"),
                                                     ],
                                                     [
                                                         InlineKeyboardButton("الفنلندية", callback_data="fin"),
                                                         InlineKeyboardButton("الفرنسية", callback_data="fre"),
                                                         InlineKeyboardButton("الألمانية", callback_data="ger"),
                                                     ],
                                                     [
                                                         InlineKeyboardButton("اليونانية", callback_data="gre"),
                                                         InlineKeyboardButton("الهنغارية", callback_data="hun"),
                                                         InlineKeyboardButton("الكورية", callback_data="kor"),
                                                     ],
                                                     [
                                                         InlineKeyboardButton("الإيطالية", callback_data="ita"),
                                                         InlineKeyboardButton("اليابانية", callback_data="jpn"),
                                                         InlineKeyboardButton("البولندية", callback_data="pol"),
                                                     ],
                                                     [
                                                         InlineKeyboardButton("البرتغالية", callback_data="por"),
                                                         InlineKeyboardButton("الروسية", callback_data="rus"),
                                                         InlineKeyboardButton("السلوفينية", callback_data="slv"),
                                                     ],
                                                     [
                                                         InlineKeyboardButton("الإسبانية", callback_data="spa"),
                                                         InlineKeyboardButton("السويدية", callback_data="swe"),
                                                         InlineKeyboardButton("التركية", callback_data="tur"),
                                                     ],
                                                 ]))
        message_id = message.message_id

        # Handle language selection callback
        def language_callback(update: Update, context: CallbackContext):
            query = update.callback_query
            context.bot.answer_callback_query(query.id)
            language_code = query.data

            # Send the image to OCR.Space API with selected language
            with open(photo_path, 'rb') as image_file:
                response = requests.post(
                    'https://api.ocr.space/parse/image',
                    files={'file': image_file},
                    data={'apikey': OCR_API_KEY, 'language': language_code}
                )

            result = response.json()
            if result['IsErroredOnProcessing']:
                context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=message_id,
                    text='حدث خطأ ، حاول مرة اخرى'
                )
                logger.error(f"OCR Error: {result.get('ErrorMessage', 'Unknown error')}")
            else:
                parsed_text = result['ParsedResults'][0]['ParsedText']
                context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=message_id,
                    text=f':النص المُستخرَج\n\n`{parsed_text}`'
                )

            # Clean up
            os.remove(photo_path)

        # Register callback handler
        context.dispatcher.add_handler(CallbackQueryHandler(language_callback))

    except Exception as e:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f'حدث خطأ:\n {str(e)}\n@ri2da قم يإعادة توجيه الرسالة للمطور'
        )
        logger.error(f'Exception: {e}')

    finally:
        os.remove(photo_path)

    # Thank user for using the bot
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
