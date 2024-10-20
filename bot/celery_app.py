import asyncio
from celery import Celery
from db import get_tasks, get_all_tasks
from datetime import datetime
from bot_init import get_bot, logger

REMIND_INTERVAL_AFTER_DEADLINE = 60
app = Celery('tasks', broker='redis://redis:6379/0', include=['celery_app'])
app.conf.broker_connection_retry_on_startup = True

async def async_send_message(reminder_bot, chat_id, text):
    logger.info(f'Celery отправляет сообщение. "{text}" для {chat_id}')
    send_message = reminder_bot.send_message(chat_id=chat_id, text=text)
    logger.info(f'Сообщение успешно отправлено')
    await send_message

def run_async_task(reminder_bot, chat_id, text):
    asyncio.run(async_send_message(reminder_bot, chat_id, text))

@app.task
def send_reminders(user_id):
    try:
        reminder_bot = get_bot()
        tasks = get_tasks(user_id=user_id)
        now = datetime.now()

        for task in tasks:
            if task.is_completed:
                logger.info(f"Задача '{task.description}' выполнена, напоминания не требуются.")
                continue

            time_until_deadline = (task.deadline - now).total_seconds()

            if task.reminder_sent:  # Проверяем, было ли уже отправлено напоминание
                continue

            if 0 < time_until_deadline <= 86400:
                run_async_task(reminder_bot, task.user_id,
                               f"Напоминание! Завтра истекает срок задачи '{task.description}'.")
            elif time_until_deadline <= 0:
                run_async_task(reminder_bot, task.user_id,
                               f"Напоминание! Срок задачи '{task.description}' истек.")
                task.reminder_sent = True  # Устанавливаем флаг после отправки
                send_reminders.apply_async((user_id,), countdown=REMIND_INTERVAL_AFTER_DEADLINE)
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминаний: {e}")

@app.task
def check_tasks_periodically():
    try:
        tasks = get_all_tasks()
        now = datetime.now()

        for task in tasks:
            if task.is_completed or task.reminder_sent:  # Проверяем, было ли уже отправлено напоминание
                continue

            countdown = (task.deadline - now).total_seconds()

            if countdown > 0:
                send_reminders.apply_async((task.user_id,), countdown=max(0, countdown))
            else:
                send_reminders.apply_async((task.user_id,), countdown=REMIND_INTERVAL_AFTER_DEADLINE)
    except Exception as e:
        logger.error(f"Ошибка при проверке задач: {e}")