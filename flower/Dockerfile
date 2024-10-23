# flower/Dockerfile

FROM python:3.9-slim

WORKDIR /app

# Копируем requirements.txt из корня проекта
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код из celery_tasker
COPY ../celery_tasker ./

# Команда для запуска Flower
CMD ["celery", "-A", "tasks.celery_app", "flower", "--loglevel=info", "--port=5555"]