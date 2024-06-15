# Telegram-Image-to-Text-Bot
Telegram bot that extracts text from images sent by users using Optical Character Recognition (OCR)

# OCR Bot

This Telegram bot uses OCR to extract text from images. Users can send images, and the bot will process them to extract any text present in the images using the OCR.Space API.

## Features

- **Extract Text from Images**: Send an image, and the bot will extract text from it.
- **Error Handling**: Handles errors gracefully and informs the user if something goes wrong.
- **Interactive**: Responds with the extracted text directly in the chat.

## Commands

- `/start` - Start the bot and display the welcome message.
- `/help` - Show a help message with instructions.

## Prerequisites

- Python 3.7 or later
- `python-telegram-bot` library
- `requests` library

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/telegram-ocr-bot.git
   cd telegram-ocr-bot


2.  **Install dependencies**

  pip install -r requirements.txt

3. **Set up the environment variables:**
Edit config.py and set your Telegram bot token and OCR API key.


4.  **Run the bot:**
  
 python main.py

