"""
Точка входа для запуска сервера. Запускается напрямую (python run_server.py),
без run_dev.ps1 - переменная окружения и config.py готовятся тут же.

uvicorn не учитывает asyncio.set_event_loop_policy() - свой event loop он
создаёт через собственную фабрику (uvicorn.loops.asyncio.asyncio_loop_factory),
которая на Windows жёстко возвращает ProactorEventLoop (если не включены
reload/workers). Поэтому нужный loop указывается явно через параметр loop.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

_FALLBACK_CONFIG_PATH = "/usr/share/porcelain-archive/config.ini"

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
    Ищет config.ini: сначала .secret/config.ini рядом с проектом, затем
    /usr/share/porcelain-archive/config.ini. Если ни один не найден,
    создаёт по второму пути пустой шаблон (только поля, без значений).
    """
    candidates = [
        os.path.join(ROOT, ".secret", "config.ini"),
        _FALLBACK_CONFIG_PATH,
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    fallback = candidates[-1]
    os.makedirs(os.path.dirname(fallback), exist_ok=True)
    with open(fallback, "w", encoding="utf-8") as f:
        f.write(_EMPTY_CONFIG_TEMPLATE)
    return fallback


if "ARCHIVE_CONFIG_INI_PATH" not in os.environ:
    os.environ["ARCHIVE_CONFIG_INI_PATH"] = _resolve_config_ini_path()

import generate_config
import uvicorn

generate_config.regenerate()

if __name__ == "__main__":
    loop = "asyncio:SelectorEventLoop" if sys.platform == "win32" else "auto"
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, loop=loop)
