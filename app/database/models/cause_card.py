from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.database.models.cause import Cause
    from app.database.models.cause_image import CauseImage


class CauseCard(Base):
    """Текстовая карточка причины."""

    __tablename__ = 'cause_cards'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    cause_id: Mapped[int] = mapped_column(
        ForeignKey('causes.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    inspection: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommendation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cause: Mapped['Cause'] = relationship(
        'Cause',
        back_populates='card',
    )

    images: Mapped[list['CauseImage']] = relationship(
        'CauseImage',
        back_populates='card',
        cascade='all, delete-orphan',
        order_by='CauseImage.sort_order',
    )