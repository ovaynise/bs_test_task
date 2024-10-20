import os
from telegram import Bot
from logger import OvayLogger
from dotenv import load_dotenv

load_dotenv()

log_file_path = os.getenv("BOT_LOG_FILE_PATH", "/bot/bot.log")


logger = OvayLogger(
    name="bot_logger", log_file_path=log_file_path
).get_logger()

def get_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    logger.info(
        f"Инициализация бота...Токен бота получен: {token}")
    return Bot(token=token)


