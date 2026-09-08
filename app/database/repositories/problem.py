from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.problem import Problem


async def get_problems(
    session: AsyncSession,
    system_id: int,
) -> list[Problem]:
    """Активные проблемы системы по возрастанию порядка."""
    result = await session.scalars(
        select(Problem)
        .where(
            Problem.system_id == system_id,
            Problem.is_active.is_(True),
        )
        .order_by(Problem.sort_order, Problem.id)
    )

    return list(result.all())


async def get_problem(
    session: AsyncSession,
    problem_id: int,
) -> Problem | None:
    """Активная проблема по id или None."""
    return await session.get(Problem, problem_id)