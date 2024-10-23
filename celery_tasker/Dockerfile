FROM python:3.9-slim

WORKDIR /app

# Копируем файлы проекта в контейнер
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Команда для запуска Celery worker
CMD ["celery", "-A", "tasks.celery_app", "worker", "--loglevel=info"]