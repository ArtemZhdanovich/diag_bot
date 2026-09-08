"""Небольшие форматтеры, общие для хендлеров."""

from collections.abc import Sequence
from html import escape as esc
from typing import Protocol


class _Named(Protocol):
    """Сущность с атрибутом name (модели БД)."""

    name: str


def numbered_names(items: Sequence[_Named]) -> list[str]:
    """Нумерованный список «1. Название» для текстов сообщений.

    Названия приходят из БД, поэтому экранируются как HTML.
    """
    return [
        f'{index}. {esc(item.name)}'
        for index, item in enumerate(items, start=1)
    ]