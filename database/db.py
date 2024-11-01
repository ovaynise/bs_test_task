from datetime import datetime

from sqlalchemy import create_engine, exc, inspect
from sqlalchemy.orm import sessionmaker

from config import LOG_PATCH
from core.logger import OvayLogger
from database.models import Base, Task

logger = OvayLogger(
    name="bd_logger", log_file_path=LOG_PATCH
).get_logger()


class Database:
    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.init_db()

    def init_db(self):
        try:
            logger.debug('Подключение к базе данных...')
            inspector = inspect(self.engine)
            logger.debug('Получаем список существующих таблиц...')
            existing_tables = inspector.get_table_names()
            logger.debug(f'Существующие таблицы: {existing_tables}')
            if not existing_tables:
                logger.info('🟧Таблицы в БД не найдены. Начинаем '
                            'создание таблиц...')
                try:
                    Base.metadata.create_all(self.engine)
                    logger.info('🟩Таблицы успешно созданы в базе данных.')
                except exc.SQLAlchemyError as e:
                    logger.error(f'🛑Ошибка при создании таблиц: {e}')
            else:
                logger.debug('🟩Таблицы уже существуют, создание не требуется.')
        except exc.SQLAlchemyError as e:
            logger.error(f'🛑Ошибка при подключении к базе данных: {e}')
        except Exception as e:
            logger.error(f'🛑Неизвестная ошибка: {e}')

    def _get_session(self):
        session = self.Session()
        logger.debug('🟦Открываем сессию к базе данных...')
        return session

    def close_session(self, session):
        session.close()
        logger.debug('🟦Закрываем соединение с базой данных.')

    def validate_description(self, description: str) -> bool:
        """Валидация описания задачи."""
        if not isinstance(description, str) or not description:
            logger.error("🛑Не удалось валидировать полученные данные БД: "
                         f"описание должно быть непустой строкой.\n "
                         f"Передано {description}"
                         f" c типом данных {type(description)}")
            return False
        return True

    def validate_deadline(self, deadline) -> bool:
        """Валидация срока выполнения задачи."""
        if not isinstance(deadline, (str, datetime)):
            logger.error("🛑Не удалось валидировать полученные данные БД:"
                         "  срок должен быть строкой"
                         f" или объектом datetime.\n Передано {datetime}"
                         f" c типом данных {type(datetime)}")
            return False
        return True

    def validate_user_id(self, user_id: int) -> bool:
        """Валидация user_id."""
        if not isinstance(user_id, int) or user_id < 1:
            logger.error("🛑Не удалось валидировать полученные данные БД: "
                         " user_id должен быть "
                         f"целым числом и больше 0.\n Передано {user_id}"
                         f" c типом данных {type(user_id)}")
            return False
        return True

    def validate_task_id(self, task_id: int) -> bool:
        """Валидация task_id."""
        if not isinstance(task_id, int) or task_id < 1:
            logger.error("🛑Не удалось валидировать полученные данные БД: "
                         " task_id должен быть "
                         "целым числом и больше 0..\n Передано {task_id}"
                         f" c типом данных {type(task_id)}")
            return False
        return True

    def add_task(self, description, deadline, user_id):
        if not (self.validate_description(description) and
                self.validate_deadline(deadline) and
                self.validate_user_id(user_id)):
            return None

        with self._get_session() as session:
            try:
                task = Task(description=description,
                            deadline=deadline,
                            user_id=user_id)
                session.add(task)
                session.commit()
                session.refresh(task)
                logger.info(f'🟩Задача {task} успешно добавлена в базу данных.')
                return task
            except Exception as e:
                logger.error(f"🛑Ошибка при добавлении задачи в базу "
                             f"данных: {e}")
                session.rollback()
                return None
            finally:
                self.close_session(session)

    def complete_task(self, task_id):
        if not self.validate_task_id(task_id):
            return None

        with self._get_session() as session:
            try:
                task = session.query(Task).filter_by(id=task_id).first()
                if task:
                    task.is_completed = True
                    session.commit()
                    logger.info(f'🟩Задача {task_id} успешно завершена.')
                    return task.description
                return None
            except Exception as e:
                logger.error(f"🛑Ошибка при завершении задачи: {e}")
                session.rollback()
                return None
            finally:
                self.close_session(session)

    def delete_task(self, task_id):
        if not self.validate_task_id(task_id):
            return None

        with self._get_session() as session:
            try:
                task = session.query(Task).filter_by(id=task_id).first()
                if task:
                    session.delete(task)
                    session.commit()
                    logger.info(f"🟩Задача {task_id} успешно удалена.")
                    return task
                else:
                    logger.warning(
                        f"🟧Попытка удалить задачу {task_id}, но"
                        f" она не найдена в БД.")
                    return None
            except Exception as e:
                logger.error(f"🛑Ошибка при удалении задачи: {e}")
                session.rollback()
                return None
            finally:
                self.close_session(session)

    def get_tasks(self, user_id):
        if not self.validate_user_id(user_id):
            return None

        with self._get_session() as session:
            try:
                user_exists = session.query(Task).filter_by(
                    user_id=user_id).first()
                if not user_exists:
                    logger.warning(
                        f"🟧Пользователь с user_id {user_id} не найден.")
                    return None
                tasks = session.query(Task).filter_by(user_id=user_id,
                                                      is_completed=False).all()
                if tasks:
                    logger.info(
                        f'Получены задачи для пользователя {user_id}: {tasks}.')
                else:
                    logger.warning(
                        f"🟧Задачи для пользователя {user_id} не найдены.")
                return tasks
            except Exception as e:
                logger.error(
                    f"🛑Ошибка при получении задач для пользователя"
                    f"{user_id}: {e}")
                return None
            finally:
                self.close_session(session)

    def get_all_not_completed_tasks(self):
        with self._get_session() as session:
            try:
                tasks = session.query(Task).filter_by(is_completed=False).all()
                logger.info(f'Получены все незавершенные задачи: {tasks}.')
                return tasks
            except Exception as e:
                logger.error(f"🛑Ошибка при получении всех задач: {e}")
                return None
            finally:
                self.close_session(session)

    def get_all_user_ids(self):
        with self._get_session() as session:
            try:
                user_ids = session.query(Task.user_id).distinct().all()
                logger.info(f'Получены все уникальные user_id: {user_ids}.')
                return [user_id[0] for user_id in
                        user_ids]  # Извлекаем id из кортежей
            except Exception as e:
                logger.error(f"🛑Ошибка при получении всех user_id: {e}")
                return None
