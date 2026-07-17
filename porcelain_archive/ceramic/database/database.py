import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, List, Optional, Sequence

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from porcelain_archive.config import config


class Database:
    """
    Класс-синглтон для управления пулом асинхронных соединений с базой данных PostgreSQL.

    Подключается к той же БД (config.database.*), что и основной пул
    porcelain_archive.database.db, но отдельным пулом с row_factory=dict_row -
    сервисы ceramic обращаются к строкам результата как к словарям (row["col"]),
    а не кортежам, как основной пул porcelain_archive.

    Пул создаётся (но не открывается) при первом создании экземпляра.
    Открытие пула и создание таблиц выполняется асинхронно в init().
    """
    _instance = None
    _pool: Optional[AsyncConnectionPool] = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self.__class__._initialized:
            return
        self.__class__._initialized = True

        self.conninfo = (
            f"dbname={config.database.dbname} "
            f"user={config.database.user} "
            f"password={config.database.password} "
            f"host={config.database.host} "
            f"port={config.database.port}"
        )

        # open=False: открытие пула требует сетевого I/O и должно происходить
        # внутри работающего event loop (см. init()), а не в момент импорта модуля.
        # row_factory=dict_row: строки результата доступны как row["column"].
        self._pool = AsyncConnectionPool(
            self.conninfo, open=False, kwargs={"row_factory": dict_row}
        )

    async def init(self) -> None:
        """
        Открывает пул соединений и выполняет create_tables.sql/create_triggers.sql.
        Должна вызываться из async-контекста (lifespan FastAPI при старте сервера).
        """
        await self._pool.open()

        async with self._pool.connection() as conn:
            sql_script = ""
            for file in ("create_tables.sql", "create_triggers.sql"):
                sql_file_path = os.path.join(os.path.dirname(__file__), file)
                with open(sql_file_path, "r", encoding="utf-8") as f:
                    sql_script += f.read() + "\n"
            await conn.execute(sql_script)

        print("Database pool opened, tables initialized/verified.")

    async def close(self) -> None:
        """Закрывает пул соединений (вызывается при остановке сервера)."""
        await self._pool.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncConnection]:
        """
        Выделяет отдельное соединение из пула на время одной транзакции.
        Коммитит при успешном завершении блока, откатывает при исключении.

        Использование:
            async with db.transaction() as conn:
                await conn.execute(...)
                await conn.execute(...)
        """
        async with self._pool.connection() as conn:
            yield conn

    async def execute_read(self, query: str, params: Optional[Sequence[Any]] = None) -> List[Any]:
        """Выполняет READ-запрос (SELECT) и возвращает все строки результата (списком dict)."""
        async with self.transaction() as conn:
            cursor = await conn.execute(query, params)
            return await cursor.fetchall()

    async def execute_read_one(self, query: str, params: Optional[Sequence[Any]] = None) -> Optional[Any]:
        """Выполняет READ-запрос и возвращает первую строку (dict) или None."""
        rows = await self.execute_read(query, params)
        return rows[0] if rows else None

    async def execute_write(self, query: str, params: Optional[Sequence[Any]] = None) -> int:
        """Выполняет WRITE-запрос (INSERT/UPDATE/DELETE), возвращает количество затронутых строк."""
        async with self.transaction() as conn:
            cursor = await conn.execute(query, params)
            return cursor.rowcount

    async def execute_insert_returning(self, query: str, params: Optional[Sequence[Any]] = None) -> Any:
        """Выполняет INSERT ... RETURNING ... и возвращает первую (единственную) строку."""
        async with self.transaction() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            return row


db = Database()
