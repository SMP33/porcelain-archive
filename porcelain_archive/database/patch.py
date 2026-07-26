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


async def _check_document_status_values(conn: AsyncConnection) -> List[str]:
    """
    document_status: старые значения пула ('Закончен', 'Требуется проверка')
    заменяются кодами с переводом (in_work/need_help/finished), по аналогии с
    document_type. Уже проставленные документам значения переименовываются.
    """
    return [
        "UPDATE document_property SET value = 'finished' WHERE tag = 'document_status' AND value = 'Закончен'",
        "UPDATE document_property SET value = 'need_help' WHERE tag = 'document_status' AND value = 'Требуется проверка'",
        "INSERT INTO document_property (document_id, tag, value) VALUES (NULL, 'document_status', 'in_work') "
        "ON CONFLICT (document_id, tag, value) DO NOTHING",
        "DELETE FROM property_translate WHERE tag = 'document_status'",
        "INSERT INTO property_translate (tag, value, translated) VALUES "
        "('document_status', 'in_work', 'В работе'), "
        "('document_status', 'need_help', 'Нужны правки'), "
        "('document_status', 'finished', 'Закончен')",
    ]


async def _check_page_count_not_usable(conn: AsyncConnection) -> List[str]:
    """
    page_count вычисляется автоматически (regenerate_branch_cache) и не должен
    быть доступен для ручного изменения через общий редактор указателей -
    is_usable=0, как у document_type.
    """
    return ["UPDATE property SET is_usable = 0 WHERE tag = 'page_count'"]


async def _check_subjects_status_system_flags(conn: AsyncConnection) -> List[str]:
    """
    "Тематика" (subjects) - обычный указатель, не системный. "Статус документа"
    (document_status) - системный принудительно (см. property.is_system).
    """
    return [
        "UPDATE property SET is_system = 0 WHERE tag = 'subjects'",
        "UPDATE property SET is_system = 1 WHERE tag = 'document_status'",
    ]


async def _check_system_properties_backfill(conn: AsyncConnection) -> List[str]:
    """
    Каждому документу должны быть присвоены все системные указатели
    (property.is_system) - реальным значением или NULL-заглушкой, если оно ещё
    не задано (см. document_service.create_document). Документам без
    document_type/document_status присваиваются значения по умолчанию.
    """
    return [
        "INSERT INTO document_property (document_id, tag, value) "
        "SELECT d.id, 'document_type', 'historical_document' FROM document d "
        "WHERE NOT EXISTS ("
        "    SELECT 1 FROM document_property dp WHERE dp.document_id = d.id AND dp.tag = 'document_type'"
        ") ON CONFLICT (document_id, tag, value) DO NOTHING",
        "INSERT INTO document_property (document_id, tag, value) "
        "SELECT d.id, 'document_status', 'in_work' FROM document d "
        "WHERE NOT EXISTS ("
        "    SELECT 1 FROM document_property dp WHERE dp.document_id = d.id AND dp.tag = 'document_status'"
        ") ON CONFLICT (document_id, tag, value) DO NOTHING",
        "INSERT INTO document_property (document_id, tag, value) "
        "SELECT d.id, p.tag, NULL FROM document d CROSS JOIN property p "
        "WHERE p.is_system = 1 AND p.tag NOT IN ('document_type', 'document_status') "
        "AND NOT EXISTS ("
        "    SELECT 1 FROM document_property dp WHERE dp.document_id = d.id AND dp.tag = p.tag"
        ") ON CONFLICT (document_id, tag, value) DO NOTHING",
    ]


async def _check_backfill_last_change_and_page_count(conn: AsyncConnection) -> List[str]:
    """
    last_change_datetime и page_count заполняются/переставляются по данным,
    уже присутствующим в master-ветке документа (last_change_time,
    meta->>'page_count') - текущее проставленное значение заменяется.
    last_change_datetime - в формате YYYY-MM-DD (см. property_service.validate_value).
    """
    return [
        """
        DELETE FROM document_property dp
        USING branch b
        WHERE b.name = 'master' AND b.last_change_time IS NOT NULL
          AND dp.document_id = b.document_id AND dp.tag = 'last_change_datetime'
        """,
        """
        INSERT INTO document_property (document_id, tag, value)
        SELECT b.document_id, 'last_change_datetime', TO_CHAR(b.last_change_time, 'YYYY-MM-DD')
        FROM branch b
        WHERE b.name = 'master' AND b.last_change_time IS NOT NULL
        ON CONFLICT (document_id, tag, value) DO NOTHING
        """,
        """
        DELETE FROM document_property dp
        USING branch b
        WHERE b.name = 'master' AND b.meta ? 'page_count'
          AND dp.document_id = b.document_id AND dp.tag = 'page_count'
        """,
        """
        INSERT INTO document_property (document_id, tag, value)
        SELECT b.document_id, 'page_count', b.meta->>'page_count'
        FROM branch b
        WHERE b.name = 'master' AND b.meta ? 'page_count'
        ON CONFLICT (document_id, tag, value) DO NOTHING
        """,
    ]


async def _check_backfill_loaded_by_and_date(conn: AsyncConnection) -> List[str]:
    """
    loaded_date (дата первого принятого набора изменений документа, YYYY-MM-DD)
    и loaded_by (логин принявшего пользователя) не проставлялись для документов,
    у которых первый набор изменений был принят до появления этой логики
    (см. task.utils._set_loaded_properties_on_first_accept) - заполняются по уже
    существующему логу статусов веток (message, receiver_type='branch_status'):
    'accepted' - когда набор изменений был принят, 'in_accept' (ближайший по
    времени до 'accepted' для той же ветки) - кем.
    """
    return [
        """
        INSERT INTO document_property (document_id, tag, value)
        SELECT DISTINCT ON (b.document_id) b.document_id, 'loaded_date', TO_CHAR(am.create_time, 'YYYY-MM-DD')
        FROM branch b
        JOIN message am ON am.receiver_type = 'branch_status' AND am.receiver_id = b.id AND am."text" = 'accepted'
        WHERE b.name != 'master'
          AND NOT EXISTS (
              SELECT 1 FROM document_property dp
              WHERE dp.document_id = b.document_id AND dp.tag = 'loaded_date'
          )
        ORDER BY b.document_id, am.create_time ASC
        ON CONFLICT (document_id, tag, value) DO NOTHING
        """,
        # loaded_date/loaded_by - combobox, значения нужны и в пуле допустимых (document_id = NULL).
        """
        INSERT INTO document_property (document_id, tag, value)
        SELECT DISTINCT NULL, 'loaded_date', dp.value
        FROM document_property dp
        WHERE dp.tag = 'loaded_date' AND dp.document_id IS NOT NULL
        ON CONFLICT (document_id, tag, value) DO NOTHING
        """,
        """
        INSERT INTO document_property (document_id, tag, value)
        SELECT sub.document_id, 'loaded_by', m.name
        FROM (
            SELECT DISTINCT ON (b.document_id) b.document_id, b.id AS branch_id, am.create_time AS accepted_time
            FROM branch b
            JOIN message am ON am.receiver_type = 'branch_status' AND am.receiver_id = b.id AND am."text" = 'accepted'
            WHERE b.name != 'master'
            ORDER BY b.document_id, am.create_time ASC
        ) sub
        JOIN LATERAL (
            SELECT im.author_id
            FROM message im
            WHERE im.receiver_type = 'branch_status' AND im.receiver_id = sub.branch_id
              AND im."text" = 'in_accept' AND im.create_time <= sub.accepted_time
            ORDER BY im.create_time DESC LIMIT 1
        ) acc ON true
        JOIN member m ON m.id = acc.author_id
        WHERE NOT EXISTS (
            SELECT 1 FROM document_property dp
            WHERE dp.document_id = sub.document_id AND dp.tag = 'loaded_by'
        )
        ON CONFLICT (document_id, tag, value) DO NOTHING
        """,
        """
        INSERT INTO document_property (document_id, tag, value)
        SELECT DISTINCT NULL, 'loaded_by', dp.value
        FROM document_property dp
        WHERE dp.tag = 'loaded_by' AND dp.document_id IS NOT NULL
        ON CONFLICT (document_id, tag, value) DO NOTHING
        """,
        """
        INSERT INTO property_translate (tag, value, translated)
        SELECT 'loaded_by', m.name, COALESCE(m.display_name, m.name)
        FROM member m
        WHERE EXISTS (SELECT 1 FROM document_property dp WHERE dp.tag = 'loaded_by' AND dp.value = m.name)
        ON CONFLICT (tag, value) DO UPDATE SET translated = EXCLUDED.translated
        """,
    ]


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
    Patch("7c2e9f04-3b8a-4d1e-9a6c-5f1d0e8b6a3c", _check_document_status_values),
    Patch("4d8f1a6b-2c9e-4f70-8b3d-6a5e0c7d9f21", _check_system_properties_backfill),
    Patch("9b3e7d15-6a4c-4f28-b1d9-3e0a8c5f2b17", _check_page_count_not_usable),
    Patch("2f6a8c19-4d3b-4e75-9a1c-7b0e5d2f8a6c", _check_subjects_status_system_flags),
    # 6e1c9a34-8f27-4b56-a1d0-3c5e7f9b2d84 (_check_sync_property_flags_from_seed) удалён -
    # синхронизация базовых указателей теперь постоянная, см. Database.fill_initial_property.
    Patch("386eefd9-2f2d-4e76-ae42-11e7078daefc", _check_backfill_last_change_and_page_count),
    Patch("37c42df3-926e-43e5-8447-ea8c67e78b73", _check_backfill_loaded_by_and_date),
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
