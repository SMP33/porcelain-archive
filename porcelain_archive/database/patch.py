from typing import Awaitable, Callable, List

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

# Проверка условия патча: получает соединение, возвращает список SQL-команд,
# которые нужно выполнить (пустой список - если изменение БД не требуется).
PatchCheck = Callable[[AsyncConnection], Awaitable[List[str]]]


class Patch:
    def __init__(self, patch_uuid: str, check: PatchCheck):
        self.uuid = patch_uuid
        self.check = check


# Патчи схемы БД для случаев, не покрытых IF NOT EXISTS в create_tables.sql.
# Список пуст - все патчи, ранее выполнявшиеся через patch_tables.sql, уже
# применены на всех известных БД (см. database_backup.sql) и перенесены
# напрямую в create_tables.sql.
PATCHES: List[Patch] = []


async def apply_patches(pool: AsyncConnectionPool) -> None:
    """
    Применяет неприменённые патчи из PATCHES по одному, каждый - в своей транзакции.
    Для патча без записи в таблице patch: выполняется его проверка условия,
    затем полученные SQL-команды, затем вставка uuid патча в таблицу.
    """
    for patch in PATCHES:
        async with pool.connection() as conn:
            cursor = await conn.execute("SELECT 1 FROM patch WHERE uuid = %s", (patch.uuid,))
            if await cursor.fetchone():
                continue

            commands = await patch.check(conn)
            for command in commands:
                await conn.execute(command)

            await conn.execute("INSERT INTO patch (uuid) VALUES (%s)", (patch.uuid,))
