import os
import logging
import requests
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler
from config import TOKEN, OCR_API_KEY

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    user_info = update.message.from_user
    first_name = user_info.first_name
    update.message.reply_text(f'''
{first_name} مرحباً

**⚡️ البوت لإستخراج النصوص من الصور** \n \n **قم بإرسال صورة لاستخراج النص منها**

:الأوامر

/start - أمر البداية
/help - للحصول على مساعدة
''')

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text('''
أرسل صورة لاستخراج النص منها !
''')

def ocr_image(update: Update, context: CallbackContext):
    # Download the photo
    photo_file = update.message.photo[-1].get_file()
    photo_path = 'temp_photo.jpg'
    photo_file.download_to_drive(photo_path)

    try:
        # Ask user to choose language
        message = update.message.reply_text('اختر اللغة المراد استخراجها:',
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
        context.user_data['photo_path'] = photo_path
        context.user_data['message_id'] = message.message_id

    except Exception as e:
        update.message.reply_text(f'حدث خطأ:\n {str(e)}\n@ri2da قم يإعادة توجيه الرسالة للمطور')
        logger.error(f'Exception: {e}')

def language_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    context.bot.answer_callback_query(query.id)
    language_code = query.data

    photo_path = context.user_data.get('photo_path')
    message_id = context.user_data.get('message_id')

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

    # Thank user for using the bot
    context.bot.send_message(
        chat_id=query.message.chat_id,
        text='شكرا لاستخدامك بوتنا !\n\nللمزيد انظم للقناة\n@iqbots0\n\n@ri2da المطور'
    )

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, ocr_image))
    application.add_handler(CallbackQueryHandler(language_callback))
    logger.info('Starting bot')
    application.run_polling()

if __name__ == '__main__':
    main()
