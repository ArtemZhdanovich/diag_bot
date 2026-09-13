from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.cause_card import CauseCard
from app.database.models.cause_image import CauseImage


async def get_card_by_cause(
    session: AsyncSession,
    cause_id: int,
) -> CauseCard | None:
    """Карточка причины по cause_id с изображениями."""
    result = await session.scalar(
        select(CauseCard)
        .options(
            selectinload(CauseCard.images)
        )
        .where(CauseCard.cause_id == cause_id)
    )

    return result


async def create_card(
    session: AsyncSession,
    cause_id: int,
    description: str | None = None,
    inspection: str | None = None,
    recommendation: str | None = None,
) -> CauseCard:
    """Создаёт карточку причины: только flush, коммит делает middleware."""
    card = CauseCard(
        cause_id=cause_id,
        description=description,
        inspection=inspection,
        recommendation=recommendation,
    )

    session.add(card)

    await session.flush()

    return card


async def update_card(
    session: AsyncSession,
    card: CauseCard,
    description: str | None,
    inspection: str | None,
    recommendation: str | None,
) -> CauseCard:
    """Обновляет текстовые поля карточки."""
    card.description = description
    card.inspection = inspection
    card.recommendation = recommendation

    await session.flush()

    return card


async def add_image(
    session: AsyncSession,
    card_id: int,
    telegram_file_id: str,
    caption: str | None = None,
    sort_order: int = 0,
) -> CauseImage:
    """Добавляет изображение к карточке."""
    image = CauseImage(
        card_id=card_id,
        telegram_file_id=telegram_file_id,
        caption=caption,
        sort_order=sort_order,
    )

    session.add(image)

    await session.flush()

    return image


async def delete_image(
    session: AsyncSession,
    image: CauseImage,
) -> None:
    """Удаляет изображение карточки."""
    await session.delete(image)
    await session.flush()