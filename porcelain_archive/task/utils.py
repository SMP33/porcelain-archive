import re
import subprocess
from datetime import datetime
from typing import Optional
from pathlib import Path
from PIL import Image
import io
from PIL import Image
import io
import tempfile

import fitz
import psycopg
from psycopg.types.json import Jsonb

from porcelain_archive.config import config


def log(*args, **kwargs) -> None:
    """Печатает текущее время (чч:мм:сс) и переданные аргументы."""
    print(datetime.now().strftime("%H:%M:%S"), *args, **kwargs)


class _LoggingCursor(psycopg.Cursor):
    """Курсор, печатающий каждый выполняемый SQL-запрос."""

    def execute(self, query, params=None, **kwargs):
        log(f"SQL: {query} {params or ''}")
        return super().execute(query, params, **kwargs)


class BrokenImageError(Exception):
    """Файл изображения повреждён и не может быть декодирован."""


def compress_image(input_path, output_path, max_side, max_size_kb):
    max_size_bytes = max_size_kb * 1024

    try:
        img = Image.open(input_path)

        # Конвертируем в RGB, если есть альфа-канал/палитра, а сохранять будем в JPEG
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        # 1. Уменьшение до 1000px по большей стороне
        width, height = img.size
        scale = min(max_side / max(width, height), 1.0)  # не увеличиваем, если уже меньше
        if scale < 1.0:
            new_size = (int(width * scale), int(height * scale))
            img = img.resize(new_size, Image.LANCZOS)

        # 2. Подбор качества JPEG, чтобы уложиться в 400KB
        quality = 95
        buffer = io.BytesIO()

        while quality > 5:
            buffer.seek(0)
            buffer.truncate(0)
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            size = buffer.tell()
            if size <= max_size_bytes:
                break
            quality -= 5

        # 3. Если даже при низком качестве не влезли — дополнительно уменьшаем размер
        while buffer.tell() > max_size_bytes and max(img.size) > 200:
            img = img.resize((int(img.width * 0.9), int(img.height * 0.9)), Image.LANCZOS)
            buffer.seek(0)
            buffer.truncate(0)
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
    except Exception as exc:
        raise BrokenImageError(f"Не удалось обработать изображение '{input_path}': {exc}") from exc

    with open(output_path, "wb") as f:
        f.write(buffer.getvalue())


def validate_image(path) -> None:
    """Проверяет, что файл является корректным изображением. Бросает BrokenImageError, если нет."""
    try:
        with Image.open(path) as img:
            img.verify()
    except Exception as exc:
        raise BrokenImageError(f"Файл '{path}' не является корректным изображением: {exc}") from exc


PROGRESS_LOG_STEP = 50


def log_progress(current: int, total: int, message: str) -> None:
    """Логирует прогресс каждые PROGRESS_LOG_STEP шагов и на последнем шаге."""
    if current % PROGRESS_LOG_STEP == 0 or current == total:
        log(f"{message}: {current}/{total}")


def render_pdf_to_images(pdf_path: Path, output_dir: Path, start_num: int) -> int:
    """Рендерит каждую страницу PDF в PNG {start_num + i + 1}.png в output_dir. Возвращает число страниц."""
    with fitz.open(pdf_path) as pdf:
        total = pdf.page_count
        log(f"Рендеринг PDF в изображения: начало, страниц: {total}")
        for i, page in enumerate(pdf):
            pixmap = page.get_pixmap(dpi=200)
            pixmap.save(str(output_dir / f"{start_num + i + 1}.png"))
            log(f"Рендеринг PDF в изображения: {i + 1}/{total}")
        return total


def natural_sort_key(name: str):
    """Ключ естественной сортировки: числовые куски сравниваются как числа."""
    return [
        int(chunk) if chunk.isdigit() else chunk.lower()
        for chunk in re.split(r"(\d+)", name)
    ]


def list_position_files(branch_path: str, branch_name: str, folder: str) -> list[Path]:
    """Файлы из folder/ ветки с числом в имени, отсортированные по номеру."""
    out = run_git(
        branch_path, "ls-tree", "-r", "--name-only", branch_name, f"./{folder}"
    )
    files = out.stdout.splitlines()

    result = [
        Path(branch_path + "/" + file) for file in files if re.search(r"\d", file)
    ]
    result.sort(key=lambda file: natural_sort_key(file.name))
    return result


def shift_folder_files_up(
    branch_path: str, branch_name: str, folder: str, position: int, count: int
) -> None:
    """Сдвигает файлы folder/ ветки с номером больше position вверх на count."""
    files = list_position_files(branch_path, branch_name, folder)

    renames = []
    for file in files:
        old_position = int(file.stem)
        if position < old_position:
            new_name = f"{old_position + count}{file.suffix}"
            renames.append((f"{folder}/{file.name}", f"{folder}/{new_name}"))

    git_mv_no_checkout(branch_path, renames)


def remove_and_shift_folder_files(
    branch_path: str,
    branch_name: str,
    folder: str,
    remove_from: int,
    remove_to: int,
    shift: int,
) -> None:
    """Удаляет файлы folder/ ветки с номером в [remove_from, remove_to] и сдвигает файлы с номером больше remove_to вниз на shift."""
    files = list_position_files(branch_path, branch_name, folder)

    remove_paths = []
    renames = []
    for file in files:
        old_position = int(file.stem)
        if remove_from <= old_position <= remove_to:
            remove_paths.append(f"{folder}/{file.name}")
        elif old_position > remove_to:
            new_name = f"{old_position - shift}{file.suffix}"
            renames.append((f"{folder}/{file.name}", f"{folder}/{new_name}"))

    git_mv_no_checkout(branch_path, renames, extra_remove_paths=remove_paths)


def run_git(repo_path: str, *args: str) -> subprocess.CompletedProcess:
    """Выполняет git-команду в указанном репозитории/worktree."""
    command = ["git", "-C", repo_path, *args]

    log(" ".join(str(x) for x in command))
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} завершился с ошибкой:\n{result.stderr}"
        )
    return result


GIT_ARGS_CHUNK_SIZE = 200  # ограничивает длину командной строки git на один вызов


def _chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def git_mv_no_checkout(
    repo_path: str, renames: list[tuple[str, str]], extra_remove_paths: list[str] = None
) -> None:
    """
    Переименовывает набор файлов на уровне git-индекса за проход, без
    материализации файлов в рабочей директории (актуально для sparse-checkout,
    когда исходные файлы физически отсутствуют на диске). extra_remove_paths -
    дополнительные пути, которые нужно только убрать из индекса (без переименования).

    :param repo_path: путь к репозиторию или worktree
    :param renames: список пар (старый путь, новый путь)
    :param extra_remove_paths: пути, удаляемые из индекса без переименования
    """
    extra_remove_paths = extra_remove_paths or []
    if not renames and not extra_remove_paths:
        return

    log(f"Переименование в индексе: {len(renames)} файл(ов), удаление: {len(extra_remove_paths)} файл(ов)")

    old_paths = [old_path for old_path, _ in renames]
    blobs = {}

    if renames:
        # 1. Получаем режим доступа и hash blob'ов старых файлов из HEAD
        for chunk in _chunked(old_paths, GIT_ARGS_CHUNK_SIZE):
            result = run_git(repo_path, "ls-tree", "HEAD", "--", *chunk)

            # Формат строки: "<mode> <type> <hash>\t<path>"
            for line in result.stdout.splitlines():
                meta, path = line.split("\t", maxsplit=1)
                mode, _obj_type, blob_hash = meta.split(maxsplit=2)
                blobs[path] = (mode, blob_hash)

        missing = [old_path for old_path in old_paths if old_path not in blobs]
        if missing:
            raise FileNotFoundError(
                f"Файлы {missing} не найдены в HEAD репозитория {repo_path}"
            )

    # 2. Убираем старые пути из индекса. Делается до добавления новых путей: новый
    # путь одного файла может совпадать со старым путём другого - иначе git rm
    # --cached откажется его убирать.
    for chunk in _chunked(old_paths + extra_remove_paths, GIT_ARGS_CHUNK_SIZE):
        run_git(repo_path, "rm", "--cached", "--sparse", *chunk)

    # 3. Добавляем blob'ы под новыми путями в индекс (без чтения файлов с диска);
    # --cacheinfo можно повторять сколько угодно раз в одной команде
    for chunk in _chunked(renames, GIT_ARGS_CHUNK_SIZE):
        cacheinfo_args = []
        for old_path, new_path in chunk:
            mode, blob_hash = blobs[old_path]
            cacheinfo_args += ["--cacheinfo", f"{mode},{blob_hash},{new_path}"]
        if cacheinfo_args:
            run_git(repo_path, "update-index", "--add", *cacheinfo_args)

    log(f"Переименовано в индексе: {len(renames)} файл(ов), удалено: {len(extra_remove_paths)} файл(ов)")


def git_sparse_checkout_files(repo_path: str, files: list[str] = None) -> None:
    """
    Переключение ветки без материализации файлов
    """
    if not files:
        raise ValueError("Список файлов не должен быть пустым")

    normalized = [f"/{f.lstrip('/')}" for f in files]

    run_git(repo_path, "sparse-checkout", "set", "--no-cone", "**.gitkeep", *normalized)

    log(f"Sparse-checkout настроен на {len(files)} файл(ов)")


import hashlib
import subprocess
from pathlib import Path


def get_lfs_file_hash(repo_path: str, branch: str, file_path: str) -> str:
    """
    Возвращает sha256 (oid) LFS-файла на указанной ветке без материализации
    содержимого на диске — читает хэш прямо из текстового pointer'а.

    :param repo_path: путь к репозиторию
    :param branch: ветка/тег/коммит
    :param file_path: путь к файлу внутри репозитория
    """
    result = run_git(repo_path, "cat-file", "-p", f"{branch}:{file_path}")

    for line in result.stdout.splitlines():
        if line.startswith("oid sha256:"):
            return line.split("oid sha256:", maxsplit=1)[1].strip()

    raise ValueError(
        f"Файл '{file_path}' на ветке '{branch}' не является LFS pointer'ом"
    )


def get_regular_file_hash(repo_path: str, branch: str, file_path: str) -> str:
    """
    Возвращает sha256 реального содержимого обычного (не-LFS) файла
    на указанной ветке, без git-специфичного заголовка blob'а.

    :param repo_path: путь к репозиторию
    :param branch: ветка/тег/коммит
    :param file_path: путь к файлу внутри репозитория
    """
    result = subprocess.run(
        ["git", "-C", repo_path, "show", f"{branch}:{file_path}"],
        capture_output=True,
        check=True,
    )

    return hashlib.sha256(result.stdout).hexdigest()


def materialize_lfs_file(
    repo_path: str, branch: str, file_path: str, dest_path: str
) -> Path:
    """
    Материализует LFS-файл из указанной ветки в произвольное место
    вне репозитория, под указанным именем.

    Требует, чтобы LFS-объект был уже подтянут локально
    (см. run_git(repo_path, "lfs", "pull", "--include", file_path)).

    :param repo_path: путь к репозиторию
    :param branch: ветка/тег/коммит
    :param file_path: путь к файлу внутри репозитория
    :param dest_path: полный путь назначения (включая имя файла)
    """
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    pointer = subprocess.run(
        ["git", "-C", repo_path, "show", f"{branch}:{file_path}"],
        capture_output=True,
        check=True,
    )

    smudged = subprocess.run(
        ["git", "-C", repo_path, "lfs", "smudge"],
        input=pointer.stdout,
        capture_output=True,
        check=True,
    )

    dest.write_bytes(smudged.stdout)
    return dest


def materialize_regular_file(
    repo_path: str, branch: str, file_path: str, dest_path: str
) -> Path:
    """
    Материализует обычный (не-LFS) файл из указанной ветки в произвольное
    место вне репозитория, под указанным именем.

    :param repo_path: путь к репозиторию
    :param branch: ветка/тег/коммит
    :param file_path: путь к файлу внутри репозитория
    :param dest_path: полный путь назначения (включая имя файла)
    """
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["git", "-C", repo_path, "show", f"{branch}:{file_path}"],
        capture_output=True,
        check=True,
    )

    dest.write_bytes(result.stdout)
    return dest


def remove_branch_trash(branch_path):
    """
    Скрывает и удаляет лишние файлы для текущей ветки
    """
    run_git(branch_path, "sparse-checkout", "set", "--no-cone", "**.gitkeep")
    run_git(branch_path, "reset", "--hard", "HEAD")
    run_git(branch_path, "clean", "-fd")


def get_master_branch_id(document_id: int) -> Optional[int]:
    """Возвращает id ветки master документа."""
    conninfo = (
        f"dbname={config.database.dbname} "
        f"user={config.database.user} "
        f"password={config.database.password} "
        f"host={config.database.host} "
        f"port={config.database.port}"
    )

    with psycopg.connect(conninfo, cursor_factory=_LoggingCursor) as conn:
        cur = conn.execute(
            "SELECT id FROM branch WHERE document_id = %s AND name = 'master'",
            (document_id,),
        )
        row = cur.fetchone()

    return row[0] if row else None


def set_branch_merge_result(branch_id: int, success: bool) -> None:
    """Завершает слияние ветки: accepted при успехе, in_review при ошибке."""
    new_status = "accepted" if success else "in_review"

    conninfo = (
        f"dbname={config.database.dbname} "
        f"user={config.database.user} "
        f"password={config.database.password} "
        f"host={config.database.host} "
        f"port={config.database.port}"
    )

    with psycopg.connect(conninfo, cursor_factory=_LoggingCursor) as conn:
        conn.execute("UPDATE branch SET status = %s WHERE id = %s", (new_status, branch_id))
        # Смена статуса автоматическая (по результату задачи merge_branch), автор неизвестен.
        conn.execute(
            "INSERT INTO message (author_id, receiver_type, receiver_id, text, is_read, create_time) "
            "VALUES (NULL, 'branch_status', %s, %s, 0, now())",
            (branch_id, new_status),
        )


def regenerate_branch_cache(repo_path: str, branch_id: int, branch: Optional[str]):
    """
    Обновляет всю информацию о версии документа и кеш для нее
    """
    queries: list[tuple[str, tuple]] = []

    out = run_git(repo_path, "rev-parse", "--path-format=absolute", "--git-common-dir")
    log(f"Стартовый репозиторий {repo_path}")
    repo_path = Path(str(out.stdout) + "/../").resolve()
    log(f"Репозиторий {repo_path}")

    repo_branch = branch
    if repo_branch is None:
        repo_branch = "master"

    if branch_id is not None:
        commit_out = run_git(repo_path, "rev-parse", repo_branch)
        commit = commit_out.stdout.strip()

        # git ls-tree сортирует строки лексикографически (1, 10, 11, ..., 2, 20, ...),
        # а не по номеру страницы - нужна сортировка по имени файла (см. natural_sort_key).
        image_out = run_git(
            repo_path, "ls-tree", "-r", "--name-only", repo_branch, "./img"
        )
        image_files = sorted(
            (f for f in str(image_out.stdout).splitlines() if re.search(r"\d", f)),
            key=lambda f: natural_sort_key(Path(f).name),
        )

        doc_out = run_git(
            repo_path, "ls-tree", "-r", "--name-only", repo_branch, "./doc"
        )
        doc_files = sorted(
            (f for f in str(doc_out.stdout).splitlines() if re.search(r"\d", f)),
            key=lambda f: natural_sort_key(Path(f).name),
        )

        if len(image_files) != len(doc_files):
            raise ValueError(f"len(doc) != len(img)")

        page_count = len(image_files)

        cache_path = config.files.cache_path

        preview_image_cache_path = cache_path + "/preview"
        web_image_cache_path = cache_path + "/web"
        json_doc_cache_path = cache_path + "/json"

        for path in [preview_image_cache_path, web_image_cache_path, json_doc_cache_path]:
            Path(path).mkdir(parents=True, exist_ok=True)

        for pos in range(1, page_count + 1):
            image_file = image_files[pos - 1]
            doc_file = doc_files[pos - 1]

            image_hash = get_lfs_file_hash(repo_path, repo_branch, image_file)
            doc_hash = get_regular_file_hash(repo_path, repo_branch, doc_file)

            preview_image_path = preview_image_cache_path + "/" + image_hash + ".jpg"
            web_image_path = web_image_cache_path + "/" + image_hash + ".jpg"
            json_doc_path = json_doc_cache_path + "/" + doc_hash + ".json"
            
            if not Path(json_doc_path).exists():
                materialize_regular_file(repo_path, repo_branch, doc_file, json_doc_path)
            
            if not Path(web_image_path).exists() or not Path(preview_image_path).exists():
                try:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        src_path = tmp_dir + "/" + Path(image_file).name
                        log(src_path)

                        materialize_lfs_file(repo_path, repo_branch, image_file, src_path)
                        compress_image(src_path, web_image_path, 2000, 400)
                        compress_image(src_path, preview_image_path, 200, 40)
                except BrokenImageError as exc:
                    log(f"ПРОПУЩЕНО (страница {pos}, {image_file}): {exc}")
                    Path(web_image_path).unlink(missing_ok=True)
                    Path(preview_image_path).unlink(missing_ok=True)
                    continue

            log_progress(pos, page_count, "Обновление кеша страниц")

            queries.append(
                (
                    "INSERT INTO page (commit, pos, image_hash, text_hash, image_file, text_file) "
                    "VALUES (%s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (commit, pos) DO NOTHING",
                    (commit, pos, image_hash, doc_hash, Path(image_file).name, Path(doc_file).name),
                )
            )

        log(image_files)
        log(doc_files)

        branch_meta = {"page_count": page_count}
        queries.append(
            (
                "UPDATE branch SET meta = %s, last_change_time = NOW(), last_commit = %s, "
                "initial_commit = COALESCE(initial_commit, %s) WHERE id = %s",
                (Jsonb(branch_meta), commit, commit, branch_id),
            )
        )
    if len(queries) == 0:
        return

    conninfo = (
        f"dbname={config.database.dbname} "
        f"user={config.database.user} "
        f"password={config.database.password} "
        f"host={config.database.host} "
        f"port={config.database.port}"
    )

    with psycopg.connect(conninfo, cursor_factory=_LoggingCursor) as conn:
        for query in queries:
            conn.execute(*query)
