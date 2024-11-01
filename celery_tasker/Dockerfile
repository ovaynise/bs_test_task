FROM python:3.9

# Устанавливаем рабочую директорию на корень приложения
WORKDIR /app

# Копируем всё содержимое проекта в рабочую директорию
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем PYTHONPATH, чтобы Python видел все модули в проекте
ENV PYTHONPATH=/app

# Запуск Celery worker
CMD ["celery", "-A", "tasks:celery_app", "worker", "--loglevel=info"]