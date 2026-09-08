from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.database.models.cause_card import CauseCard
    from app.database.models.problem import Problem


class Cause(Base):
    """Причина неисправности с карточкой и изображениями."""

    __tablename__ = 'causes'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    problem_id: Mapped[int] = mapped_column(
        ForeignKey('problems.id', ondelete='CASCADE'),
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

    problem: Mapped['Problem'] = relationship(
        'Problem',
        back_populates='causes',
    )

    card: Mapped['CauseCard | None'] = relationship(
        'CauseCard',
        back_populates='cause',
        uselist=False,
        cascade='all, delete-orphan',
    )