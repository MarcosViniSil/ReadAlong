from psycopg_pool import AsyncConnectionPool

from storage.connection.config import (
    DatabaseConfig,
    load_database_config,
)

def create_pool(
    config: DatabaseConfig | None = None,
) -> AsyncConnectionPool:
    cfg = config or load_database_config()

    return AsyncConnectionPool(
        conninfo=cfg.url,
        min_size=cfg.min_size,
        max_size=cfg.max_size,
        timeout=cfg.acquire_timeout,
        open=False,
    )
