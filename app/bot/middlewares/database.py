from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware

from app.database.session import async_session_factory


class DatabaseMiddleware(BaseMiddleware):
    """Открывает сессию на каждый апдейт и управляет транзакцией.

    Репозитории выполняют только flush(); коммит делается здесь один раз
    после успешного выполнения хендлера, а при ошибке транзакция
    откатывается целиком — частичные записи невозможны.
    """

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        """Открывает сессию БД и передаёт её в хендлер; коммит в middleware."""
        async with async_session_factory() as session:
            data['session'] = session

            try:
                result = await handler(event, data)
            except Exception:
                await session.rollback()
                raise

            await session.commit()

            return result