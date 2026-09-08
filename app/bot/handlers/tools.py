from html import escape as esc

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks import MenuCB, ToolsCB
from app.bot.helpers import (
    CATEGORY_NOT_FOUND,
    NODE_NOT_FOUND,
    alert,
    get_node_or_alert,
    get_system_or_alert,
    refresh,
    show,
    unpack_id,
)
from app.bot.keyboards.tools import (
    node_card_keyboard,
    nodes_keyboard,
    nodes_selection_keyboard,
    tool_card_keyboard,
    tools_categories_keyboard,
)
from app.bot.states.tools import ToolsStates
from app.database.models import System
from app.database.repositories.node import get_nodes
from app.services.tools import (
    format_tools_card,
    get_all_tool_nodes,
    get_all_tools,
    get_tool_system,
    get_tools_for_nodes,
)


router = Router()


async def show_tools_categories(callback: CallbackQuery) -> None:
    """Экран категорий — общий для входа и кнопки «Назад»."""
    await show(
        callback,
        '🧰 <b>Инструмент</b>\n\n'
        'Выберите категорию:',
        tools_categories_keyboard(),
    )


async def show_system_nodes(
    callback: CallbackQuery,
    session: AsyncSession,
    system: System,
) -> None:
    """Список узлов категории — общий для выбора категории и «Назад»."""
    nodes = await get_nodes(session, system.id)

    if not nodes:
        await show(
            callback,
            f'🧰 <b>{esc(system.name)}</b>\n\n'
            'В этой категории пока нет узлов.',
            tool_card_keyboard(),
        )
        return

    await show(
        callback,
        f'🧰 <b>{esc(system.name)}</b>\n\n'
        'Выберите узел:',
        nodes_keyboard(nodes),
    )


async def open_all_tools(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Показывает сводную карточку всех инструментов."""
    tools = await get_all_tools(session)

    if not tools:
        await show(
            callback,
            '🧰 <b>Все инструменты</b>\n\n'
            'Инструменты пока не добавлены.',
            tool_card_keyboard(),
        )
        return

    text = [
        '🧰 <b>Все инструменты</b>',
        '',
    ]

    for index, tool in enumerate(tools, start=1):
        text.append(f'{index}. <b>{esc(tool.name)}</b>')

        if tool.description:
            text.append(f'   {esc(tool.description)}')

        text.append('')

    await show(
        callback,
        '\n'.join(text),
        tool_card_keyboard(),
    )


async def open_nodes_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинает выбор узлов для сводной карточки."""
    nodes = await get_all_tool_nodes(session)

    if not nodes:
        await show(
            callback,
            '⚙️ <b>Узлы</b>\n\n'
            'Узлы пока не добавлены.',
            tool_card_keyboard(),
        )
        return

    await state.set_state(ToolsStates.selecting_nodes)
    await state.update_data(selected_node_ids=[])

    await show(
        callback,
        '⚙️ <b>Выбор узлов</b>\n\n'
        'Выберите один или несколько узлов:',
        nodes_selection_keyboard(nodes, set()),
    )


@router.callback_query(MenuCB.filter(F.action == 'tools'))
async def open_tools(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Открывает раздел инструментов."""
    await state.clear()

    await show_tools_categories(callback)


@router.callback_query(ToolsCB.filter(F.action == 'category'))
async def select_tools_category(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обрабатывает выбор категории инструментов."""
    if callback.data is None:
        return

    callback_data = ToolsCB.unpack(callback.data)

    category = callback_data.category or ''

    if category == 'nodes':
        await open_nodes_selection(callback, state, session)
        return

    if category == 'all':
        await open_all_tools(callback, session)
        return

    system = await get_tool_system(session, category)

    if system is None:
        await alert(callback, 'Категория пока не заполнена.')
        return

    await show_system_nodes(callback, session, system)


@router.callback_query(ToolsCB.filter(F.action == 'node'))
async def open_tool_node(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Показывает карточку узла с его инструментами."""
    if (node_id := unpack_id(callback, ToolsCB)) is None:
        await alert(callback, NODE_NOT_FOUND)
        return

    node = await get_node_or_alert(session, callback, node_id)

    if node is None:
        return

    tools = [tool for tool in node.tools if tool.is_active]

    await show(
        callback,
        format_tools_card(node.name, tools),
        node_card_keyboard(node.system_id),
    )


@router.callback_query(ToolsCB.filter(F.action == 'select_node'))
async def toggle_node_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Переключает выбор узла в FSM-состоянии."""
    if (node_id := unpack_id(callback, ToolsCB)) is None:
        await alert(callback, NODE_NOT_FOUND)
        return

    node = await get_node_or_alert(session, callback, node_id)

    if node is None:
        return

    data = await state.get_data()

    selected_ids = set(data.get('selected_node_ids', []))

    if node_id in selected_ids:
        selected_ids.remove(node_id)
    else:
        selected_ids.add(node_id)

    await state.update_data(selected_node_ids=list(selected_ids))

    nodes = await get_all_tool_nodes(session)

    await refresh(
        callback,
        nodes_selection_keyboard(nodes, selected_ids),
    )


@router.callback_query(ToolsCB.filter(F.action == 'confirm_nodes'))
async def confirm_nodes_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Показывает сводную карточку по выбранным узлам."""
    data = await state.get_data()

    selected_ids = data.get('selected_node_ids', [])

    if not selected_ids:
        await alert(callback, 'Выберите хотя бы один узел.')
        return

    tools = await get_tools_for_nodes(session, selected_ids)

    back_keyboard = tool_card_keyboard(
        back_callback=ToolsCB(
            action='category',
            category='nodes',
        ).pack(),
    )

    if not tools:
        await show(
            callback,
            '⚙️ <b>Результат</b>\n\n'
            'Для выбранных узлов инструмент пока не назначен.',
            back_keyboard,
        )
        await state.clear()
        return

    await show(
        callback,
        format_tools_card('Инструмент для выбранных узлов', tools),
        back_keyboard,
    )
    await state.clear()


@router.callback_query(ToolsCB.filter(F.action == 'back_nodes'))
async def back_to_nodes(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Возвращается к экрану выбора узлов."""
    if (system_id := unpack_id(callback, ToolsCB)) is None:
        await alert(callback, CATEGORY_NOT_FOUND)
        return

    system = await get_system_or_alert(
        session,
        callback,
        system_id,
        not_found=CATEGORY_NOT_FOUND,
    )

    if system is None:
        return

    await show_system_nodes(callback, session, system)


@router.callback_query(ToolsCB.filter(F.action == 'back_categories'))
async def back_to_tools_categories(
    callback: CallbackQuery,
) -> None:
    """Возвращается к категориям инструментов."""
    await show_tools_categories(callback)
