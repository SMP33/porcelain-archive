import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, List, Optional, Sequence

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from ..config.config import config


class Database:
    """
    Класс-синглтон для управления пулом асинхронных соединений с базой данных PostgreSQL.

    Пул создаётся (но не открывается) при первом создании экземпляра.
    Открытие пула и создание таблиц выполняется асинхронно в init().
    """
    _instance = None
    _pool: Optional[AsyncConnectionPool] = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """
        Реализация паттерна Singleton.
        Создает экземпляр только при первом вызове, при повторных - возвращает его же.
        """
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Читает конфиг и создаёт (но не открывает) пул соединений с БД.
        Выполняется только один раз, даже если Database() будет вызван повторно.
        """
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
        self._pool = AsyncConnectionPool(self.conninfo, open=False)

    async def init(self) -> None:
        """
        Открывает пул соединений и выполняет create_tables.sql.
        Должна вызываться из async-контекста (lifespan FastAPI при старте сервера).
        """
        await self._pool.open()

        async with self._pool.connection() as conn:
            files = ['create_tables.sql', 'create_triggers.sql', 'fill_initial_data.sql']
            
            sql_script=''
            for file in files:
                sql_file_path = os.path.join(os.path.dirname(__file__), file)
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    sql_script += f.read() + '\n'
            
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
        Каждый вызов transaction() полностью изолирован от остальных запросов -
        в отличие от одного общего соединения на всё приложение, конкурентные
        запросы больше не могут перепутать состояние транзакций друг друга.

        Использование:
            async with db.transaction() as conn:
                await conn.execute(...)
                await conn.execute(...)
        """
        async with self._pool.connection() as conn:
            yield conn

    async def execute_read(self, query: str, params: Optional[Sequence[Any]] = None) -> List[Any]:
        """
        Выполняет READ-запрос (SELECT) в отдельном соединении из пула
        и возвращает все строки результата.
        """
        async with self.transaction() as conn:
            cursor = await conn.execute(query, params)
            return await cursor.fetchall()

    async def execute_write(self, query: str, params: Optional[Sequence[Any]] = None) -> int:
        """
        Выполняет WRITE-запрос (INSERT/UPDATE/DELETE) в отдельном соединении из пула.
        Каждый вызов - отдельная, независимая транзакция.

        :return: Количество затронутых строк.
        """
        async with self.transaction() as conn:
            cursor = await conn.execute(query, params)
            return cursor.rowcount

    async def get_user_role(self, user_id: int) -> Optional[str]:
        """
        Возвращает роль пользователя (см. ROLES.md), либо None, если пользователь не найден.
        """
        rows = await self.execute_read(
            "SELECT role FROM member WHERE id = %s",
            (user_id,)
        )
        if not rows:
            return None
        return rows[0][0]


db = Database()
