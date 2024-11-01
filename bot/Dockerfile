FROM python:3.9

# Устанавливаем рабочую директорию на корень приложения
WORKDIR /app

# Копируем всё содержимое проекта в рабочую директорию
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем PYTHONPATH, чтобы Python видел все модули в проекте
ENV PYTHONPATH=/app

# Установим переменную окружения для определения, какое приложение запускать
ENV APP_TYPE=bot

# Запуск бота или Celery в зависимости от переменной
CMD ["python" ,"main.py"]