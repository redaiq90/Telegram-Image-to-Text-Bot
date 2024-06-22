import os
import logging
import requests
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from config import TOKEN, OCR_API_KEY
import sqlite3

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

OWNER_ID = 1374312239

# Dictionary to track last message times for spam protection
last_message_time = {}

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        user_id INTEGER UNIQUE
    )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database Working!")

def add_user_if_not_exists(user_id, username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute('INSERT INTO users (username, user_id) VALUES (?, ?)', (username, user_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

async def count_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    if user_id != OWNER_ID:
        #await context.bot.send_message(chat_id=chat_id, text="You are not authorized to use this command.")
        return

    # Connect to the SQLite database
    conn = sqlite3.connect('users.db')  # Replace with the actual path to your database
    cursor = conn.cursor()

    # Query to count users
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    # Close the database connection
    cursor.close()
    conn.close()

    # Send the user count as a message
    await context.bot.send_message(chat_id=chat_id, text=f"Total number of users: {user_count}")


# Function to get the profile link of a user
def get_profile_link(username):
    return f"https://t.me/{username}" if username else "N/A"

async def start(update: Update, context: CallbackContext):
    user_info = update.message.from_user
    first_name = user_info.first_name
    user_id = user_info.id
    username = user_info.username

    # Check if user is new and add to the database if so
    is_new_user = add_user_if_not_exists(user_id, username)

    # Notify the owner about the new user
    if is_new_user:
        profile_link = get_profile_link(username)
        notification = f"New user entered the bot:\n\nID: {user_id}\nUsername: @{username}\nProfile: {profile_link}"
        await context.bot.send_message(chat_id=OWNER_ID, text=notification)

    welcome = f'''
{first_name} مرحباً

**⚡️ البوت لإستخراج النصوص من الصور** \n \n **قم بإرسال صورة لاستخراج النص منها**

الأوامر

/start أمر البداية
/help للحصول على مساعدة
'''
    await update.message.reply_text(welcome, parse_mode="MarkdownV2")



async def help_command(update: Update, context: CallbackContext):
    #await asyncio.sleep(1)  # Simulating some asynchronous task
    await update.message.reply_text('''
أرسل صورة لاستخراج النص منها !
للخدمات راسل المطور @ri2da
''')

async def ocr_image(update: Update, context: CallbackContext):
    global last_message_time
    user_id = update.message.from_user.id
    
    # Spam protection
    current_time = datetime.now()
    if user_id in last_message_time and (current_time - last_message_time[user_id]) < timedelta(seconds=5):
        return  # Ignore message if it's considered spam
    last_message_time[user_id] = current_time
    
    photo_file = await update.message.photo[-1].get_file()
    photo_path = 'temp_photo.jpg'
    await photo_file.download_to_drive(photo_path)
        
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
        context.user_data['photo_path'] = photo_path
        context.user_data['message_id'] = message.message_id
        
        # Schedule deletion if language is not chosen within 15 minutes
        loop = asyncio.get_event_loop()
        loop.create_task(delete_image_after_timeout(context, update.message.chat_id, message.message_id, photo_path))
    except TypeError:
        await update.message.reply_text("انتهى الوقت، حاول إرسال صورا مجدداً")
    except Exception as e:
        await update.message.reply_text(f'حدث خطأ:\n {str(e)}\n@ri2da قم يإعادة توجيه الرسالة للمطور')
        logger.error(f'Exception: {e}')

async def delete_image_after_timeout(context, chat_id, message_id, photo_path):
    await asyncio.sleep(900)  # 900 seconds = 15 minutes
    if 'photo_path' in context.user_data:
        os.remove(context.user_data['photo_path'])
        del context.user_data['photo_path']
        logger.info(f"Deleted temporary file {photo_path} after 15 minutes.")

        # Inform user to try again if they attempt to use an inline query after timeout
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text='انتهى الوقت حاول مجددا'
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")

async def language_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await context.bot.answer_callback_query(query.id)
    language_code = query.data

    photo_path = context.user_data.get('photo_path')
    message_id = context.user_data.get('message_id')

    try:
        # Send the image to OCR.Space API with selected language
        with open(photo_path, 'rb') as image_file:
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files={'file': image_file},
                data={'apikey': OCR_API_KEY, 'language': language_code}
            )
        result = response.json()
        
        if result['IsErroredOnProcessing']:
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=message_id,
                text='حدث خطأ ، حاول مرة اخرى'
            )
            logger.error(f"OCR Error: {result.get('ErrorMessage', 'Unknown error')}")
        else:
            parsed_text = result['ParsedResults'][0]['ParsedText']
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=message_id,
                text=f"`{parsed_text}`",
                parse_mode='MarkdownV2'
            )

    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=message_id,
            text=f'حدث خطأ:\n {str(e)}\n@ri2da قم يإعادة توجيه الرسالة للمطور'
        )
        logger.error(f'Exception: {e}')

    finally:
        # Clean up
        os.remove(photo_path)
        del context.user_data['photo_path']

        # Thank user for using the bot
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text='شكرا لاستخدامك بوتنا !\n\nللمزيد انظم للقناة\n@iqbots0\n\n@ri2da المطور'
        )

async def handle_no_language_choice(update: Update, context: CallbackContext):
    await update.message.reply_text("انتهى الوقت حاوب مجددا")
    await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)

def main() -> None:
    init_db()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", count_users))
    application.add_handler(MessageHandler(filters.PHOTO, ocr_image))
    application.add_handler(CallbackQueryHandler(language_callback))
    #application.add_handler(MessageHandler(filters.TEXT & filters.command, handle_no_language_choice))
    logger.info('Starting bot')
    application.run_polling()

if __name__ == '__main__':
    main()
