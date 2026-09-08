from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.database.models.cause import Cause
    from app.database.models.system import System


class Problem(Base):
    """Проблема в рамках системы диагностики."""

    __tablename__ = 'problems'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    system_id: Mapped[int] = mapped_column(
        ForeignKey('systems.id', ondelete='CASCADE'),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
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
        back_populates='problems',
    )

    causes: Mapped[list['Cause']] = relationship(
        'Cause',
        back_populates='problem',
        cascade='all, delete-orphan',
    )