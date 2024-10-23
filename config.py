import os
from dotenv import load_dotenv
load_dotenv()

LOG_PATCH = os.getenv("BOT_LOG_FILE_PATH", "/bot/bot.log")
DATABASE = 'sqlite:///tasks.db'
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = "sqlite:///tasks.db"
REDIS_BROKER_URL = 'redis://redis:6379/0'
REMIND_INTERVAL_AFTER_DEADLINE = 60