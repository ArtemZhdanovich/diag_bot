from html import escape as esc

from app.database.models.cause import Cause


def format_cause_card(cause: Cause) -> str:
    """Форматирует HTML-карточку причины."""
    if cause.card is None:
        return (
            f'🔴 <b>{esc(cause.name)}</b>\n\n'
            'Карточка пока не заполнена.'
        )

    parts = [
        f'🔴 <b>{esc(cause.name)}</b>',
    ]

    if cause.card.description:
        parts.append(
            f'\n📋 <b>Описание</b>\n'
            f'{esc(cause.card.description)}'
        )

    if cause.card.inspection:
        parts.append(
            f'\n🔍 <b>Проверка</b>\n'
            f'{esc(cause.card.inspection)}'
        )

    if cause.card.recommendation:
        parts.append(
            f'\n🛠 <b>Рекомендации</b>\n'
            f'{esc(cause.card.recommendation)}'
        )

    return '\n'.join(parts)