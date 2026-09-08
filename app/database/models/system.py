from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.database.models.node import Node
    from app.database.models.problem import Problem


class System(Base):
    """Система диагностики или инструментов."""

    __tablename__ = 'systems'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    type: Mapped[str] = mapped_column(
        String(50),
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

    problems: Mapped[list['Problem']] = relationship(
        'Problem',
        back_populates='system',
        cascade='all, delete-orphan',
    )

    nodes: Mapped[list['Node']] = relationship(
        'Node',
        back_populates='system',
        cascade='all, delete-orphan',
    )