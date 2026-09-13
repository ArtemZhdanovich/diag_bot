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


async def get_inactive_problems(
    session: AsyncSession,
    system_id: int,
) -> list[Problem]:
    """Отключённые проблемы системы по возрастанию порядка."""
    result = await session.scalars(
        select(Problem)
        .where(
            Problem.system_id == system_id,
            Problem.is_active.is_(False),
        )
        .order_by(Problem.sort_order, Problem.id)
    )

    return list(result.all())


async def get_problem(
    session: AsyncSession,
    problem_id: int,
) -> Problem | None:
    """Проблема по id независимо от активности."""
    return await session.get(Problem, problem_id)


async def create_problem(
    session: AsyncSession,
    system_id: int,
    name: str,
    sort_order: int = 0,
) -> Problem:
    """Создаёт проблему: только flush, коммит делает middleware."""
    problem = Problem(
        system_id=system_id,
        name=name,
        sort_order=sort_order,
        is_active=True,
    )

    session.add(problem)

    await session.flush()

    return problem


async def update_problem(
    session: AsyncSession,
    problem: Problem,
    name: str,
    sort_order: int,
) -> Problem:
    """Обновляет название и порядок сортировки проблемы."""
    problem.name = name
    problem.sort_order = sort_order

    await session.flush()

    return problem


async def deactivate_problem(
    session: AsyncSession,
    problem: Problem,
) -> None:
    """Мягко отключает проблему."""
    problem.is_active = False

    await session.flush()


async def restore_problem(
    session: AsyncSession,
    problem: Problem,
) -> Problem:
    """Возвращает отключённую проблему в работу."""
    problem.is_active = True

    await session.flush()

    return problem


async def delete_problem(
    session: AsyncSession,
    problem: Problem,
) -> None:
    """Удаляет проблему вместе со связанными причинами.

    Каскад обеспечивают relationship(cascade="all, delete-orphan") и
    PRAGMA foreign_keys=ON, включённый в app.database.session.
    """
    await session.delete(problem)
    await session.flush()