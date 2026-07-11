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

if "ARCHIVE_CONFIG_INI_PATH" not in os.environ:
    os.environ["ARCHIVE_CONFIG_INI_PATH"] = os.path.join(ROOT, ".secret", "config.ini")

import generate_config
import uvicorn

generate_config.regenerate()

if __name__ == "__main__":
    loop = "asyncio:SelectorEventLoop" if sys.platform == "win32" else "auto"
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, loop=loop)
