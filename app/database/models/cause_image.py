from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.database.models.cause_card import CauseCard


class CauseImage(Base):
    """Изображение карточки причины."""

    __tablename__ = 'cause_images'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    card_id: Mapped[int] = mapped_column(
        ForeignKey(
            'cause_cards.id',
            ondelete='CASCADE',
        ),
        nullable=False,
    )

    telegram_file_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    caption: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    card: Mapped['CauseCard'] = relationship(
        'CauseCard',
        back_populates='images',
    )