from aiogram.types import InlineKeyboardMarkup

from app.bot.callbacks import ToolsCB
from app.bot.keyboards.common import button, stack, with_nav
from app.database.models.node import Node


def tools_categories_keyboard() -> InlineKeyboardMarkup:
    """Категории инструментов (кнопки систем-инструментов)."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                button(
                    '🔧 Гидросистема погрузочного оборудования',
                    ToolsCB(
                        action='category',
                        category='loading',
                    ).pack(),
                ),
                button(
                    '🚜 Гидросистема рулевого управления',
                    ToolsCB(
                        action='category',
                        category='steering',
                    ).pack(),
                ),
                button(
                    '🛑 Гидросистема тормозов',
                    ToolsCB(
                        action='category',
                        category='brakes',
                    ).pack(),
                ),
                button(
                    '⚙️ Узлы',
                    ToolsCB(
                        action='category',
                        category='nodes',
                    ).pack(),
                ),
                button(
                    '📋 Все',
                    ToolsCB(
                        action='category',
                        category='all',
                    ).pack(),
                ),
            ),
        )
    )


def nodes_keyboard(
    nodes: list[Node],
) -> InlineKeyboardMarkup:
    """Кнопки узлов выбранной системы."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            stack(
                *(
                    button(
                        node.name,
                        ToolsCB(
                            action='node',
                            id=node.id,
                        ).pack(),
                    )
                    for node in nodes
                ),
            ),
            back=button(
                '⬅️ Назад',
                ToolsCB(action='back_categories').pack(),
            ),
        )
    )


def nodes_selection_keyboard(
    nodes: list[Node],
    selected_ids: set[int],
) -> InlineKeyboardMarkup:
    """Чекбоксы узлов для сводной карточки."""
    selection_rows = stack(
        *(
            button(
                f"{'☑️' if node.id in selected_ids else '⬜'} {node.name}",
                ToolsCB(
                    action='select_node',
                    id=node.id,
                ).pack(),
            )
            for node in nodes
        ),
    )

    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            selection_rows
            + stack(
                button('✅ ОК', ToolsCB(action='confirm_nodes').pack()),
            ),
            back=button(
                '⬅️ Назад',
                ToolsCB(action='back_categories').pack(),
            ),
        )
    )


def tool_card_keyboard(
    back_callback: str = ToolsCB(action='back_categories').pack(),
) -> InlineKeyboardMarkup:
    """Клавиатура карточки инструментов."""
    return InlineKeyboardMarkup(
        inline_keyboard=with_nav(
            [],
            back=button('⬅️ Назад', back_callback),
        )
    )


def node_card_keyboard(
    system_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки узла."""
    return tool_card_keyboard(
        back_callback=ToolsCB(
            action='back_nodes',
            id=system_id,
        ).pack(),
    )