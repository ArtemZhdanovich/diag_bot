from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.cause import Cause
from app.database.models.cause_card import CauseCard


async def get_causes(
    session: AsyncSession,
    problem_id: int,
) -> list[Cause]:
    """Активные причины проблемы по возрастанию порядка."""
    result = await session.scalars(
        select(Cause)
        .where(
            Cause.problem_id == problem_id,
            Cause.is_active.is_(True),
        )
        .order_by(Cause.sort_order, Cause.id)
    )

    return list(result.all())


async def get_inactive_causes(
    session: AsyncSession,
    problem_id: int,
) -> list[Cause]:
    """Отключённые причины проблемы по возрастанию порядка."""
    result = await session.scalars(
        select(Cause)
        .where(
            Cause.problem_id == problem_id,
            Cause.is_active.is_(False),
        )
        .order_by(Cause.sort_order, Cause.id)
    )

    return list(result.all())


async def get_cause(
    session: AsyncSession,
    cause_id: int,
) -> Cause | None:
    """Причина по id или None."""
    result = await session.scalar(
        select(Cause)
        .options(
            selectinload(Cause.card)
            .selectinload(CauseCard.images)
        )
        .where(Cause.id == cause_id)
    )

    return result


async def create_cause(
    session: AsyncSession,
    problem_id: int,
    name: str,
    sort_order: int = 0,
) -> Cause:
    """Создаёт причину: только flush, коммит делает middleware."""
    cause = Cause(
        problem_id=problem_id,
        name=name,
        sort_order=sort_order,
        is_active=True,
    )

    session.add(cause)

    await session.flush()

    return cause


async def update_cause(
    session: AsyncSession,
    cause: Cause,
    name: str,
    sort_order: int,
) -> Cause:
    """Обновляет название и порядок сортировки причины."""
    cause.name = name
    cause.sort_order = sort_order

    await session.flush()

    return cause


async def deactivate_cause(
    session: AsyncSession,
    cause: Cause,
) -> None:
    """Мягко отключает причину."""
    cause.is_active = False

    await session.flush()


async def restore_cause(
    session: AsyncSession,
    cause: Cause,
) -> Cause:
    """Возвращает отключённую причину в работу."""
    cause.is_active = True

    await session.flush()

    return cause


async def delete_cause(
    session: AsyncSession,
    cause: Cause,
) -> None:
    """Удаляет причину вместе со связанной карточкой.

    Каскад обеспечивают relationship(cascade="all, delete-orphan") и
    PRAGMA foreign_keys=ON, включённый в app.database.session.
    """
    await session.delete(cause)
    await session.flush()