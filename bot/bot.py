from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import LOG_PATCH
from core.core import extract_datetime
from core.logger import OvayLogger
from database.db import Database

logger = OvayLogger(
    name='bot_logger', log_file_path=LOG_PATCH
).get_logger()


class TaskBot:
    def __init__(self, application: Application, database: Database):
        self.database = database
        self.application = application

    async def start(self, update: Update,
                    context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.debug(f'Запущена команда /start')
        user = update.effective_user
        await update.message.reply_text(
            f'Привет, {user.first_name}! Используй команды /add, /list,'
            f' /complete, /delete для управления задачами.'
        )

    def validate_add_command(self, args):
        if len(args) < 1:
            return False, ('Используй команду в формате: /add'
                           ' Описание DD-MM-YYYY-HH-MM')
        return True, None

    def validate_date(self, input_text):
        date_str = extract_datetime(input_text)
        if not date_str:
            return False, ('🟧Даты не найдены. Проверьте формат:'
                           ' "текст DD-MM-YYYY-HH-MM"')
        return True, date_str

    async def add_task(self, update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.debug(f'Запущена команда /add с аргументами: {context.args}')
        try:
            valid, message = self.validate_add_command(context.args)
            if not valid:
                await update.message.reply_text(message)
                return

            input_text = ' '.join(context.args)
            valid, date_str_or_message = self.validate_date(input_text)
            if not valid:
                await update.message.reply_text(date_str_or_message)
                return

            description = input_text.replace(date_str_or_message,
                                             '').strip()
            deadline = datetime.strptime(date_str_or_message,
                                         '%d-%m-%Y-%H-%M')

            logger.info(f'Добавление задачи: {description},'
                        f' срок: {deadline}')
            task = self.database.add_task(description, deadline,
                                          update.effective_user.id)

            if task:
                logger.info(f'🟩Задача успешно создана: {task}')
                await update.message.reply_text(
                    f'🟩Задача успешно создана:\nОписание: {task.description}\n'
                    f'Дата выполнения:'
                    f' {task.deadline.strftime("%d-%m-%Y %H:%M")}'
                )
            else:
                logger.error('🟥Не удалось создать задачу.')
                await update.message.reply_text('🟥Произошла ошибка при '
                                                'добавлении задачи.')

        except Exception as e:
            logger.error(f'🟥Ошибка при добавлении задачи: {e}')
            await update.message.reply_text('🟥Произошла ошибка при '
                                            'добавлении задачи.')

    def validate_task_id(self, args):
        try:
            task_id = int(args[0])
            return True, task_id
        except (IndexError, ValueError):
            return False, 'Используй команду в формате: /complete task_id'

    async def complete_task(self, update: Update,
                            context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.debug(f'Запущена команда /complete')
        valid, result = self.validate_task_id(context.args)
        if not valid:
            await update.message.reply_text(result)
            return

        task_description = self.database.complete_task(result)
        if task_description:
            await update.message.reply_text(
                f'Задача "{task_description}" отмечена как выполненная.')
        else:
            await update.message.reply_text('Задача не найдена.')

    async def delete_task(self, update: Update,
                          context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.debug(f'Запущена команда /delete')
        valid, result = self.validate_task_id(context.args)
        if not valid:
            await update.message.reply_text(result)
            return

        task = self.database.delete_task(result)
        if task:
            await update.message.reply_text(f'🟩Задача "{task.description}"'
                                            f' удалена.')
        else:
            await update.message.reply_text('Задача не найдена.')

    async def list_tasks(self, update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.debug(f'Запущена команда /list')
        user_id = update.effective_user.id
        tasks = self.database.get_tasks(user_id)
        if tasks:
            message = 'Ваши задачи:\n' + '\n'.join([
                f'{task.id}. {task.description} - '
                f'{task.deadline.strftime("%d-%m-%Y %H:%M")}'
                for task in tasks
            ])
        else:
            message = 'У вас нет активных задач.'
        await update.message.reply_text(message)

    def run(self):
        self.application.add_handler(
            CommandHandler('start', self.start))
        self.application.add_handler(
            CommandHandler('add', self.add_task))
        self.application.add_handler(
            CommandHandler('list', self.list_tasks))
        self.application.add_handler(
            CommandHandler('complete', self.complete_task))
        self.application.add_handler(
            CommandHandler('delete', self.delete_task))
        logger.info('Бот запустился')
        print('Бот запустился')
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
