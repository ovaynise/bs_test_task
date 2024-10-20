from celery.schedules import crontab
from celery_app import app

app.conf.beat_schedule = {
    'check-tasks-every-5-minutes': {
        'task': 'celery_app.check_tasks_periodically',
        'schedule': crontab(minute='*/5'),
    },
}