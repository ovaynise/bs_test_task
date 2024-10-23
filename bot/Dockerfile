FROM python:3.9

WORKDIR /app

# Копируем requirements.txt из корневой папки
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем содержимое папки bot
COPY bot/ .

# Установим переменную окружения для определения, какое приложение запускать
ENV APP_TYPE=bot

CMD ["sh", "-c", "if [ \"$APP_TYPE\" = 'bot' ]; then python main.py; else celery -A bot.celery_app.app $@; fi"]