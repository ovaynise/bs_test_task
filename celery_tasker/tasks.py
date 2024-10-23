from celery import Celery
from celery.schedules import crontab

REDIS_BROKER_URL = 'redis://redis:6379/0'

celery_app = Celery('tasks', broker=REDIS_BROKER_URL)

@celery_app.task
def someplus(x: int, y: int):
    c = x + y
    print(c)
    return c

@celery_app.task
def print_hello():
    print("Hello")


# Настройка периодической задачи
celery_app.conf.beat_schedule = {
    'print-hello-every-minute': {
        'task': 'tasks.print_hello',
        'schedule': crontab(minute='*'),
    },
}

celery_app.conf.timezone = 'UTC'
