"""Настройка логирования сервера: новый файл лога на каждый запуск."""
import logging
import os
from datetime import datetime

from .config import config

_current_log_file: str | None = None


def _generate_log_filename() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
    return f"{timestamp}.log"


def configure_logging() -> str:
    """
    Создаёт новый файл лога в config.files.log_path и направляет в него
    вывод стандартного logging (включая логи uvicorn - см. log_config=None
    в uvicorn.run в __main__.py). Возвращает путь к созданному файлу.
    """
    global _current_log_file

    os.makedirs(config.files.log_path, exist_ok=True)
    log_path = os.path.join(config.files.log_path, _generate_log_filename())

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _current_log_file = log_path
    return log_path


def get_current_log_file() -> str | None:
    return _current_log_file
