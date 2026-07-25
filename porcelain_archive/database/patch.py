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


async def _column_exists(conn: AsyncConnection, table: str, column: str) -> bool:
    cursor = await conn.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
        (table, column),
    )
    return await cursor.fetchone() is not None


async def _table_exists(conn: AsyncConnection, table: str) -> bool:
    cursor = await conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = %s", (table,)
    )
    return await cursor.fetchone() is not None


async def _check_property_type_migration(conn: AsyncConnection) -> List[str]:
    """
    property: is_system убран, is_list заменён на type. document_property:
    значение указателя хранится напрямую (property_id, value) вместо ссылки
    на property_enum - на случай существующей БД, созданной до этого изменения.
    """
    commands: List[str] = []

    if await _column_exists(conn, "property", "is_system"):
        commands += [
            "ALTER TABLE property ADD COLUMN IF NOT EXISTS type TEXT DEFAULT 'string'",
            "UPDATE property SET type = CASE WHEN is_list = 1 THEN 'multicheckbox' ELSE 'string' END",
            "UPDATE property SET is_editable = 1",
            "ALTER TABLE property DROP COLUMN IF EXISTS is_system",
            "ALTER TABLE property DROP COLUMN IF EXISTS is_list",
        ]

    if await _table_exists(conn, "property_enum"):
        commands += [
            "ALTER TABLE document_property ADD COLUMN IF NOT EXISTS property_id "
            "BIGINT REFERENCES property (id) ON DELETE SET NULL",
            "ALTER TABLE document_property ADD COLUMN IF NOT EXISTS value TEXT",
            # Перенос значений, уже проставленных документам.
            """
            UPDATE document_property dp
            SET property_id = pe.property_id, value = pe.value
            FROM property_enum pe
            WHERE dp.property_enum_id = pe.id
            """,
            # Перенос всех прежних допустимых значений (property_enum) в пул
            # доступных значений - строки document_property с document_id = NULL.
            """
            INSERT INTO document_property (document_id, property_id, value)
            SELECT NULL, pe.property_id, pe.value FROM property_enum pe
            """,
            "ALTER TABLE document_property DROP COLUMN IF EXISTS property_enum_id",
            "DROP TABLE IF EXISTS property_enum",
        ]

    return commands


async def _check_document_property_indexes(conn: AsyncConnection) -> List[str]:
    return [
        "CREATE INDEX IF NOT EXISTS idx_document_property_property_value "
        "ON document_property (property_id, value)",
        "CREATE INDEX IF NOT EXISTS idx_document_property_document_property "
        "ON document_property (document_id, property_id)",
    ]


# Патчи схемы БД для случаев, не покрытых IF NOT EXISTS в create_tables.sql.
# Порядок важен: индексы полагаются на колонки, которые могла добавить
# предыдущая миграция.
PATCHES: List[Patch] = [
    Patch("23747d75-94ca-4f56-8da4-267490da41ed", _check_property_type_migration),
    Patch("9f8b4fbc-692b-4cf5-908c-0ba026218b35", _check_document_property_indexes),
]


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
