# Архив

Архив документов: FastAPI (backend) + Vue3/Vuetify SPA на Vite (frontend, `frontend/`).

## Системные зависимости (ставятся вручную, требуют sudo)

`install.sh` их не устанавливает сам — только проверяет наличие и подсказывает команду, если чего-то не хватает. Перед первым запуском поставьте на Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y git git-lfs python3-venv python3-pip postgresql postgresql-contrib
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

PostgreSQL нужно настроить отдельно (создать БД и пользователя) - хост/порт/имя БД/логин/пароль потом указываются в `config.ini` (раздел `[Database]`).

## Установка проекта

```bash
./install.sh
```

Создаёт `.venv` и ставит python-зависимости из `requirements.txt`, проверяет git/git-lfs (и настраивает `user.name`/`user.email`, если не заданы), проверяет node/npm. Также создаёт пустой шаблон `/usr/share/porcelain-archive/config.ini` (требует sudo для создания каталога, дальше файл принадлежит текущему пользователю).

После этого заполните `/usr/share/porcelain-archive/config.ini`:

```ini
[Common]
root = /path/to/archive

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
```

## Запуск / остановка (Linux)

```bash
./start.sh   # пересобирает frontend (npm install + npm run build) и запускает backend на 127.0.0.1:8000
./stop.sh    # останавливает
```

Таблицы БД (`create_tables.sql`, `create_triggers.sql`, `fill_initial_data.sql`) накатываются автоматически при каждом старте сервера - вручную накатывать не нужно.

Снаружи backend должен отдаваться через reverse proxy (nginx и т.п.), проксирующий на `127.0.0.1:8000` (включая апгрейд WebSocket для `/api/tasks/ws`).

## Запуск / остановка (Windows, разработка)

```powershell
./start.ps1   # backend (порт 8000) + frontend dev-сервер с hot-reload (порт 5173, проксирует /api на backend)
./stop.ps1
```
