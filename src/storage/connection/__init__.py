"""Connection abstraction for the centralized PostgreSQL.

Public API:
    create_pool()          -> sync ConnectionPool from env config
    Database               -> async facade repos receive in __init__
    load_database_config() -> DatabaseConfig (env-driven, testable)
"""
from storage.connection.config import DatabaseConfig, load_database_config
from storage.connection.database import Database, Transaction
from storage.connection.factory import create_pool

__all__ = [
    "Database",
    "DatabaseConfig",
    "Transaction",
    "create_pool",
    "load_database_config",
]
