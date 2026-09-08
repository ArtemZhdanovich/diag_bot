from aiogram.types import InlineKeyboardMarkup

from app.bot.callbacks import DiagnosisCB
from app.bot.keyboards.common import button, stack, with_nav
from app.database.models.cause import Cause
from app.database.models.problem import Problem
from app.database.models.system import System


def diagnosis_systems_keyboard(
    systems: list[System],
) -> InlineKeyboardMarkup:
    """Кнопки систем диагностики."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        system.name,
                        DiagnosisCB(
                            action='system',
                            id=system.id,
                        ).pack(),
                    )
                    for system in systems
                ),
            ),
        )
    )


def diagnosis_problems_keyboard(
    problems: list[Problem],
) -> InlineKeyboardMarkup:
    """Кнопки проблем выбранной системы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        problem.name,
                        DiagnosisCB(
                            action='problem',
                            id=problem.id,
                        ).pack(),
                    )
                    for problem in problems
                ),
            ),
            back=button(
                '⬅️ Назад',
                DiagnosisCB(action='back_systems').pack(),
            ),
        )
    )


def diagnosis_causes_keyboard(
    causes: list[Cause],
) -> InlineKeyboardMarkup:
    """Кнопки причин выбранной проблемы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        cause.name,
                        DiagnosisCB(
                            action='cause',
                            id=cause.id,
                        ).pack(),
                    )
                    for cause in causes
                ),
            ),
            back=button(
                '⬅️ Назад',
                DiagnosisCB(action='back_problems').pack(),
            ),
        )
    )


def cause_card_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура карточки причины."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            [],
            back=button(
                '⬅️ Назад',
                DiagnosisCB(action='back_causes').pack(),
            ),
        )
    )