from aiogram.types import InlineKeyboardMarkup

from app.bot.callbacks import AdminCB, MenuCB
from app.bot.keyboards.common import button, stack, with_nav
from app.database.models.system import System


def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню администратора."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '🩺 Диагностика',
                    AdminCB(action='diagnosis').pack(),
                ),
                button(
                    '🧰 Инструменты',
                    AdminCB(action='tools').pack(),
                ),
                button(
                    '👥 Пользователи',
                    AdminCB(action='users').pack(),
                ),
            ),
            back=button('⬅️ Назад', MenuCB(action='main').pack()),
            menu=False,
        )
    )


def admin_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с единственной кнопкой «в админку»."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            [],
            back=button(
                '⬅️ В админку',
                MenuCB(action='admin').pack(),
            ),
        )
    )


def admin_diagnosis_keyboard() -> InlineKeyboardMarkup:
    """Меню раздела администрирования диагностики."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '🗂 Системы',
                    AdminCB(action='diagnosis_systems').pack(),
                ),
                button(
                    '🔴 Проблемы',
                    AdminCB(action='diagnosis_problems').pack(),
                ),
                button(
                    '⚠️ Причины',
                    AdminCB(action='diagnosis_causes').pack(),
                ),
                button(
                    '📋 Карточки',
                    AdminCB(action='diagnosis_cards').pack(),
                ),
            ),
            back=button(
                '⬅️ В админку',
                MenuCB(action='admin').pack(),
            ),
        )
    )


def admin_systems_keyboard(
    systems: list[System],
) -> InlineKeyboardMarkup:
    """Список активных систем с кнопкой добавления."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'🗂 {system.name}',
                        AdminCB(
                            action='system',
                            id=system.id,
                        ).pack(),
                    )
                    for system in systems
                ),
                button(
                    '➕ Добавить систему',
                    AdminCB(action='system_add').pack(),
                ),
                button(
                    '🗑 Отключённые системы',
                    AdminCB(action='systems_inactive').pack(),
                ),
            ),
            back=button(
                '⬅️ В админку',
                AdminCB(action='diagnosis').pack(),
            ),
        )
    )


def admin_system_card_keyboard(
    system_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки активной системы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '✏️ Редактировать',
                    AdminCB(
                        action='system_edit',
                        id=system_id,
                    ).pack(),
                ),
                button(
                    '⛔ Отключить',
                    AdminCB(
                        action='system_deactivate',
                        id=system_id,
                    ).pack(),
                ),
                button(
                    '🔴 Проблемы',
                    AdminCB(
                        action='system_problems',
                        id=system_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='diagnosis_systems').pack(),
            ),
        )
    )


def admin_inactive_systems_keyboard(
    systems: list[System],
) -> InlineKeyboardMarkup:
    """Список отключённых систем."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'🗑 {system.name}',
                        AdminCB(
                            action='inactive_system',
                            id=system.id,
                        ).pack(),
                    )
                    for system in systems
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='diagnosis_systems').pack(),
            ),
        )
    )


def admin_inactive_system_card_keyboard(
    system_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки отключённой системы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '♻️ Восстановить',
                    AdminCB(
                        action='system_restore',
                        id=system_id,
                    ).pack(),
                ),
                button(
                    '❌ Удалить окончательно',
                    AdminCB(
                        action='system_delete',
                        id=system_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='systems_inactive').pack(),
            ),
        )
    )


def admin_delete_system_confirm_keyboard(
    system_id: int,
) -> InlineKeyboardMarkup:
    """Подтверждение окончательного удаления системы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '❌ Да, удалить окончательно',
                    AdminCB(
                        action='system_delete_confirm',
                        id=system_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Отмена',
                AdminCB(action='inactive_system', id=system_id).pack(),
            ),
        )
    )
