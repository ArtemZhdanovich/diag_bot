from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.cause import Cause
from app.database.models.cause_card import CauseCard


async def get_causes(
    session: AsyncSession,
    problem_id: int,
) -> list[Cause]:
    """Причины проблемы по возрастанию порядка."""
    result = await session.scalars(
        select(Cause)
        .where(
            Cause.problem_id == problem_id,
            Cause.is_active.is_(True),
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