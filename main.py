import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters
from config import TOKEN, OCR_API_KEY  # Import the config

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    user_info = update.message.from_user
    first_name = user_info.first_name
    await update.message.reply_text(f'''
Hello {first_name},

This bot extracts text from images using OCR ⚡️ \n \n Send an image to get started

Available commands:

/start - Show this message
/help - Get help using the bot
''')

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text('''
Send an image to extract text from it using OCR😌
''')

async def ocr_image(update: Update, context: CallbackContext):
    photo_file = await update.message.photo[-1].get_file()
    photo_path = 'temp_photo.jpg'
    await photo_file.download_to_drive(photo_path)

    try:
        # Send a "Please wait..." message and store the message ID
        message = await update.message.reply_text('wait... Processing the image👀⏳')
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
                text='Mtsmm an error occurred while processing the image...Try again'
            )
            logger.error(f"OCR Error: {result.get('ErrorMessage', 'Unknown error')}")
        else:
            parsed_text = result['ParsedResults'][0]['ParsedText']
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=message_id,
                text=f'Extracted text:\n{parsed_text}'
            )

    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=message_id,
            text=f'An error occurred: {str(e)}'
        )
        logger.error(f'Exception: {e}')
    finally:
        os.remove(photo_path)
        await update.message.reply_text('Thanks for using my bot🤛🏽   \n \n @A13XBOTZ\n\nJoin this channel to make me smile:)')

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, ocr_image))

    logger.info('Starting bot')
    application.run_polling()

if __name__ == '__main__':
    main()
