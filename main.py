import os
import sys

from telegram.ext import Application

from bot.bot import TaskBot
from config import DATABASE_URL, TELEGRAM_TOKEN, logger
from database.db import Database

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def main():
    logger.debug('start main')
    database = Database(DATABASE_URL)
    task_bot = Application.builder().token(TELEGRAM_TOKEN).build()
    bot = TaskBot(task_bot, database)
    bot.run()


if __name__ == '__main__':
    main()
