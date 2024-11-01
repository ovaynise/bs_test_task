import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

import pytz


class OvayLogger:
    def __init__(self, name, log_file_path):
        self.logger = logging.getLogger(name)
        self.log_file_path = log_file_path
        self.setup_logging()

    def setup_logging(self):
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

        formatter = self.OvayFormatter(
            "[%(asctime)s - func:_%(filename)s.%(funcName)s- %(levelname)s ]:"
            "\n >> %(message)s <<\n ----"
        )
        self.logger.setLevel(logging.DEBUG)
        handler = RotatingFileHandler(
            self.log_file_path, maxBytes=50000000, backupCount=5
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    class OvayFormatter(logging.Formatter):
        def converter(self, timestamp):
            dt = datetime.fromtimestamp(timestamp)
            return dt.astimezone(pytz.timezone("Europe/Moscow"))

        def formatTime(self, record, datefmt=None):
            dt = self.converter(record.created)
            days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
            day_of_week = days[dt.weekday()]
            if datefmt:
                s = dt.strftime(datefmt)
            else:
                s = f"{day_of_week} {dt.strftime('%d.%m.%Y %H:%M:%S')}"
            return s

    def get_logger(self):
        return self.logger