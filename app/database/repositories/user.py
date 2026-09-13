from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
) -> User:
    """Возвращает пользователя по telegram_id, создавая при отсутствии.

    Обновляет username/first_name при изменении.
    """
    result = await session.scalar(
        select(User).where(User.telegram_id == telegram_id)
    )

    if result is None:
        result = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )

        session.add(result)
    else:
        result.username = username
        result.first_name = first_name

    await session.flush()

    return result


async def get_users(
    session: AsyncSession,
) -> list[User]:
    """Все пользователи по возрастанию id."""
    result = await session.scalars(
        select(User).order_by(User.id)
    )

    return list(result.all())


async def count_users(
    session: AsyncSession,
) -> int:
    """Количество пользователей."""
    result = await session.scalar(
        select(func.count()).select_from(User)
    )

    return int(result or 0)
