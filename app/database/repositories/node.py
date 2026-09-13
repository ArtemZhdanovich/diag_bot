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


async def get_inactive_nodes(
    session: AsyncSession,
    system_id: int,
) -> list[Node]:
    """Отключённые узлы системы по возрастанию порядка."""
    result = await session.scalars(
        select(Node)
        .options(
            selectinload(Node.tools)
        )
        .where(
            Node.system_id == system_id,
            Node.is_active.is_(False),
        )
        .order_by(Node.sort_order, Node.id)
    )

    return list(result.all())


async def get_node(
    session: AsyncSession,
    node_id: int,
) -> Node | None:
    """Узел по id независимо от активности."""
    node: Node | None = await session.scalar(
        select(Node)
        .options(selectinload(Node.tools))
        .where(Node.id == node_id)
    )

    return node


async def create_node(
    session: AsyncSession,
    system_id: int,
    name: str,
    sort_order: int = 0,
) -> Node:
    """Создаёт узел: только flush, коммит делает middleware."""
    node = Node(
        system_id=system_id,
        name=name,
        sort_order=sort_order,
        is_active=True,
    )

    session.add(node)

    await session.flush()

    return node


async def update_node(
    session: AsyncSession,
    node: Node,
    name: str,
    sort_order: int,
) -> Node:
    """Обновляет название и порядок сортировки узла."""
    node.name = name
    node.sort_order = sort_order

    await session.flush()

    return node


async def deactivate_node(
    session: AsyncSession,
    node: Node,
) -> None:
    """Мягко отключает узел."""
    node.is_active = False

    await session.flush()


async def restore_node(
    session: AsyncSession,
    node: Node,
) -> Node:
    """Возвращает отключённый узел в работу."""
    node.is_active = True

    await session.flush()

    return node


async def delete_node(
    session: AsyncSession,
    node: Node,
) -> None:
    """Удаляет узел вместе со связями инструментов.

    Каскад обеспечивают relationship(cascade="all, delete-orphan") и
    PRAGMA foreign_keys=ON, включённый в app.database.session.
    """
    await session.delete(node)
    await session.flush()


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