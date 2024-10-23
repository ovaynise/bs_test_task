import os
from celery import Celery
from datetime import datetime, timedelta
from logger import OvayLogger
from config import (LOG_PATCH, REDIS_BROKER_URL, TELEGRAM_TOKEN)
from db import Database
import requests

# Логирование
logger = OvayLogger(name="celery_logger", log_file_path=LOG_PATCH).get_logger()

# Переменные для настройки напоминаний
TEXT_TO_SEND_ALL = "Это общее сообщение для всех пользователей."
REMINDER_BEFORE_DEADLINE = 86400  # Напоминание за день
REMINDER_INTERVAL = 60  # Интервал для повторного напоминания, если задача просрочена

app = Celery('tasks', broker=REDIS_BROKER_URL)
app.conf.broker_connection_retry_on_startup = True

# Получаем имя worker'а из переменной окружения
worker_name = os.getenv('WORKER_NAME', 'unknown_worker')

# Функция для отправки напоминания
def send_reminder(user_id, message):
    logger.info(f"Отправляем напоминание пользователю {user_id} от {worker_name}: {message}")
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            data={'chat_id': user_id, 'text': message}
        )
        response.raise_for_status()
        logger.info(f"Сообщение успешно отправлено пользователю {user_id}. Ответ: {response.text}")
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP ошибка при отправке сообщения пользователю {user_id}: {http_err}")
    except Exception as err:
        logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {err}")

# Задача для отправки напоминаний
@app.task
def send_reminders():
    logger.info(f"Запускается проверка задач от {worker_name}...")

    # Подключаемся к базе данных
    database = Database("sqlite:///tasks.db")
    tasks = database.get_all_tasks()

    if tasks is None:
        logger.error("Не удалось получить задачи из базы данных.")
        return

    logger.debug(f"Найдено задач: {len(tasks)}")  # Логируем количество задач

    now = datetime.now()
    has_overdue_tasks = False  # Флаг для отслеживания просроченных задач

    for task in tasks:
        logger.debug(
            f"Проверяем задачу: {task.description}, выполнено: {task.is_completed}, дедлайн: {task.deadline}")

        if task.is_completed:
            logger.info(
                f"Не отправлено: Задача '{task.description}' выполнена.")
            continue

        time_until_deadline = (task.deadline - now).total_seconds()

        # Напоминание за день до дедлайна
        if 0 < time_until_deadline <= REMINDER_BEFORE_DEADLINE and not task.reminder_sent:
            logger.debug(
                f"Отправляем напоминание за день до дедлайна: '{task.description}'")
            send_reminder(task.user_id,
                          f"Напоминание: Срок задачи '{task.description}' истекает через день!")
            task.reminder_sent = True
            database.update_task(task)

        # Просроченные задачи
        elif time_until_deadline < 0:
            logger.debug(
                f"Отправляем уведомление о просроченной задаче: '{task.description}'")
            send_reminder(task.user_id,
                          f"Срок задачи '{task.description}' истек!")
            has_overdue_tasks = True

    if has_overdue_tasks:
        logger.info(
            "Есть просроченные задачи, отправляем повторные напоминания через минуту.")
        send_reminders.apply_async(countdown=REMINDER_INTERVAL)
    else:
        logger.info("Нет просроченных задач.")

# Задача для отправки общего сообщения
@app.task
def send_general_message():
    logger.info(f"Отправляем общее сообщение всем пользователям от {worker_name}...")
    database = Database("sqlite:///tasks.db")
    user_ids = database.get_all_user_ids()

    unique_user_ids = set(user_ids)
    logger.info(f"Уникальные user_id для отправки: {unique_user_ids}")

    for user_id in unique_user_ids:
        logger.info(f"Отправляем сообщение пользователю {user_id} от {worker_name}")
        send_reminder(user_id, TEXT_TO_SEND_ALL)

# Настройка периодических задач Celery
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    logger.info("Настройка периодических задач...")
    send_general_message.apply_async(countdown=0)  # Отправляем общее сообщение сразу
    logger.info("Общее сообщение отправлено.")
    # Запускаем задачу раз в минуту
    sender.add_periodic_task(60.0, send_reminders.s(), name='send-reminders-every-minute')
    logger.info("Периодическая задача send_reminders добавлена.")