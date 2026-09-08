from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.node import Node
from app.database.models.system import System


async def get_nodes(
    session: AsyncSession,
    system_id: int,
) -> list[Node]:
    """Активные узлы системы по возрастанию порядка."""
    result = await session.scalars(
        select(Node)
        .options(
            selectinload(Node.tools)
        )
        .where(
            Node.system_id == system_id,
            Node.is_active.is_(True),
        )
        .order_by(Node.sort_order, Node.id)
    )

    return list(result.all())


async def get_node(
    session: AsyncSession,
    node_id: int,
) -> Node | None:
    """Активный узел по id или None."""
    node: Node | None = await session.scalar(
        select(Node)
        .options(selectinload(Node.tools))
        .where(Node.id == node_id)
    )

    return node


async def get_tool_nodes(
    session: AsyncSession,
) -> list[Node]:
    """Активные узлы всех систем типа "tool" одним запросом."""
    result = await session.scalars(
        select(Node)
        .join(Node.system)
        .options(
            selectinload(Node.tools)
        )
        .where(
            System.type == 'tool',
            Node.is_active.is_(True),
        )
        .order_by(
            System.sort_order,
            System.id,
            Node.sort_order,
            Node.id,
        )
    )

    return list(result.all())


async def get_active_nodes_by_ids(
    session: AsyncSession,
    node_ids: Sequence[int],
) -> list[Node]:
    """Активные узлы по списку id одним запросом (без N+1)."""
    if not node_ids:
        return []

    result = await session.scalars(
        select(Node)
        .options(
            selectinload(Node.tools)
        )
        .where(
            Node.id.in_(list(node_ids)),
            Node.is_active.is_(True),
        )
        .order_by(Node.sort_order, Node.id)
    )

    return list(result.all())
