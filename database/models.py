from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    user_id = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
