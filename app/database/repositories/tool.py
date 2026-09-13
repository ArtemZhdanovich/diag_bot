from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tool import Tool


async def get_tools(
    session: AsyncSession,
) -> list[Tool]:
    """Все активные инструменты по возрастанию порядка."""
    result = await session.scalars(
        select(Tool)
        .where(Tool.is_active.is_(True))
        .order_by(Tool.sort_order, Tool.id)
    )

    return list(result.all())


async def get_inactive_tools(
    session: AsyncSession,
) -> list[Tool]:
    """Все отключённые инструменты по возрастанию порядка."""
    result = await session.scalars(
        select(Tool)
        .where(Tool.is_active.is_(False))
        .order_by(Tool.sort_order, Tool.id)
    )

    return list(result.all())


async def get_tool(
    session: AsyncSession,
    tool_id: int,
) -> Tool | None:
    """Инструмент по id независимо от активности."""
    return await session.get(Tool, tool_id)


async def create_tool(
    session: AsyncSession,
    name: str,
    description: str | None = None,
    sort_order: int = 0,
) -> Tool:
    """Создаёт инструмент: только flush, коммит делает middleware."""
    tool = Tool(
        name=name,
        description=description,
        sort_order=sort_order,
        is_active=True,
    )

    session.add(tool)

    await session.flush()

    return tool


async def update_tool(
    session: AsyncSession,
    tool: Tool,
    name: str,
    description: str | None,
    sort_order: int,
) -> Tool:
    """Обновляет название, описание и порядок сортировки инструмента."""
    tool.name = name
    tool.description = description
    tool.sort_order = sort_order

    await session.flush()

    return tool


async def deactivate_tool(
    session: AsyncSession,
    tool: Tool,
) -> None:
    """Мягко отключает инструмент."""
    tool.is_active = False

    await session.flush()


async def restore_tool(
    session: AsyncSession,
    tool: Tool,
) -> Tool:
    """Возвращает отключённый инструмент в работу."""
    tool.is_active = True

    await session.flush()

    return tool


async def delete_tool(
    session: AsyncSession,
    tool: Tool,
) -> None:
    """Удаляет инструмент вместе со связями узлов.

    Каскад обеспечивают relationship(cascade="all, delete-orphan") и
    PRAGMA foreign_keys=ON, включённый в app.database.session.
    """
    await session.delete(tool)
    await session.flush()