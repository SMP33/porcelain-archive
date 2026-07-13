"""
Точка входа для запуска сервера. Запускается напрямую (python -m porcelain_archive),
без run_dev.ps1 - переменная окружения и config.py готовятся тут же.

uvicorn не учитывает asyncio.set_event_loop_policy() - свой event loop он
создаёт через собственную фабрику (uvicorn.loops.asyncio.asyncio_loop_factory),
которая на Windows жёстко возвращает ProactorEventLoop (если не включены
reload/workers). Поэтому нужный loop указывается явно через параметр loop.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_SECRET_CONFIG_PATH = os.path.join(ROOT, ".secret", "config.ini")
_HOME_CONFIG_PATH = os.path.expanduser("~/.config/porcelain-archive/config.ini")
_SYSTEM_CONFIG_PATH = "/usr/share/porcelain-archive/config.ini"

_EMPTY_CONFIG_TEMPLATE = """[Common]
root =

[Database]
host =
port =
dbname =
user =
password =

[Files]
repos_root =
repos_branch_root =
cache_path =
log_path =
"""


def _resolve_config_ini_path() -> str:
    """
    Ищет config.ini по приоритету:
    1. .secret/config.ini рядом с проектом (локальная разработка).
    2. Переменная окружения ARCHIVE_CONFIG_INI_PATH, если задана.
    3. ~/.config/porcelain-archive/config.ini.
    4. /usr/share/porcelain-archive/config.ini - если и его нет,
       создаётся пустой шаблон (только поля, без значений).
    """
    if os.path.exists(_SECRET_CONFIG_PATH):
        return _SECRET_CONFIG_PATH

    env_path = os.environ.get("ARCHIVE_CONFIG_INI_PATH")
    if env_path:
        return env_path

    if os.path.exists(_HOME_CONFIG_PATH):
        return _HOME_CONFIG_PATH

    if os.path.exists(_SYSTEM_CONFIG_PATH):
        return _SYSTEM_CONFIG_PATH

    os.makedirs(os.path.dirname(_SYSTEM_CONFIG_PATH), exist_ok=True)
    with open(_SYSTEM_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(_EMPTY_CONFIG_TEMPLATE)
    return _SYSTEM_CONFIG_PATH


os.environ["ARCHIVE_CONFIG_INI_PATH"] = _resolve_config_ini_path()

_config_ini_abspath = os.path.abspath(os.environ["ARCHIVE_CONFIG_INI_PATH"])
print(f'config.ini: "{_config_ini_abspath}"', flush=True)

from .config import generator
import uvicorn

generator.regenerate()

from .config import config

for _files_path in (
    config.files.repos_root,
    config.files.repos_branch_root,
    config.files.cache_path,
    config.files.log_path,
):
    os.makedirs(_files_path, exist_ok=True)

if __name__ == "__main__":
    loop = "asyncio:SelectorEventLoop" if sys.platform == "win32" else "auto"

    parser = argparse.ArgumentParser()
    # По умолчанию 127.0.0.1 - сервер доступен только через reverse proxy
    # (nginx и т.п.). Для тестового запуска без nginx (доступ напрямую по
    # IP:8000) передайте --host 0.0.0.0 (или задайте ARCHIVE_SERVER_HOST).
    parser.add_argument(
        "--host",
        default=os.environ.get("ARCHIVE_SERVER_HOST", "127.0.0.1"),
        help="Адрес для прослушивания (по умолчанию 127.0.0.1, для теста без nginx - 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("ARCHIVE_SERVER_PORT", "8000")),
        help="Порт для прослушивания (по умолчанию 8000)",
    )
    args = parser.parse_args()

    uvicorn.run("porcelain_archive.server:app", host=args.host, port=args.port, loop=loop)
