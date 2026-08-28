import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    url: str
    min_size: int
    max_size: int
    acquire_timeout: float


def load_database_config() -> DatabaseConfig:
    return DatabaseConfig(
        url=os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:password@localhost:5432/readalong",
        ),
        min_size=int(os.getenv("PG_POOL_MIN", "0")),
        max_size=int(os.getenv("PG_POOL_MAX", "5")),
        acquire_timeout=float(os.getenv("PG_ACQUIRE_TIMEOUT", "10")),
    )
