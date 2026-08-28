from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Sequence

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


class Database:

    def __init__(self, pool: AsyncConnectionPool):
        self._pool = pool

    async def open(self) -> None:
        await self._pool.open()

    async def close(self) -> None:
        await self._pool.close()

    @asynccontextmanager
    async def transaction(
        self,
    ) -> AsyncGenerator["Transaction", None]:
        async with self._pool.connection() as conn:
            async with conn.transaction():
                yield Transaction(conn)


class Transaction:

    def __init__(self, conn: AsyncConnection):
        self._conn = conn

    async def execute(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> int:
        async with self._conn.cursor() as cur:
            await cur.execute(query, params)
            return cur.rowcount

    async def fetchall(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> list[dict]:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            return await cur.fetchall()

    async def fetchone(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> dict | None:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            return await cur.fetchone()

    async def fetchval(
        self,
        query: str,
        params: Sequence[Any] | None = None,
        column: int = 0,
    ) -> Any:
        async with self._conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()

            if row is None:
                return None

            return row[column]
