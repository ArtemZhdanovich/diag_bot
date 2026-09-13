from aiogram.types import InlineKeyboardMarkup

from app.bot.callbacks import AdminCB, MenuCB
from app.bot.keyboards.common import button, stack, with_nav
from app.database.models.cause import Cause
from app.database.models.node import Node
from app.database.models.problem import Problem
from app.database.models.system import System
from app.database.models.tool import Tool


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


def admin_problems_keyboard(
    problems: list[Problem],
    system_id: int,
) -> InlineKeyboardMarkup:
    """Список проблем системы с кнопкой добавления."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'🔴 {problem.name}',
                        AdminCB(
                            action='problem',
                            id=problem.id,
                        ).pack(),
                    )
                    for problem in problems
                ),
                button(
                    '➕ Добавить проблему',
                    AdminCB(
                        action='problem_add',
                        id=system_id,
                    ).pack(),
                ),
                button(
                    '🗑 Отключённые проблемы',
                    AdminCB(
                        action='problems_inactive',
                        id=system_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='system', id=system_id).pack(),
            ),
        )
    )


def admin_problem_card_keyboard(
    problem_id: int,
    system_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки активной проблемы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '✏️ Редактировать',
                    AdminCB(
                        action='problem_edit',
                        id=problem_id,
                    ).pack(),
                ),
                button(
                    '⛔ Отключить',
                    AdminCB(
                        action='problem_deactivate',
                        id=problem_id,
                    ).pack(),
                ),
                button(
                    '⚠️ Причины',
                    AdminCB(
                        action='problem_causes',
                        id=problem_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='system_problems', id=system_id).pack(),
            ),
        )
    )


def admin_inactive_problems_keyboard(
    problems: list[Problem],
    system_id: int,
) -> InlineKeyboardMarkup:
    """Список отключённых проблем системы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'🗑 {problem.name}',
                        AdminCB(
                            action='inactive_problem',
                            id=problem.id,
                        ).pack(),
                    )
                    for problem in problems
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='system_problems', id=system_id).pack(),
            ),
        )
    )


def admin_inactive_problem_card_keyboard(
    problem_id: int,
    system_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки отключённой проблемы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '♻️ Восстановить',
                    AdminCB(
                        action='problem_restore',
                        id=problem_id,
                    ).pack(),
                ),
                button(
                    '❌ Удалить окончательно',
                    AdminCB(
                        action='problem_delete',
                        id=problem_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='problems_inactive', id=system_id).pack(),
            ),
        )
    )


def admin_delete_problem_confirm_keyboard(
    problem_id: int,
    system_id: int,
) -> InlineKeyboardMarkup:
    """Подтверждение окончательного удаления проблемы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '❌ Да, удалить окончательно',
                    AdminCB(
                        action='problem_delete_confirm',
                        id=problem_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Отмена',
                AdminCB(
                    action='inactive_problem',
                    id=problem_id,
                ).pack(),
            ),
        )
    )


def admin_causes_keyboard(
    causes: list[Cause],
    problem_id: int,
) -> InlineKeyboardMarkup:
    """Список причин проблемы с кнопкой добавления."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'⚠️ {cause.name}',
                        AdminCB(
                            action='cause',
                            id=cause.id,
                        ).pack(),
                    )
                    for cause in causes
                ),
                button(
                    '➕ Добавить причину',
                    AdminCB(
                        action='cause_add',
                        id=problem_id,
                    ).pack(),
                ),
                button(
                    '🗑 Отключённые причины',
                    AdminCB(
                        action='causes_inactive',
                        id=problem_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='problem', id=problem_id).pack(),
            ),
        )
    )


def admin_cause_card_keyboard(
    cause_id: int,
    problem_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки активной причины."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '✏️ Редактировать',
                    AdminCB(
                        action='cause_edit',
                        id=cause_id,
                    ).pack(),
                ),
                button(
                    '⛔ Отключить',
                    AdminCB(
                        action='cause_deactivate',
                        id=cause_id,
                    ).pack(),
                ),
                button(
                    '📋 Карточка',
                    AdminCB(
                        action='cause_card',
                        id=cause_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='problem_causes', id=problem_id).pack(),
            ),
        )
    )


def admin_inactive_causes_keyboard(
    causes: list[Cause],
    problem_id: int,
) -> InlineKeyboardMarkup:
    """Список отключённых причин проблемы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'🗑 {cause.name}',
                        AdminCB(
                            action='inactive_cause',
                            id=cause.id,
                        ).pack(),
                    )
                    for cause in causes
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='problem_causes', id=problem_id).pack(),
            ),
        )
    )


def admin_inactive_cause_card_keyboard(
    cause_id: int,
    problem_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки отключённой причины."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '♻️ Восстановить',
                    AdminCB(
                        action='cause_restore',
                        id=cause_id,
                    ).pack(),
                ),
                button(
                    '❌ Удалить окончательно',
                    AdminCB(
                        action='cause_delete',
                        id=cause_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='causes_inactive', id=problem_id).pack(),
            ),
        )
    )


def admin_delete_cause_confirm_keyboard(
    cause_id: int,
    problem_id: int,
) -> InlineKeyboardMarkup:
    """Подтверждение окончательного удаления причины."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '❌ Да, удалить окончательно',
                    AdminCB(
                        action='cause_delete_confirm',
                        id=cause_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Отмена',
                AdminCB(
                    action='inactive_cause',
                    id=cause_id,
                ).pack(),
            ),
        )
    )


def admin_card_keyboard(
    cause_id: int,
    problem_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки причины."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '📝 Описание',
                    AdminCB(
                        action='card_edit_description',
                        id=cause_id,
                    ).pack(),
                ),
                button(
                    '🔍 Проверка',
                    AdminCB(
                        action='card_edit_inspection',
                        id=cause_id,
                    ).pack(),
                ),
                button(
                    '🛠 Рекомендации',
                    AdminCB(
                        action='card_edit_recommendation',
                        id=cause_id,
                    ).pack(),
                ),
                button(
                    '🖼 Добавить фото',
                    AdminCB(
                        action='card_add_image',
                        id=cause_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='cause', id=cause_id).pack(),
            ),
        )
    )


def admin_tool_systems_keyboard(
    systems: list[System],
) -> InlineKeyboardMarkup:
    """Список систем-инструментов."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'🧰 {system.name}',
                        AdminCB(
                            action='tool_system',
                            id=system.id,
                        ).pack(),
                    )
                    for system in systems
                ),
                button(
                    '🔧 Все инструменты',
                    AdminCB(action='tools_list').pack(),
                ),
            ),
            back=button(
                '⬅️ В админку',
                AdminCB(action='tools').pack(),
            ),
            menu=False,
        )
    )


def admin_tools_keyboard(
    tools: list[Tool],
) -> InlineKeyboardMarkup:
    """Список инструментов с кнопкой добавления."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'🔧 {tool.name}',
                        AdminCB(
                            action='tool',
                            id=tool.id,
                        ).pack(),
                    )
                    for tool in tools
                ),
                button(
                    '➕ Добавить инструмент',
                    AdminCB(action='tool_add').pack(),
                ),
                button(
                    '🗑 Отключённые инструменты',
                    AdminCB(action='tools_inactive').pack(),
                ),
            ),
            back=button(
                '⬅️ К системам',
                AdminCB(action='tools').pack(),
            ),
        )
    )


def admin_tool_card_keyboard(
    tool_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки инструмента."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '✏️ Редактировать',
                    AdminCB(
                        action='tool_edit',
                        id=tool_id,
                    ).pack(),
                ),
                button(
                    '⛔ Отключить',
                    AdminCB(
                        action='tool_deactivate',
                        id=tool_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='tools_list').pack(),
            ),
        )
    )


def admin_inactive_tools_keyboard(
    tools: list[Tool],
) -> InlineKeyboardMarkup:
    """Список отключённых инструментов."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'🗑 {tool.name}',
                        AdminCB(
                            action='inactive_tool',
                            id=tool.id,
                        ).pack(),
                    )
                    for tool in tools
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='tools_list').pack(),
            ),
        )
    )


def admin_inactive_tool_card_keyboard(
    tool_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки отключённого инструмента."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '♻️ Восстановить',
                    AdminCB(
                        action='tool_restore',
                        id=tool_id,
                    ).pack(),
                ),
                button(
                    '❌ Удалить окончательно',
                    AdminCB(
                        action='tool_delete',
                        id=tool_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='tools_inactive').pack(),
            ),
        )
    )


def admin_nodes_keyboard(
    nodes: list[Node],
    system_id: int,
) -> InlineKeyboardMarkup:
    """Список узлов системы с кнопкой добавления."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'⚙️ {node.name}',
                        AdminCB(
                            action='node',
                            id=node.id,
                        ).pack(),
                    )
                    for node in nodes
                ),
                button(
                    '➕ Добавить узел',
                    AdminCB(
                        action='node_add',
                        id=system_id,
                    ).pack(),
                ),
                button(
                    '🗑 Отключённые узлы',
                    AdminCB(
                        action='nodes_inactive',
                        id=system_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='tool_system', id=system_id).pack(),
            ),
        )
    )


def admin_node_card_keyboard(
    node_id: int,
    system_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки узла."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '✏️ Редактировать',
                    AdminCB(
                        action='node_edit',
                        id=node_id,
                    ).pack(),
                ),
                button(
                    '⛔ Отключить',
                    AdminCB(
                        action='node_deactivate',
                        id=node_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='tool_system', id=system_id).pack(),
            ),
        )
    )


def admin_inactive_nodes_keyboard(
    nodes: list[Node],
    system_id: int,
) -> InlineKeyboardMarkup:
    """Список отключённых узлов."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        f'🗑 {node.name}',
                        AdminCB(
                            action='inactive_node',
                            id=node.id,
                        ).pack(),
                    )
                    for node in nodes
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='tool_system', id=system_id).pack(),
            ),
        )
    )


def admin_inactive_node_card_keyboard(
    node_id: int,
    system_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки отключённого узла."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '♻️ Восстановить',
                    AdminCB(
                        action='node_restore',
                        id=node_id,
                    ).pack(),
                ),
                button(
                    '❌ Удалить окончательно',
                    AdminCB(
                        action='node_delete',
                        id=node_id,
                    ).pack(),
                ),
            ),
            back=button(
                '⬅️ Назад',
                AdminCB(action='nodes_inactive', id=system_id).pack(),
            ),
        )
    )
