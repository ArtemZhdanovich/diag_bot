from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.system import System


async def get_systems(
    session: AsyncSession,
    system_type: str,
) -> list[System]:
    """Активные системы заданного типа по возрастанию порядка."""
    result = await session.scalars(
        select(System)
        .where(
            System.type == system_type,
            System.is_active.is_(True),
        )
        .order_by(
            System.sort_order,
            System.id,
        )
    )

    return list(result.all())


async def get_system(
    session: AsyncSession,
    system_id: int,
) -> System | None:
    """Система по id независимо от активности."""
    return await session.get(
        System,
        system_id,
    )


async def create_system(
    session: AsyncSession,
    name: str,
    system_type: str,
    sort_order: int = 0,
) -> System:
    """Создаёт систему: только flush, коммит делает middleware."""
    system = System(
        name=name,
        type=system_type,
        sort_order=sort_order,
        is_active=True,
    )

    session.add(system)

    # Коммит выполняется в DatabaseMiddleware после хендлера.
    await session.flush()

    return system


async def update_system(
    session: AsyncSession,
    system: System,
    name: str,
    sort_order: int,
) -> System:
    """Обновляет название и порядок сортировки системы."""
    system.name = name
    system.sort_order = sort_order

    await session.flush()

    return system


async def deactivate_system(
    session: AsyncSession,
    system: System,
) -> None:
    """Мягко отключает систему."""
    system.is_active = False

    await session.flush()


async def get_inactive_systems(
    session: AsyncSession,
    system_type: str,
) -> list[System]:
    """Отключённые системы заданного типа по порядку."""
    result = await session.scalars(
        select(System)
        .where(
            System.type == system_type,
            System.is_active.is_(False),
        )
        .order_by(
            System.sort_order,
            System.id,
        )
    )

    return list(result.all())


async def restore_system(
    session: AsyncSession,
    system: System,
) -> System:
    """Возвращает отключённую систему в работу."""
    system.is_active = True

    await session.flush()

    return system


async def delete_system(
    session: AsyncSession,
    system: System,
) -> None:
    """Удаляет систему вместе со всеми связанными данными.

    Каскад обеспечивают relationship(cascade="all, delete-orphan") и
    PRAGMA foreign_keys=ON, включённый в app.database.session,
    поэтому ручное удаление по уровням больше не нужно.
    """
    await session.delete(system)
    await session.flush()
