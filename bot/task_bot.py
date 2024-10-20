import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from db import (add_task, get_tasks, complete_task, delete_task, engine,
                get_all_tasks)
from celery_app import send_reminders
from bot_init import get_bot, logger
from core import (extract_datetime, check_database, check_redis, check_celery,
                  check_flower)
from models import Base


class TaskBot:
    def __init__(self):
        self.bot = get_bot()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.debug(f"Запущена команда /start")
        user = update.effective_user
        await update.message.reply_text(
            f"Привет, {user.first_name}! Используй команды /add, /list, /complete, /delete для управления задачами."
        )

    async def add_task(self, update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.debug(f"Запущена команда /add с аргументами: {context.args}")
        try:
            if len(context.args) < 1:
                await update.message.reply_text(
                    "Используй команду в формате: /add Описание DD-MM-YYYY-HH-MM"
                )
                return

            input_text = ' '.join(context.args)
            date_str = extract_datetime(input_text)

            if date_str:
                description = input_text.replace(date_str, '').strip()
                deadline = datetime.strptime(date_str, '%d-%m-%Y-%H-%M')

                logger.info(
                    f"Добавление задачи: {description}, срок: {deadline}")

                task = add_task(description, deadline,
                                update.effective_user.id)

                if task:
                    logger.info(f"Задача успешно создана: {task}")
                    await update.message.reply_text(
                        f"Задача успешно создана:\n"
                        f"Описание: {task.description}\n"
                        f"Дата выполнения: {task.deadline.strftime('%d-%m-%Y %H:%M')}"
                    )
                    # Логируем статус Redis и Celery
                    redis_status = check_redis()
                    celery_status = check_celery()
                    logger.info(
                        f'Redis status: {redis_status}, Celery status: {celery_status}')

                    if redis_status and celery_status:
                        countdown = (deadline - datetime.now()).total_seconds()
                        logger.info(
                            f"Запускаем напоминание с задержкой {countdown} секунд.")
                        send_reminders.apply_async((update.effective_user.id,),
                                                   countdown=countdown)
                    else:
                        await update.message.reply_text(
                            "Внимание! Для полноценной работы приложения необходим Redis."
                        )
                else:
                    logger.error("Не удалось создать задачу.")
                    await update.message.reply_text(
                        "Произошла ошибка при добавлении задачи.")
            else:
                await update.message.reply_text(
                    "Даты не найдены. Проверьте формат: 'текст DD-MM-YYYY-HH-MM'"
                )
        except Exception as e:
            logger.error(f"Ошибка при добавлении задачи: {e}")
            await update.message.reply_text(
                "Произошла ошибка при добавлении задачи.")

    async def list_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.debug(f"Запущена команда /list")
        user_id = update.effective_user.id
        tasks = get_tasks(user_id)
        if tasks:
            message = "Ваши задачи:\n" + "\n".join([
                f"{task.id}. {task.description} - {task.deadline.strftime('%d-%m-%Y %H:%M')}"
                for task in tasks
            ])
        else:
            message = "У вас нет активных задач."
        await update.message.reply_text(message)

    async def complete_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.debug(f"Запущена команда /complete")
        try:
            task_id = int(context.args[0])
            task = complete_task(task_id)
            if task:
                await update.message.reply_text(
                    f"Задача '{task.description}' отмечена как выполненная.")
            else:
                await update.message.reply_text("Задача не найдена.")
        except (IndexError, ValueError):
            await update.message.reply_text(
                "Используй команду в формате: /complete task_id")

    async def delete_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.debug(f"Запущена команда /delete")
        try:
            task_id = int(context.args[0])
            task = delete_task(task_id)
            if task:
                await update.message.reply_text(
                    f"Задача '{task.description}' удалена.")
            else:
                await update.message.reply_text("Задача не найдена.")
        except (IndexError, ValueError):
            await update.message.reply_text(
                "Используй команду в формате: /delete task_id")

    def run(self):
        application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("add", self.add_task))
        application.add_handler(CommandHandler("list", self.list_tasks))
        application.add_handler(CommandHandler("complete", self.complete_task))
        application.add_handler(CommandHandler("delete", self.delete_task))

        Base.metadata.create_all(engine)  # Убедись, что здесь правильно импортирован engine

        logger.info("Бот запустился")
        print('Бот запустился')

        db_status = check_database()
        logger.info(f"База данных доступна: {'Да' if db_status else 'Нет'}")

        redis_status = check_redis()
        logger.info(f"Redis - {'работает' if redis_status else 'не работает'}")

        celery_status = check_celery()
        logger.info(f"Celery - {'работает' if celery_status else 'не работает'}")

        flower_status = check_flower()
        if flower_status:
            logger.info(
                f"Flower - работает, ссылка: http://localhost:5555/tasks")
            print(f"Flower - работает, ссылка: http://localhost:5555/tasks")
        else:
            logger.info("Flower - не работает")
            print("Flower - не работает")

        # Вызов метода с self
        self.check_tasks_on_startup()

        application.run_polling(allowed_updates=Update.ALL_TYPES)

    def check_tasks_on_startup(self):
        logger.info("Проверка незавершённых задач при старте...")
        tasks = get_all_tasks()
        unique_user_ids = {task.user_id for task in tasks}
        logger.info(
            f"Найдено уникальных user_id с незавершёнными задачами: {unique_user_ids}")

        now = datetime.now()
        for user_id in unique_user_ids:
            user_tasks = get_tasks(user_id)
            for task in user_tasks:
                countdown = (task.deadline - now).total_seconds()
                if countdown > 0:
                    logger.info(
                        f'Добавляем задачу "{task.description}" в очередь с задержкой {countdown} секунд.')
                    result = send_reminders.apply_async((user_id,),
                                                        countdown=max(0,
                                                                      countdown))
                    logger.info(
                        f'Задача успешно добавлена в очередь. ID задачи: {result.id}')
                else:
                    send_reminders.apply_async((user_id,), countdown=0)
                    logger.info(f'Задача {task.description} уже просрочена.')


if __name__ == "__main__":
    logger.debug("Cтарт main")
    bot = TaskBot()
    logger.debug("Создан экземпляр бота")
    bot.run()
    logger.debug("Запущен бот run")