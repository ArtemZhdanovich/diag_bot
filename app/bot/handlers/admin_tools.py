from html import escape as esc

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks import AdminCB
from app.bot.filters import IsAdmin
from app.bot.helpers import (
    alert,
    show,
    unpack_id,
)
from app.bot.keyboards.admin import (
    admin_inactive_node_card_keyboard,
    admin_inactive_nodes_keyboard,
    admin_inactive_tool_card_keyboard,
    admin_inactive_tools_keyboard,
    admin_node_card_keyboard,
    admin_nodes_keyboard,
    admin_tool_card_keyboard,
    admin_tool_systems_keyboard,
    admin_tools_keyboard,
)
from app.bot.states.admin import AdminNodeStates, AdminToolStates
from app.database.repositories.node import (
    create_node,
    deactivate_node,
    delete_node,
    get_inactive_nodes,
    get_node,
    get_nodes,
    restore_node,
    update_node,
)
from app.database.repositories.system import get_system, get_systems
from app.database.repositories.tool import (
    create_tool,
    deactivate_tool,
    delete_tool,
    get_inactive_tools,
    get_tool,
    get_tools,
    restore_tool,
    update_tool,
)
from app.services.formatting import numbered_names


router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(AdminCB.filter(F.action == 'tools_systems'))
async def admin_tool_systems(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список систем-инструментов."""
    await state.clear()

    systems = await get_systems(session, 'tool')

    if not systems:
        await show(
            callback,
            '🧰 <b>Системы инструментов</b>\n\n'
            'Систем пока нет.',
            admin_tool_systems_keyboard(systems),
        )
        return

    text = [
        '🧰 <b>Системы инструментов</b>',
        '',
        *numbered_names(systems),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_tool_systems_keyboard(systems),
    )


@router.callback_query(AdminCB.filter(F.action == 'tool_system'))
async def open_admin_tool_system(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Карточка системы-инструмента."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Система не найдена.')
        return

    system = await get_system(session, system_id)

    if system is None or not system.is_active:
        await alert(callback, 'Система не найдена или отключена.')
        return

    await state.clear()

    nodes = await get_nodes(session, system_id)

    text = [
        '🧰 <b>Система инструментов</b>',
        '',
        f'<b>Название:</b> {esc(system.name)}',
        f'<b>Порядок:</b> {system.sort_order}',
        '',
        f'<b>Узлы:</b> {len(nodes)}',
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_nodes_keyboard(nodes, system_id),
    )


@router.callback_query(AdminCB.filter(F.action == 'node_add'))
async def admin_add_node(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Начинает FSM-сценарий добавления узла."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Система не найдена.')
        return

    await state.update_data(system_id=system_id)

    await state.set_state(AdminNodeStates.waiting_name)

    await show(
        callback,
        '➕ <b>Добавление узла</b>\n\n'
        'Введите название узла:',
    )


@router.message(AdminNodeStates.waiting_name)
async def admin_node_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Принимает название нового узла."""
    name = (message.text or '').strip()

    if not name:
        await message.answer(
            'Название не может быть пустым.\n\n'
            'Введите название узла:'
        )
        return

    await state.update_data(node_name=name)

    await state.set_state(AdminNodeStates.waiting_sort_order)

    await message.answer(
        'Введите порядковый номер узла.\n\n'
        'Например: <code>1</code>'
    )


@router.message(AdminNodeStates.waiting_sort_order)
async def admin_node_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Принимает порядок сортировки и создаёт узел."""
    try:
        sort_order = int((message.text or '').strip())
    except (TypeError, ValueError):
        await message.answer(
            'Введите целое число.\n\n'
            'Например: <code>1</code>'
        )
        return

    data = await state.get_data()

    system_id = data.get('system_id')
    node_name = data.get('node_name')

    if system_id is None or node_name is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные узла.\n'
            'Попробуйте добавить узел заново.'
        )
        return

    node = await create_node(
        session=session,
        system_id=int(system_id),
        name=node_name,
        sort_order=sort_order,
    )

    await state.clear()

    nodes = await get_nodes(session, int(system_id))

    text = [
        '✅ <b>Узел успешно добавлен!</b>',
        '',
        f'⚙️ <b>{esc(node.name)}</b>',
        f'Порядок: {node.sort_order}',
        '',
        'Список узлов:',
        '',
        *numbered_names(nodes),
    ]

    await message.answer(
        '\n'.join(text),
        reply_markup=admin_nodes_keyboard(nodes, int(system_id)),
    )


@router.callback_query(AdminCB.filter(F.action == 'node'))
async def open_admin_node(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Карточка узла."""
    if (node_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Узел не найден.')
        return

    node = await get_node(session, node_id)

    if node is None or not node.is_active:
        await alert(callback, 'Узел не найден или отключён.')
        return

    await state.clear()

    tools = [tool for tool in node.tools if tool.is_active]

    text = [
        '⚙️ <b>Узел</b>',
        '',
        f'<b>Название:</b> {esc(node.name)}',
        f'<b>Порядок:</b> {node.sort_order}',
        '',
        f'<b>Инструменты:</b> {len(tools)}',
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_node_card_keyboard(node.id, node.system_id),
    )


@router.callback_query(AdminCB.filter(F.action == 'node_edit'))
async def edit_admin_node(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинает FSM-сценарий редактирования узла."""
    if (node_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Узел не найден.')
        return

    node = await get_node(session, node_id)

    if node is None or not node.is_active:
        await alert(callback, 'Узел не найден.')
        return

    await state.update_data(
        node_id=node.id,
        system_id=node.system_id,
    )

    await state.set_state(AdminNodeStates.editing_name)

    await show(
        callback,
        '✏️ <b>Редактирование узла</b>\n\n'
        f'Текущее название:\n'
        f'<b>{esc(node.name)}</b>\n\n'
        'Введите новое название:',
    )


@router.message(AdminNodeStates.editing_name)
async def edit_admin_node_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Принимает новое название узла."""
    name = (message.text or '').strip()

    if not name:
        await message.answer(
            'Название не может быть пустым.\n\n'
            'Введите новое название:'
        )
        return

    await state.update_data(node_name=name)

    await state.set_state(AdminNodeStates.editing_sort_order)

    await message.answer(
        'Введите новый порядковый номер.\n\n'
        'Например: <code>1</code>'
    )


@router.message(AdminNodeStates.editing_sort_order)
async def edit_admin_node_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Принимает новый порядок сортировки узла."""
    try:
        sort_order = int((message.text or '').strip())
    except ValueError:
        await message.answer(
            'Введите целое число.\n\n'
            'Например: <code>1</code>'
        )
        return

    data = await state.get_data()

    node_id = data.get('node_id')
    system_id = data.get('system_id')
    node_name = data.get('node_name')

    if node_id is None or system_id is None or node_name is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные узла.\n'
            'Попробуйте отредактировать узел заново.'
        )
        return

    node = await get_node(session, int(node_id))

    if node is None or not node.is_active:
        await state.clear()

        await message.answer(
            '❌ Узел не найден.'
        )
        return

    node = await update_node(
        session=session,
        node=node,
        name=node_name,
        sort_order=sort_order,
    )

    await state.clear()

    await message.answer(
        '✅ <b>Узел изменён</b>\n\n'
        f'<b>Название:</b> {esc(node.name)}\n'
        f'<b>Порядок:</b> {node.sort_order}',
        reply_markup=admin_node_card_keyboard(node.id, int(system_id)),
    )


@router.callback_query(AdminCB.filter(F.action == 'node_deactivate'))
async def deactivate_admin_node(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Отключает узел."""
    if (node_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Узел не найден.')
        return

    node = await get_node(session, node_id)

    if node is None or not node.is_active:
        await alert(callback, 'Узел уже отключён.')
        return

    system_id = node.system_id

    await deactivate_node(session, node)

    await state.clear()

    nodes = await get_nodes(session, system_id)

    text = [
        '⛔ <b>Узел отключён</b>',
        '',
        f'<s>{esc(node.name)}</s>',
        '',
        'Активные узлы:',
        '',
    ]

    text.extend(
        numbered_names(nodes) or ['Активных узлов нет.']
    )

    await show(
        callback,
        '\n'.join(text),
        admin_nodes_keyboard(nodes, system_id),
    )


@router.callback_query(AdminCB.filter(F.action == 'nodes_inactive'))
async def admin_inactive_nodes(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список отключённых узлов."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Система не найдена.')
        return

    await state.clear()

    nodes = await get_inactive_nodes(session, system_id)

    if not nodes:
        await show(
            callback,
            '🗑 <b>Отключённые узлы</b>\n\n'
            'Отключённых узлов нет.',
            admin_inactive_nodes_keyboard(nodes, system_id),
        )
        return

    text = [
        '🗑 <b>Отключённые узлы</b>',
        '',
        *numbered_names(nodes),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_inactive_nodes_keyboard(nodes, system_id),
    )


@router.callback_query(AdminCB.filter(F.action == 'inactive_node'))
async def open_inactive_admin_node(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Карточка отключённого узла."""
    if (node_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Узел не найден.')
        return

    node = await get_node(session, node_id)

    if node is None or node.is_active:
        await alert(callback, 'Узел не найден или уже восстановлен.')
        return

    await state.clear()

    await show(
        callback,
        '🗑 <b>Отключённый узел</b>\n\n'
        f'<b>Название:</b> {esc(node.name)}\n'
        f'<b>Порядок:</b> {node.sort_order}\n\n'
        'Узел не отображается пользователям.',
        admin_inactive_node_card_keyboard(node.id, node.system_id),
    )


@router.callback_query(AdminCB.filter(F.action == 'node_restore'))
async def restore_admin_node(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Восстанавливает отключённый узел."""
    if (node_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Узел не найден.')
        return

    node = await get_node(session, node_id)

    if node is None or node.is_active:
        await alert(callback, 'Узел уже активен.')
        return

    system_id = node.system_id

    node = await restore_node(session, node)

    await state.clear()

    nodes = await get_inactive_nodes(session, system_id)

    await show(
        callback,
        '♻️ <b>Узел восстановлен</b>\n\n'
        f'<b>{esc(node.name)}</b>\n\n'
        'Он снова доступен в разделе инструментов.',
        admin_inactive_nodes_keyboard(nodes, system_id),
    )


@router.callback_query(AdminCB.filter(F.action == 'node_delete'))
async def delete_admin_node_warning(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Предупреждение перед удалением узла."""
    if (node_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Узел не найден.')
        return

    node = await get_node(session, node_id)

    if node is None:
        await alert(callback, 'Узел не найден.')
        return

    if node.is_active:
        await alert(callback, 'Сначала отключите узел.')
        return

    await state.clear()

    await show(
        callback,
        '⚠️ <b>Удаление узла</b>\n\n'
        f'Узел:\n'
        f'<b>{esc(node.name)}</b>\n\n'
        'После удаления будут потеряны связи с инструментами.\n\n'
        'Это действие нельзя отменить.\n\n'
        '<b>Вы действительно хотите удалить узел?</b>',
        admin_inactive_node_card_keyboard(node.id, node.system_id),
    )


@router.callback_query(AdminCB.filter(F.action == 'node_delete_confirm'))
async def delete_admin_node_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Окончательно удаляет узел."""
    if (node_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Узел не найден.')
        return

    node = await get_node(session, node_id)

    if node is None:
        await alert(callback, 'Узел не найден.')
        return

    if node.is_active:
        await alert(callback, 'Нельзя удалить активный узел.')
        return

    system_id = node.system_id
    node_name = node.name

    await delete_node(session, node)

    await state.clear()

    nodes = await get_inactive_nodes(session, system_id)

    text = [
        '✅ <b>Узел удалён окончательно</b>',
        '',
        f'<s>{esc(node_name)}</s>',
        '',
    ]

    if nodes:
        text.extend(('🗑 <b>Отключённые узлы:</b>', ''))
        text.extend(numbered_names(nodes))
    else:
        text.append('Отключённых узлов больше нет.')

    await show(
        callback,
        '\n'.join(text),
        admin_inactive_nodes_keyboard(nodes, system_id),
        answer_text='Узел удалён.',
    )


@router.callback_query(AdminCB.filter(F.action == 'tools_list'))
async def admin_tools_list(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список всех инструментов."""
    await state.clear()

    tools = await get_tools(session)

    if not tools:
        await show(
            callback,
            '🧰 <b>Все инструменты</b>\n\n'
            'Инструментов пока нет.',
            admin_tools_keyboard([]),
        )
        return

    text = [
        '🧰 <b>Все инструменты</b>',
        '',
        *numbered_names(tools),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_tools_keyboard(tools),
    )


@router.callback_query(AdminCB.filter(F.action == 'tool_add'))
async def admin_add_tool(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Начинает FSM-сценарий добавления инструмента."""
    await state.set_state(AdminToolStates.waiting_name)

    await show(
        callback,
        '➕ <b>Добавление инструмента</b>\n\n'
        'Введите название инструмента:',
    )


@router.message(AdminToolStates.waiting_name)
async def admin_tool_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Принимает название нового инструмента."""
    name = (message.text or '').strip()

    if not name:
        await message.answer(
            'Название не может быть пустым.\n\n'
            'Введите название инструмента:'
        )
        return

    await state.update_data(tool_name=name)

    await state.set_state(AdminToolStates.waiting_description)

    await message.answer(
        'Введите описание инструмента\n'
        '(или <code>/</code> чтобы пропустить):'
    )


@router.message(AdminToolStates.waiting_description)
async def admin_tool_description(
    message: Message,
    state: FSMContext,
) -> None:
    """Принимает описание нового инструмента."""
    text = (message.text or '').strip()

    description = None if text == '/' else (text or None)

    await state.update_data(tool_description=description)

    await state.set_state(AdminToolStates.waiting_sort_order)

    await message.answer(
        'Введите порядковый номер инструмента.\n\n'
        'Например: <code>1</code>'
    )


@router.message(AdminToolStates.waiting_sort_order)
async def admin_tool_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Принимает порядок сортировки и создаёт инструмент."""
    try:
        sort_order = int((message.text or '').strip())
    except (TypeError, ValueError):
        await message.answer(
            'Введите целое число.\n\n'
            'Например: <code>1</code>'
        )
        return

    data = await state.get_data()

    tool_name = data.get('tool_name')
    tool_description = data.get('tool_description')

    if tool_name is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные инструмента.\n'
            'Попробуйте добавить инструмент заново.'
        )
        return

    tool = await create_tool(
        session=session,
        name=tool_name,
        description=tool_description,
        sort_order=sort_order,
    )

    await state.clear()

    tools = await get_tools(session)

    text = [
        '✅ <b>Инструмент успешно добавлен!</b>',
        '',
        f'🔧 <b>{esc(tool.name)}</b>',
        f'Порядок: {tool.sort_order}',
        '',
        'Список инструментов:',
        '',
        *numbered_names(tools),
    ]

    await message.answer(
        '\n'.join(text),
        reply_markup=admin_tools_keyboard(tools),
    )


@router.callback_query(AdminCB.filter(F.action == 'tool'))
async def open_admin_tool(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Карточка инструмента."""
    if (tool_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Инструмент не найден.')
        return

    tool = await get_tool(session, tool_id)

    if tool is None or not tool.is_active:
        await alert(callback, 'Инструмент не найден или отключён.')
        return

    await state.clear()

    text = [
        '🔧 <b>Инструмент</b>',
        '',
        f'<b>Название:</b> {esc(tool.name)}',
        f'<b>Порядок:</b> {tool.sort_order}',
    ]

    if tool.description:
        text.extend(('', f'<b>Описание:</b> {esc(tool.description)}'))

    await show(
        callback,
        '\n'.join(text),
        admin_tool_card_keyboard(tool.id),
    )


@router.callback_query(AdminCB.filter(F.action == 'tool_edit'))
async def edit_admin_tool(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинает FSM-сценарий редактирования инструмента."""
    if (tool_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Инструмент не найден.')
        return

    tool = await get_tool(session, tool_id)

    if tool is None or not tool.is_active:
        await alert(callback, 'Инструмент не найден.')
        return

    await state.update_data(tool_id=tool.id)

    await state.set_state(AdminToolStates.editing_name)

    await show(
        callback,
        '✏️ <b>Редактирование инструмента</b>\n\n'
        f'Текущее название:\n'
        f'<b>{esc(tool.name)}</b>\n\n'
        'Введите новое название:',
    )


@router.message(AdminToolStates.editing_name)
async def edit_admin_tool_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Принимает новое название инструмента."""
    name = (message.text or '').strip()

    if not name:
        await message.answer(
            'Название не может быть пустым.\n\n'
            'Введите новое название:'
        )
        return

    await state.update_data(tool_name=name)

    await state.set_state(AdminToolStates.editing_description)

    await message.answer(
        'Введите новое описание\n'
        '(или <code>/</code> чтобы очистить):'
    )


@router.message(AdminToolStates.editing_description)
async def edit_admin_tool_description(
    message: Message,
    state: FSMContext,
) -> None:
    """Принимает новое описание инструмента."""
    text = (message.text or '').strip()

    description = None if text == '/' else (text or None)

    await state.update_data(tool_description=description)

    await state.set_state(AdminToolStates.editing_sort_order)

    await message.answer(
        'Введите новый порядковый номер.\n\n'
        'Например: <code>1</code>'
    )


@router.message(AdminToolStates.editing_sort_order)
async def edit_admin_tool_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Принимает новый порядок сортировки инструмента."""
    try:
        sort_order = int((message.text or '').strip())
    except ValueError:
        await message.answer(
            'Введите целое число.\n\n'
            'Например: <code>1</code>'
        )
        return

    data = await state.get_data()

    tool_id = data.get('tool_id')
    tool_name = data.get('tool_name')
    tool_description = data.get('tool_description')

    if tool_id is None or tool_name is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные инструмента.\n'
            'Попробуйте отредактировать инструмент заново.'
        )
        return

    tool = await get_tool(session, int(tool_id))

    if tool is None or not tool.is_active:
        await state.clear()

        await message.answer(
            '❌ Инструмент не найден.'
        )
        return

    tool = await update_tool(
        session=session,
        tool=tool,
        name=tool_name,
        description=tool_description,
        sort_order=sort_order,
    )

    await state.clear()

    await message.answer(
        '✅ <b>Инструмент изменён</b>\n\n'
        f'<b>Название:</b> {esc(tool.name)}\n'
        f'<b>Порядок:</b> {tool.sort_order}',
        reply_markup=admin_tool_card_keyboard(tool.id),
    )


@router.callback_query(AdminCB.filter(F.action == 'tool_deactivate'))
async def deactivate_admin_tool(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Отключает инструмент."""
    if (tool_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Инструмент не найден.')
        return

    tool = await get_tool(session, tool_id)

    if tool is None or not tool.is_active:
        await alert(callback, 'Инструмент уже отключён.')
        return

    await deactivate_tool(session, tool)

    await state.clear()

    tools = await get_tools(session)

    text = [
        '⛔ <b>Инструмент отключён</b>',
        '',
        f'<s>{esc(tool.name)}</s>',
        '',
        'Активные инструменты:',
        '',
    ]

    text.extend(
        numbered_names(tools) or ['Активных инструментов нет.']
    )

    await show(
        callback,
        '\n'.join(text),
        admin_tools_keyboard(tools),
    )


@router.callback_query(AdminCB.filter(F.action == 'tools_inactive'))
async def admin_inactive_tools(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список отключённых инструментов."""
    await state.clear()

    tools = await get_inactive_tools(session)

    if not tools:
        await show(
            callback,
            '🗑 <b>Отключённые инструменты</b>\n\n'
            'Отключённых инструментов нет.',
            admin_inactive_tools_keyboard(tools),
        )
        return

    text = [
        '🗑 <b>Отключённые инструменты</b>',
        '',
        *numbered_names(tools),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_inactive_tools_keyboard(tools),
    )


@router.callback_query(AdminCB.filter(F.action == 'inactive_tool'))
async def open_inactive_admin_tool(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Карточка отключённого инструмента."""
    if (tool_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Инструмент не найден.')
        return

    tool = await get_tool(session, tool_id)

    if tool is None or tool.is_active:
        await alert(callback, 'Инструмент не найден или уже восстановлен.')
        return

    await state.clear()

    await show(
        callback,
        '🗑 <b>Отключённый инструмент</b>\n\n'
        f'<b>Название:</b> {esc(tool.name)}\n'
        f'<b>Порядок:</b> {tool.sort_order}\n\n'
        'Инструмент не отображается пользователям.',
        admin_inactive_tool_card_keyboard(tool.id),
    )


@router.callback_query(AdminCB.filter(F.action == 'tool_restore'))
async def restore_admin_tool(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Восстанавливает отключённый инструмент."""
    if (tool_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Инструмент не найден.')
        return

    tool = await get_tool(session, tool_id)

    if tool is None or tool.is_active:
        await alert(callback, 'Инструмент уже активен.')
        return

    tool = await restore_tool(session, tool)

    await state.clear()

    tools = await get_inactive_tools(session)

    await show(
        callback,
        '♻️ <b>Инструмент восстановлен</b>\n\n'
        f'<b>{esc(tool.name)}</b>\n\n'
        'Он снова доступен в разделе инструментов.',
        admin_inactive_tools_keyboard(tools),
    )


@router.callback_query(AdminCB.filter(F.action == 'tool_delete'))
async def delete_admin_tool_warning(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Предупреждение перед удалением инструмента."""
    if (tool_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Инструмент не найден.')
        return

    tool = await get_tool(session, tool_id)

    if tool is None:
        await alert(callback, 'Инструмент не найден.')
        return

    if tool.is_active:
        await alert(callback, 'Сначала отключите инструмент.')
        return

    await state.clear()

    await show(
        callback,
        '⚠️ <b>Удаление инструмента</b>\n\n'
        f'Инструмент:\n'
        f'<b>{esc(tool.name)}</b>\n\n'
        'После удаления будут потеряны связи с узлами.\n\n'
        'Это действие нельзя отменить.\n\n'
        '<b>Вы действительно хотите удалить инструмент?</b>',
        admin_inactive_tool_card_keyboard(tool.id),
    )


@router.callback_query(AdminCB.filter(F.action == 'tool_delete_confirm'))
async def delete_admin_tool_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Окончательно удаляет инструмент."""
    if (tool_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Инструмент не найден.')
        return

    tool = await get_tool(session, tool_id)

    if tool is None:
        await alert(callback, 'Инструмент не найден.')
        return

    if tool.is_active:
        await alert(callback, 'Нельзя удалить активный инструмент.')
        return

    tool_name = tool.name

    await delete_tool(session, tool)

    await state.clear()

    tools = await get_inactive_tools(session)

    text = [
        '✅ <b>Инструмент удалён окончательно</b>',
        '',
        f'<s>{esc(tool_name)}</s>',
        '',
    ]

    if tools:
        text.extend(('🗑 <b>Отключённые инструменты:</b>', ''))
        text.extend(numbered_names(tools))
    else:
        text.append('Отключённых инструментов больше нет.')

    await show(
        callback,
        '\n'.join(text),
        admin_inactive_tools_keyboard(tools),
        answer_text='Инструмент удалён.',
    )