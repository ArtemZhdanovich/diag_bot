"""Общие помощники хендлеров: разбор callback_data, показ сообщений,
получение сущностей с guard-ответами.

Здесь живёт всё то, что раньше копировалось в каждом хендлере:
«unpack → id is None → alert», «fetch → not found → alert» и
пара «edit_text + answer».
"""

from collections.abc import Awaitable, Callable
from typing import Protocol, cast

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardMarkup,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.cause import Cause
from app.database.models.node import Node
from app.database.models.problem import Problem
from app.database.models.system import System
from app.database.repositories.cause import get_cause
from app.database.repositories.node import get_node
from app.database.repositories.problem import get_problem
from app.database.repositories.system import get_system


SYSTEM_NOT_FOUND = 'Система не найдена.'
CATEGORY_NOT_FOUND = 'Категория не найдена.'
NODE_NOT_FOUND = 'Узел не найден.'
PROBLEM_NOT_FOUND = 'Проблема не найдена.'
CAUSE_NOT_FOUND = 'Причина не найдена.'


class _HasId(Protocol):
    """Разобранная callback_data с полем id."""

    id: int | None


class _Active(Protocol):
    """Сущность БД с признаком активности."""

    is_active: bool


async def alert(callback: CallbackQuery, text: str) -> None:
    """Показывает всплывающее уведомление, не меняя сообщение."""
    await callback.answer(text, show_alert=True)


def unpack_id(
    callback: CallbackQuery,
    factory: type[CallbackData],
) -> int | None:
    """Достаёт поле id из callback_data, разобранной фабрикой."""
    if callback.data is None:
        return None

    data = cast('_HasId', factory.unpack(callback.data))

    return data.id


def _is_not_modified(error: TelegramBadRequest) -> bool:
    """Проверяет безобидную ошибку повторного нажатия той же кнопки."""
    text = ' '.join(
        part
        for part in (
            str(error),
            str(getattr(error, 'message', '')),
        )
        if part
    )

    return 'message is not modified' in text


async def show(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    *,
    answer_text: str | None = None,
) -> None:
    """Заменяет текст сообщения и отвечает на callback.

    Повторное нажатие кнопки Telegram отклоняет с ошибкой
    «message is not modified» — она глушится, остальные
    пробрасываются в dp.errors.
    """
    message = callback.message

    if message is None or isinstance(message, InaccessibleMessage):
        await alert(callback, 'Сообщение недоступно.')
        return

    try:
        await message.edit_text(
            text,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as error:
        if not _is_not_modified(error):
            raise

    await callback.answer(answer_text)


async def refresh(
    callback: CallbackQuery,
    reply_markup: InlineKeyboardMarkup,
) -> None:
    """Заменяет только клавиатуру (выбор узлов с чекбоксами)."""
    message = callback.message

    if message is None or isinstance(message, InaccessibleMessage):
        await alert(callback, 'Сообщение недоступно.')
        return

    try:
        await message.edit_reply_markup(
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as error:
        if not _is_not_modified(error):
            raise

    await callback.answer()


async def _fetch_or_alert[T: _Active](
    callback: CallbackQuery,
    fetch: Callable[[], Awaitable[T | None]],
    not_found: str,
    require_active: bool,
) -> T | None:
    entity = await fetch()

    if entity is None or (require_active and not entity.is_active):
        await alert(callback, not_found)
        return None

    return entity


async def get_system_or_alert(
    session: AsyncSession,
    callback: CallbackQuery,
    system_id: int,
    *,
    require_active: bool = True,
    not_found: str = SYSTEM_NOT_FOUND,
) -> System | None:
    """Возвращает систему или отвечает alert-ом «не найдена»."""
    return await _fetch_or_alert(
        callback,
        lambda: get_system(session, system_id),
        not_found,
        require_active,
    )


async def get_node_or_alert(
    session: AsyncSession,
    callback: CallbackQuery,
    node_id: int,
) -> Node | None:
    """Возвращает активный узел или отвечает alert-ом."""
    return await _fetch_or_alert(
        callback,
        lambda: get_node(session, node_id),
        NODE_NOT_FOUND,
        require_active=True,
    )


async def get_problem_or_alert(
    session: AsyncSession,
    callback: CallbackQuery,
    problem_id: int,
) -> Problem | None:
    """Возвращает активную проблему или отвечает alert-ом."""
    return await _fetch_or_alert(
        callback,
        lambda: get_problem(session, problem_id),
        PROBLEM_NOT_FOUND,
        require_active=True,
    )


async def get_cause_or_alert(
    session: AsyncSession,
    callback: CallbackQuery,
    cause_id: int,
) -> Cause | None:
    """Возвращает активную причину или отвечает alert-ом."""
    return await _fetch_or_alert(
        callback,
        lambda: get_cause(session, cause_id),
        CAUSE_NOT_FOUND,
        require_active=True,
    )