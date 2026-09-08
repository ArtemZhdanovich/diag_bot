import sqlite3

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings


settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
)


@event.listens_for(Engine, 'connect')
def _enable_sqlite_foreign_keys(
    dbapi_connection: sqlite3.Connection,
    connection_record: Any,
) -> None:
    """Включает FK-каскады (ondelete=CASCADE) для SQLite.

    По умолчанию SQLite игнорирует внешние ключи, поэтому без этой
    настройки ondelete="CASCADE" на уровне БД не работает.
    Слушатель вешается на класс Engine и действует в том числе
    для синхронного движка alembic.
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость: выдаёт сессию БД для middleware."""
    async with async_session_factory() as session:
        yield session
