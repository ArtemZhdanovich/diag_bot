from collections.abc import Sequence
from html import escape as esc

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.node import Node
from app.database.models.system import System
from app.database.models.tool import Tool
from app.database.repositories.node import (
    get_active_nodes_by_ids,
    get_tool_nodes,
)
from app.database.repositories.system import get_system_by_slug
from app.database.repositories.tool import get_tools


async def get_tool_system(
    session: AsyncSession,
    category: str,
) -> System | None:
    """Активная система-инструмент по slug категории."""
    return await get_system_by_slug(
        session,
        category,
    )


async def get_all_tool_nodes(
    session: AsyncSession,
) -> list[Node]:
    # Один запрос со selectinload вместо запроса на каждую систему.
    """Все активные узлы систем-инструментов."""
    return await get_tool_nodes(
        session,
    )


async def get_all_tools(
    session: AsyncSession,
) -> list[Tool]:
    # Все активные инструменты одним запросом — обход узлов не нужен.
    """Все инструменты по порядку."""
    return await get_tools(
        session,
    )


async def get_tools_for_nodes(
    session: AsyncSession,
    node_ids: Sequence[int],
) -> list[Tool]:
    # Один запрос вместо запроса на каждый узел.
    """Инструменты выбранных узлов с дедупликацией по id."""
    nodes = await get_active_nodes_by_ids(
        session,
        node_ids,
    )

    tools_by_id: dict[int, Tool] = {}

    for node in nodes:
        for tool in node.tools:
            if tool.is_active:
                tools_by_id[tool.id] = tool

    return sorted(
        tools_by_id.values(),
        key=lambda tool: (
            tool.sort_order,
            tool.id,
        ),
    )


def format_tools_card(
    title: str,
    tools: Sequence[Tool],
) -> str:
    """Форматирует HTML-карточку списка инструментов."""
    parts = [
        f'🧰 <b>{esc(title)}</b>',
        '',
        '<b>Необходимый инструмент:</b>',
    ]

    for tool in tools:
        parts.append(
            f'\n🔧 <b>{esc(tool.name)}</b>'
        )

        if tool.description:
            parts.append(
                esc(tool.description)
            )

    return '\n'.join(parts)