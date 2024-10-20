import os
from sqlalchemy import create_engine, inspect, exc
from sqlalchemy.orm import sessionmaker
from models import Base, Task
from bot_init import logger


DATABASE_URL = "sqlite:///tasks.db"

try:
    logger.debug('Подключение к базе данных...')
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    logger.debug('Подключение к базе данных успешно.')
    inspector = inspect(engine)
    logger.debug('Получаем список существующих таблиц...')
    existing_tables = inspector.get_table_names()
    logger.debug(f'Существующие таблицы: {existing_tables}')
    if not existing_tables:
        logger.info('Таблицы в БД не найдены. Начинаем создание таблиц...')
        try:
            Base.metadata.create_all(engine)
            logger.info('Таблицы успешно созданы в базе данных.')
        except exc.SQLAlchemyError as e:
            logger.error(f'Ошибка при создании таблиц: {e}')
    else:
        logger.debug('Таблицы уже существуют, создание не требуется.')

except exc.SQLAlchemyError as e:
    logger.error(f'Ошибка при подключении к базе данных: {e}')
except Exception as e:
    logger.error(f'Неизвестная ошибка: {e}')


def add_task(description, deadline, user_id):
    session = Session()
    logger.debug(f'Открыта сессия с базой данных: {session}.')
    try:
        task = Task(description=description, deadline=deadline, user_id=user_id)
        session.add(task)
        session.commit()
        session.refresh(task)
        logger.info(f'Задача {task} успешно добавлена в базу данных.')
        return task
    except Exception as e:
        logger.error(f"Ошибка при добавлении задачи в базу данных: {e}")
        session.rollback()
        return None
    finally:
        session.close()
        logger.debug(f'Закрыта сессия с базой данных: {session}.')


def get_tasks(user_id):
    session = Session()
    logger.debug(f'Открыта сессия с базой данных: {session}.')
    try:
        tasks = session.query(Task).filter_by(user_id=user_id, is_completed=False).all()
        logger.info(f'Получены таски: {tasks}.')
        return tasks
    finally:
        session.close()
        logger.debug(f'Закрыта сессия с базой данных: {session}.')

def get_all_tasks():
    session = Session()
    logger.debug(f'Открыта сессия с базой данных: {session}.')
    try:
        tasks = session.query(Task).filter_by(is_completed=False).all()
        logger.info(f'Получены таски: {tasks}.')
        return tasks
    finally:
        session.close()
        logger.debug(f'Закрыта сессия с базой данных: {session}.')

def complete_task(task_id):
    session = Session()
    logger.debug(f'Открыта сессия с базой данных: {session}.')
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if task:
            task.is_completed = True
            session.commit()
            return task
        return None
    except Exception as e:
        logger.error(f"Ошибка при завершении задачи: {e}")
        session.rollback()
        return None
    finally:
        session.close()
        logger.debug(f'Закрыта сессия с базой данных: {session}.')

def delete_task(task_id):
    session = Session()
    logger.debug(f'Открыта сессия с базой данных: {session}.')
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if task:
            session.delete(task)
            session.commit()
            logger.info(f"Задача {task_id} успешно удалена.")
            return task
        return None
    except Exception as e:
        logger.error(f"Ошибка при удалении задачи: {e}")
        session.rollback()
        return None
    finally:
        session.close()
        logger.debug(f'Закрыта сессия с базой данных: {session}.')
