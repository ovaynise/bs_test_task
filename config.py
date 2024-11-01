import os

from dotenv import load_dotenv

from core.logger import OvayLogger

load_dotenv()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'tasks.db')
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


LOG_PATCH = os.getenv("BOT_LOG_FILE_PATH", "/bot/bot.log")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REDIS_BROKER_URL = 'redis://redis:6379/0'
REMIND_INTERVAL_AFTER_DEADLINE = 60

logger = OvayLogger(
    name='bot_init_logger', log_file_path=LOG_PATCH
).get_logger()