"""
Бэкап PostgreSQL с отправкой на резервный SSH-сервер (см. [StorageSSH] в config.ini).

Дампает базу через pg_dump, упаковывает дамп в zip-архив с текущим
таймштампом в названии и заливает его по SFTP на резервный сервер.
"""

import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime

import paramiko

from porcelain_archive.config import config
from porcelain_archive.task import TaskInfo
from porcelain_archive.task.utils import log

TaskInfo.from_stdin()

DUMP_FILENAME = "database_backup.sql"


def dump_database(tmp_dir: str) -> str:
    """Делает pg_dump в tmp_dir/DUMP_FILENAME, возвращает путь к файлу дампа."""
    if shutil.which("pg_dump") is None:
        raise RuntimeError("pg_dump не найден в PATH")

    dump_path = os.path.join(tmp_dir, DUMP_FILENAME)
    log(f"Делаю дамп базы {config.database.dbname} в {dump_path} ...")

    env = os.environ.copy()
    env["PGPASSWORD"] = config.database.password

    result = subprocess.run(
        [
            "pg_dump",
            "-h", config.database.host,
            "-p", str(config.database.port),
            "-U", config.database.user,
            "-F", "p",
            "-f", dump_path,
            config.database.dbname,
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump завершился с ошибкой:\n{result.stderr}")

    log(f"Дамп готов: {dump_path} ({os.path.getsize(dump_path)} байт)")
    return dump_path


def zip_dump(dump_path: str, tmp_dir: str) -> str:
    """Упаковывает файл дампа и папку repos_root в zip с таймштампом. Возвращает путь к архиву."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(tmp_dir, f"backup_{timestamp}.zip")

    repos_root = config.files.repos_root
    log(f"Упаковываю {dump_path} и {repos_root} в {zip_path} ...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(dump_path, os.path.basename(dump_path))

        repos_root_name = os.path.basename(os.path.normpath(repos_root))
        for root, _dirs, files in os.walk(repos_root):
            for filename in files:
                file_path = os.path.join(root, filename)
                arcname = os.path.join(repos_root_name, os.path.relpath(file_path, repos_root))
                zf.write(file_path, arcname)

    log(f"Архив готов: {zip_path} ({os.path.getsize(zip_path)} байт)")
    return zip_path


def ensure_remote_dir(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    """Аналог mkdir -p на удалённой стороне через SFTP."""
    path = ""
    for part in remote_dir.strip("/").split("/"):
        path += "/" + part
        try:
            sftp.stat(path)
        except FileNotFoundError:
            sftp.mkdir(path)


def upload_zip(zip_path: str) -> None:
    """Заливает архив на резервный сервер по SFTP (логин+пароль, без ssh-ключей)."""
    log(f"Подключаюсь к {config.storagessh.host} по SSH...")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=config.storagessh.host,
        username=config.storagessh.user,
        password=config.storagessh.password,
        look_for_keys=False,
        allow_agent=False,
        timeout=15,
    )

    sftp = client.open_sftp()
    try:
        ensure_remote_dir(sftp, config.storagessh.path)

        remote_path = f"{config.storagessh.path.rstrip('/')}/{os.path.basename(zip_path)}"
        log(f"Заливаю {zip_path} -> {config.storagessh.host}:{remote_path} ...")
        sftp.put(zip_path, remote_path)

        local_size = os.path.getsize(zip_path)
        remote_size = sftp.stat(remote_path).st_size
        if local_size != remote_size:
            raise RuntimeError(f"Размер не совпадает: локально {local_size}, на сервере {remote_size} байт")

        log(f"Загружено успешно, {remote_size} байт.")
    finally:
        sftp.close()
        client.close()


with tempfile.TemporaryDirectory() as tmp_dir:
    dump_path = dump_database(tmp_dir)
    zip_path = zip_dump(dump_path, tmp_dir)
    upload_zip(zip_path)

log("Бэкап завершён.")
