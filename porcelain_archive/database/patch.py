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
    property: is_system убран, is_list заменён на type, добавлен is_usable.
    document_property: значение указателя хранится напрямую (tag, value)
    вместо ссылки на property_enum - на случай существующей БД, созданной
    до этого изменения.
    """
    commands: List[str] = []

    has_property_enum = await _table_exists(conn, "property_enum")

    if await _column_exists(conn, "property", "is_system"):
        commands += [
            "ALTER TABLE property ADD COLUMN IF NOT EXISTS type TEXT DEFAULT 'string'",
            "ALTER TABLE property ADD COLUMN IF NOT EXISTS is_usable INTEGER DEFAULT 1",
        ]
        if has_property_enum:
            # Указатель, у которого уже есть допустимые значения - combobox
            # (или multicheckbox, если раньше допускал несколько значений).
            commands.append(
                """
                UPDATE property p SET type = CASE
                    WHEN EXISTS (SELECT 1 FROM property_enum pe WHERE pe.property_id = p.id)
                        THEN CASE WHEN p.is_list = 1 THEN 'multicheckbox' ELSE 'combobox' END
                    ELSE 'string'
                END
                """
            )
        else:
            commands.append(
                "UPDATE property SET type = CASE WHEN is_list = 1 THEN 'multicheckbox' ELSE 'string' END"
            )
        commands += [
            # Старый is_editable отвечал и за использование в документах -
            # переносим его в новый is_usable, а is_editable (теперь - только
            # про редактирование списка значений) делаем открытым всем.
            "UPDATE property SET is_usable = is_editable",
            "UPDATE property SET is_editable = 1",
            "ALTER TABLE property DROP COLUMN IF EXISTS is_system",
            "ALTER TABLE property DROP COLUMN IF EXISTS is_list",
        ]

    if has_property_enum:
        commands += [
            "ALTER TABLE document_property ADD COLUMN IF NOT EXISTS tag "
            "TEXT REFERENCES property (tag) ON DELETE SET NULL",
            "ALTER TABLE document_property ADD COLUMN IF NOT EXISTS value TEXT",
            # Перенос значений, уже проставленных документам.
            """
            UPDATE document_property dp
            SET tag = p.tag, value = pe.value
            FROM property_enum pe
            JOIN property p ON p.id = pe.property_id
            WHERE dp.property_enum_id = pe.id
            """,
            # Перенос всех прежних допустимых значений (property_enum) в пул
            # доступных значений - строки document_property с document_id = NULL.
            """
            INSERT INTO document_property (document_id, tag, value)
            SELECT NULL, p.tag, pe.value
            FROM property_enum pe
            JOIN property p ON p.id = pe.property_id
            """,
            "ALTER TABLE document_property DROP COLUMN IF EXISTS property_enum_id",
            "DROP TABLE IF EXISTS property_enum",
        ]

    return commands


async def _check_document_property_indexes(conn: AsyncConnection) -> List[str]:
    return [
        "CREATE INDEX IF NOT EXISTS idx_document_property_tag_value "
        "ON document_property (tag, value)",
        "CREATE INDEX IF NOT EXISTS idx_document_property_document_tag "
        "ON document_property (document_id, tag)",
    ]


async def _check_document_property_unique(conn: AsyncConnection) -> List[str]:
    """
    Убирает случайно продублированные строки document_property (например, из-за
    повторной отправки формы сохранения указателей документа) и добавляет
    UNIQUE (document_id, tag, value), чтобы такое дублирование стало
    невозможно на уровне БД.
    """
    return [
        """
        DELETE FROM document_property a
        USING document_property b
        WHERE a.ctid < b.ctid
          AND a.document_id IS NOT DISTINCT FROM b.document_id
          AND a.tag IS NOT DISTINCT FROM b.tag
          AND a.value IS NOT DISTINCT FROM b.value
        """,
        "ALTER TABLE document_property ADD CONSTRAINT document_property_unique "
        "UNIQUE NULLS NOT DISTINCT (document_id, tag, value)",
    ]


async def _check_property_is_system(conn: AsyncConnection) -> List[str]:
    """property.is_system - принудительная видимость указателя и защита от удаления."""
    return ["ALTER TABLE property ADD COLUMN IF NOT EXISTS is_system INTEGER DEFAULT 0"]


async def _check_drop_object_tables(conn: AsyncConnection) -> List[str]:
    """
    porcelain_object/object_image/object_property (отдельная сущность "объект" со
    своими фото и указателями) заменены документами с указателем
    document_type='object' (см. porcelain_archive/ceramic/objects) - на случай
    существующей БД, созданной до этого изменения. Данные объектов (если есть)
    не переносятся автоматически - таблицы удаляются вместе с данными.
    """
    if not await _table_exists(conn, "porcelain_object"):
        return []
    return [
        "DROP TABLE IF EXISTS object_property",
        "DROP TABLE IF EXISTS object_image",
        "DROP TABLE IF EXISTS porcelain_object",
    ]


# Патчи схемы БД для случаев, не покрытых IF NOT EXISTS в create_tables.sql.
# Порядок важен: индексы и ограничение уникальности полагаются на колонки
# (tag, value), которые могла добавить предыдущая миграция.
PATCHES: List[Patch] = [
    Patch("23747d75-94ca-4f56-8da4-267490da41ed", _check_property_type_migration),
    Patch("9f8b4fbc-692b-4cf5-908c-0ba026218b35", _check_document_property_indexes),
    Patch("06a3c7d2-3c1c-475f-9529-630e54635de9", _check_document_property_unique),
    Patch("d6d7f56b-e466-4603-b723-253b3f68dd69", _check_drop_object_tables),
    Patch("1a9d4b2e-5f7c-4a3d-8e9b-2c6f0d1a7b4e", _check_property_is_system),
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
