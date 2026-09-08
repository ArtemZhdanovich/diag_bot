from html import escape as esc

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks import AdminCB, MenuCB
from app.bot.filters import IsAdmin
from app.bot.helpers import (
    SYSTEM_NOT_FOUND,
    alert,
    get_system_or_alert,
    show,
    unpack_id,
)
from app.bot.keyboards.admin import (
    admin_back_keyboard,
    admin_delete_system_confirm_keyboard,
    admin_diagnosis_keyboard,
    admin_inactive_system_card_keyboard,
    admin_inactive_systems_keyboard,
    admin_main_keyboard,
    admin_system_card_keyboard,
    admin_systems_keyboard,
)
from app.bot.states.admin import AdminSystemStates
from app.database.repositories.system import (
    create_system,
    deactivate_system,
    delete_system,
    get_inactive_systems,
    get_system,
    get_systems,
    restore_system,
    update_system,
)
from app.services.formatting import numbered_names


# Доступ ко всем хендлерам роутера разрешён только администраторам:
# проверка прав вынесена на уровень роутера (app.bot.filters.IsAdmin)
# и не зависит от ручных вызовов в каждом хендлере.
router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(MenuCB.filter(F.action == 'admin'))
async def open_admin(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Показывает главное меню администратора."""
    await state.clear()

    await show(
        callback,
        '⚙️ <b>Админ-панель</b>\n\n'
        'Выберите раздел для управления:',
        admin_main_keyboard(),
    )


@router.callback_query(AdminCB.filter(F.action == 'diagnosis'))
async def admin_diagnosis(
    callback: CallbackQuery,
) -> None:
    """Раздел администрирования диагностики."""
    await show(
        callback,
        '🩺 <b>Управление диагностикой</b>\n\n'
        'Выберите раздел:',
        admin_diagnosis_keyboard(),
    )


@router.callback_query(AdminCB.filter(F.action == 'tools'))
async def admin_tools(
    callback: CallbackQuery,
) -> None:
    """Раздел администрирования инструментов."""
    await show(
        callback,
        '🧰 <b>Управление инструментами</b>\n\n'
        'Раздел пока находится в разработке.',
        admin_back_keyboard(),
    )


@router.callback_query(AdminCB.filter(F.action == 'users'))
async def admin_users(
    callback: CallbackQuery,
) -> None:
    """Экран управления пользователями (заглушка)."""
    await show(
        callback,
        '👥 <b>Пользователи</b>\n\n'
        'Раздел пока находится в разработке.',
        admin_back_keyboard(),
    )


@router.callback_query(
    AdminCB.filter(
        F.action.in_({
            'diagnosis_problems',
            'diagnosis_causes',
            'diagnosis_cards',
        })
    )
)
async def admin_section_stub(
    callback: CallbackQuery,
) -> None:
    # Раньше кнопки «Проблемы», «Причины» и «Карточки» не имели
    # обработчиков и нажатие просто «висело» без ответа.
    """Заглушка для ещё не реализованных разделов."""
    await alert(callback, 'Раздел пока находится в разработке.')


@router.callback_query(
    AdminCB.filter(F.action == 'diagnosis_systems')
)
async def admin_systems(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список активных систем диагностики."""
    await state.clear()

    systems = await get_systems(
        session,
        'diagnosis',
    )

    if not systems:
        await show(
            callback,
            '🗂 <b>Системы диагностики</b>\n\n'
            'Систем пока нет.',
            admin_systems_keyboard(systems),
        )
        return

    text = [
        '🗂 <b>Системы диагностики</b>',
        '',
        *numbered_names(systems),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_systems_keyboard(systems),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'systems_inactive')
)
async def admin_inactive_systems(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список отключённых систем."""
    await state.clear()

    systems = await get_inactive_systems(
        session,
        'diagnosis',
    )

    if not systems:
        await show(
            callback,
            '🗑 <b>Отключённые системы</b>\n\n'
            'Отключённых систем нет.',
            admin_inactive_systems_keyboard(systems),
        )
        return

    text = [
        '🗑 <b>Отключённые системы</b>',
        '',
        *numbered_names(systems),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_inactive_systems_keyboard(systems),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'inactive_system')
)
async def open_inactive_admin_system(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Карточка отключённой системы."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    system = await get_system_or_alert(
        session,
        callback,
        system_id,
        require_active=False,
        not_found='Система не найдена или уже восстановлена.',
    )

    if system is None:
        return

    await state.clear()

    await show(
        callback,
        '🗑 <b>Отключённая система</b>\n\n'
        f'<b>Название:</b> {esc(system.name)}\n'
        f'<b>Тип:</b> {system.type}\n'
        f'<b>Порядок:</b> {system.sort_order}\n\n'
        'Система не отображается пользователям.',
        admin_inactive_system_card_keyboard(system.id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'system_delete')
)
async def delete_admin_system_warning(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Предупреждение перед окончательным удалением системы."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    system = await get_system_or_alert(
        session,
        callback,
        system_id,
        require_active=False,
    )

    if system is None:
        return

    if system.is_active:
        await alert(callback, 'Сначала отключите систему.')
        return

    await state.clear()

    await show(
        callback,
        '⚠️ <b>Окончательное удаление</b>\n\n'
        f'Система:\n'
        f'<b>{esc(system.name)}</b>\n\n'
        'После удаления будут потеряны связанные '
        'данные этой системы.\n\n'
        'Это действие нельзя отменить.\n\n'
        '<b>Вы действительно хотите удалить систему?</b>',
        admin_delete_system_confirm_keyboard(system.id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'system_restore')
)
async def restore_admin_system(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Восстанавливает отключённую систему."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    system = await get_system_or_alert(
        session,
        callback,
        system_id,
        require_active=False,
    )

    if system is None:
        return

    if system.is_active:
        await alert(callback, 'Система уже активна.')
        return

    system = await restore_system(
        session,
        system,
    )

    await state.clear()

    systems = await get_inactive_systems(
        session,
        'diagnosis',
    )

    await show(
        callback,
        '♻️ <b>Система восстановлена</b>\n\n'
        f'<b>{esc(system.name)}</b>\n\n'
        'Она снова доступна в разделе диагностики.',
        admin_inactive_systems_keyboard(systems),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'system_add')
)
async def admin_add_system(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Начинает FSM-сценарий добавления новой системы."""
    await state.set_state(
        AdminSystemStates.waiting_name
    )

    await show(
        callback,
        '➕ <b>Добавление системы</b>\n\n'
        'Введите название системы:',
    )


@router.message(
    AdminSystemStates.waiting_name
)
async def admin_system_name(
    message: Message,
    state: FSMContext,
) -> None:
    # Права проверяет IsAdmin на уровне роутера.
    # message.text может быть None (фото, стикер и т.п.).
    """Принимает название новой системы."""
    name = (message.text or '').strip()

    if not name:
        await message.answer(
            'Название не может быть пустым.\n\n'
            'Введите название системы:'
        )
        return

    await state.update_data(
        system_name=name
    )

    await state.set_state(
        AdminSystemStates.waiting_sort_order
    )

    await message.answer(
        'Введите порядковый номер системы.\n\n'
        'Например: <code>1</code>'
    )


@router.message(
    AdminSystemStates.waiting_sort_order
)
async def admin_system_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Принимает порядок сортировки и создаёт систему."""
    try:
        sort_order = int(
            (message.text or '').strip()
        )
    except (TypeError, ValueError):
        await message.answer(
            'Введите целое число.\n\n'
            'Например: <code>1</code>'
        )
        return

    data = await state.get_data()

    system = await create_system(
        session=session,
        name=data['system_name'],
        system_type='diagnosis',
        sort_order=sort_order,
    )

    await state.clear()

    systems = await get_systems(
        session,
        'diagnosis',
    )

    text = [
        '✅ <b>Система успешно добавлена!</b>',
        '',
        f'🗂 <b>{esc(system.name)}</b>',
        f'Порядок: {system.sort_order}',
        '',
        'Список систем:',
        '',
        *numbered_names(systems),
    ]

    await message.answer(
        '\n'.join(text),
        reply_markup=admin_systems_keyboard(
            systems
        ),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'system')
)
async def open_admin_system(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Показывает карточку активной системы."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    system = await get_system_or_alert(
        session,
        callback,
        system_id,
        not_found='Система не найдена или отключена.',
    )

    if system is None:
        return

    await state.clear()

    await show(
        callback,
        '🗂 <b>Система диагностики</b>\n\n'
        f'<b>Название:</b> {esc(system.name)}\n'
        f'<b>Тип:</b> {system.type}\n'
        f'<b>Порядок:</b> {system.sort_order}',
        admin_system_card_keyboard(system.id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'system_edit')
)
async def edit_admin_system(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинает FSM-сценарий редактирования названия системы."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    system = await get_system_or_alert(session, callback, system_id)

    if system is None:
        return

    await state.update_data(
        system_id=system.id,
    )

    await state.set_state(
        AdminSystemStates.editing_name
    )

    await show(
        callback,
        '✏️ <b>Редактирование системы</b>\n\n'
        f'Текущее название:\n'
        f'<b>{esc(system.name)}</b>\n\n'
        'Введите новое название:',
    )


@router.message(
    AdminSystemStates.editing_name
)
async def edit_admin_system_name(
    message: Message,
    state: FSMContext,
) -> None:
    # Права проверяет IsAdmin на уровне роутера.
    """Принимает новое название системы."""
    name = (message.text or '').strip()

    if not name:
        await message.answer(
            'Название не может быть пустым.\n\n'
            'Введите новое название:'
        )
        return

    await state.update_data(
        system_name=name,
    )

    await state.set_state(
        AdminSystemStates.editing_sort_order
    )

    await message.answer(
        'Введите новый порядковый номер.\n\n'
        'Например: <code>1</code>'
    )


@router.message(
    AdminSystemStates.editing_sort_order
)
async def edit_admin_system_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Принимает новый порядок сортировки системы."""
    try:
        sort_order = int(
            (message.text or '').strip()
        )
    except ValueError:
        await message.answer(
            'Введите целое число.\n\n'
            'Например: <code>1</code>'
        )
        return

    data = await state.get_data()

    system = await get_system(
        session,
        int(data['system_id']),
    )

    if system is None or not system.is_active:
        await state.clear()

        await message.answer(
            '❌ Система не найдена.'
        )
        return

    system = await update_system(
        session=session,
        system=system,
        name=data['system_name'],
        sort_order=sort_order,
    )

    await state.clear()

    await message.answer(
        '✅ <b>Система изменена</b>\n\n'
        f'<b>Название:</b> {esc(system.name)}\n'
        f'<b>Порядок:</b> {system.sort_order}',
        reply_markup=admin_system_card_keyboard(
            system.id
        ),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'system_deactivate')
)
async def deactivate_admin_system(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Отключает систему (мягкое удаление)."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    system = await get_system_or_alert(
        session,
        callback,
        system_id,
        require_active=False,
    )

    if system is None:
        return

    if not system.is_active:
        await alert(callback, 'Система уже отключена.')
        return

    await deactivate_system(
        session,
        system,
    )

    await state.clear()

    systems = await get_systems(
        session,
        'diagnosis',
    )

    text = [
        '⛔ <b>Система отключена</b>',
        '',
        f'<s>{esc(system.name)}</s>',
        '',
        'Активные системы:',
        '',
    ]

    text.extend(
        numbered_names(systems) or ['Активных систем нет.']
    )

    await show(
        callback,
        '\n'.join(text),
        admin_systems_keyboard(systems),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'system_problems')
)
async def admin_system_problems(
    callback: CallbackQuery,
) -> None:
    """Заглушка раздела проблем системы."""
    await alert(callback, 'Раздел проблем будет добавлен следующим шагом.')


@router.callback_query(
    AdminCB.filter(F.action == 'system_delete_confirm')
)
async def delete_admin_system_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Окончательно удаляет систему вместе с её данными."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    system = await get_system_or_alert(
        session,
        callback,
        system_id,
        require_active=False,
    )

    if system is None:
        return

    if system.is_active:
        await alert(callback, 'Нельзя удалить активную систему.')
        return

    system_name = system.name

    await delete_system(
        session,
        system,
    )

    await state.clear()

    systems = await get_inactive_systems(
        session,
        'diagnosis',
    )

    text = [
        '✅ <b>Система удалена окончательно</b>',
        '',
        f'<s>{esc(system_name)}</s>',
        '',
    ]

    if systems:
        text.extend(('🗑 <b>Отключённые системы:</b>', ''))
        text.extend(numbered_names(systems))
    else:
        text.append('Отключённых систем больше нет.')

    await show(
        callback,
        '\n'.join(text),
        admin_inactive_systems_keyboard(systems),
        answer_text='Система удалена.',
    )
