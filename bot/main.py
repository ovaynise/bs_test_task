from db import Database
from logger import OvayLogger
from config import LOG_PATCH, DATABASE_URL, TELEGRAM_TOKEN
from bot import TaskBot
from telegram.ext import Application

logger = OvayLogger(
    name='bot_init_logger', log_file_path=LOG_PATCH
).get_logger()

if __name__ == '__main__':
    logger.debug('start main')
    database = Database(DATABASE_URL)
    task_bot = Application.builder().token(TELEGRAM_TOKEN).build()
    bot = TaskBot(task_bot, database)
    bot.run()