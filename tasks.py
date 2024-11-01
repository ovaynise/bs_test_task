import time
from datetime import datetime, timedelta

import httpx
from celery import Celery
from celery.schedules import crontab

from config import DATABASE_URL, LOG_PATCH, TELEGRAM_TOKEN
from core.logger import OvayLogger
from database.db import Database

logger = OvayLogger(name='bot_logger', log_file_path=LOG_PATCH).get_logger()

database = Database(DATABASE_URL)
REDIS_BROKER_URL = 'redis://redis:6379/0'
celery_app = Celery('tasks', broker=REDIS_BROKER_URL)


MINUTES_AFTER_DEADLINE = 10


@celery_app.task
def bot_send_message(user_id, description, retries=3):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {'chat_id': user_id, 'text': f'Напоминание {description}'}

    for attempt in range(retries):
        try:
            response = httpx.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f'Message sent to user {user_id}: {description}')
            return
        except httpx.RequestError as e:
            logger.error(f'Request error for user {user_id}: {e}')
            if attempt < retries - 1:
                time.sleep(2)


@celery_app.task
def send_message_task():
    tasks = database.get_all_not_completed_tasks()
    now = datetime.now()

    for task in tasks:
        deadline = task.deadline
        time_diff = deadline - now
        if timedelta(days=1) >= time_diff > timedelta(seconds=0):
            if now.hour == deadline.hour and now.minute == deadline.minute:
                logger.info(
                    f'Задача {task.id} за день до дедлайна. '
                    f'Напоминание пользователю {task.user_id}.')
                bot_send_message.delay(task.user_id,
                                       f'№{task.id}🔔(за 1дн. до deadline ):'
                                       f'\n' + task.description)
        elif timedelta(seconds=0) >= time_diff >= timedelta(
                seconds=-5):
            if now.hour == deadline.hour and now.minute == deadline.minute:
                logger.info(
                    f'Задача {task.id} в день дедлайна. Напоминание '
                    f'пользователю {task.user_id}.')
                bot_send_message.delay(task.user_id,
                                       f'№{task.id}🔅 (в день дедлайна)'
                                       f':\n' + task.description)
        elif time_diff < timedelta(seconds=0):
            if int(abs(
                    time_diff.total_seconds()) // 60
                   ) % MINUTES_AFTER_DEADLINE == 0:
                logger.info(
                    f'Задача {task.id} просрочена. Напоминание'
                    f' пользователю {task.user_id} каждую'
                    f'{MINUTES_AFTER_DEADLINE} минуту.')
                bot_send_message.delay(
                    task.user_id,
                    f'№{task.id}⚠️ (просрочено,'
                    f' напоминаем с повтором {MINUTES_AFTER_DEADLINE} '
                    f'мин.):\n' + task.description)


celery_app.conf.beat_schedule = {
    'send-reminders-every-minute': {
        'task': 'tasks.send_message_task',
        'schedule': crontab(minute='*'),
    },
}
celery_app.conf.timezone = 'UTC'
