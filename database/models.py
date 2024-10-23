from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    user_id = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)