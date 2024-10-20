from sqlalchemy import create_engine
import subprocess
import re
import redis


def extract_datetime(text: str):
    pattern = r'\d{2}-\d{2}-\d{4}-\d{2}-\d{2}'
    result = re.findall(pattern, text)
    return result[0] if result else None


def check_database():
    try:
        engine = create_engine("sqlite:///tasks.db")
        connection = engine.connect()
        connection.close()
        return True
    except Exception:
        return False


def check_redis():
    try:
        r = redis.Redis(host='redis', port=6379, db=0)  # Измените 'localhost' на 'redis'
        r.ping()
        return True
    except Exception:
        return False

def check_celery():
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'celery'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.strip() != b''
    except Exception:
        return False

def check_flower():
    try:
        result = subprocess.run(['curl', '-Is', 'http://flower:5555'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False