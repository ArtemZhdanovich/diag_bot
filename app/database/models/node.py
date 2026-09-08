from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.database.models.system import System
    from app.database.models.tool import Tool


node_tools = Table(
    'node_tools',
    Base.metadata,
    Column(
        'node_id',
        ForeignKey('nodes.id', ondelete='CASCADE'),
        primary_key=True,
    ),
    Column(
        'tool_id',
        ForeignKey('tools.id', ondelete='CASCADE'),
        primary_key=True,
    ),
)


class Node(Base):
    """Узел системы с привязанными инструментами."""

    __tablename__ = 'nodes'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    system_id: Mapped[int] = mapped_column(
        ForeignKey('systems.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    system: Mapped['System'] = relationship(
        'System',
        back_populates='nodes',
    )

    tools: Mapped[list['Tool']] = relationship(
        'Tool',
        secondary=node_tools,
        back_populates='nodes',
    )