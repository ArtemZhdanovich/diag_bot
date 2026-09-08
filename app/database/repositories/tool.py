from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tool import Tool


async def get_tools(
    session: AsyncSession,
) -> list[Tool]:
    """Все инструменты по возрастанию порядка."""
    result = await session.scalars(
        select(Tool)
        .where(Tool.is_active.is_(True))
        .order_by(Tool.sort_order, Tool.id)
    )

    return list(result.all())


async def get_tool(
    session: AsyncSession,
    tool_id: int,
) -> Tool | None:
    """Инструмент по id или None."""
    return await session.get(Tool, tool_id)