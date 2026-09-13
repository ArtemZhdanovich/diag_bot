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
    admin_card_keyboard,
    admin_cause_card_keyboard,
    admin_causes_keyboard,
    admin_delete_cause_confirm_keyboard,
    admin_delete_problem_confirm_keyboard,
    admin_delete_system_confirm_keyboard,
    admin_diagnosis_keyboard,
    admin_inactive_cause_card_keyboard,
    admin_inactive_causes_keyboard,
    admin_inactive_problem_card_keyboard,
    admin_inactive_problems_keyboard,
    admin_inactive_system_card_keyboard,
    admin_inactive_systems_keyboard,
    admin_main_keyboard,
    admin_problem_card_keyboard,
    admin_problems_keyboard,
    admin_system_card_keyboard,
    admin_systems_keyboard,
    admin_tool_systems_keyboard,
)
from app.bot.states.admin import (
    AdminCardStates,
    AdminCauseStates,
    AdminProblemStates,
    AdminSystemStates,
)
from app.database.repositories.cause import (
    create_cause,
    deactivate_cause,
    delete_cause,
    get_cause,
    get_causes,
    get_inactive_causes,
    restore_cause,
    update_cause,
)
from app.database.repositories.cause_card import (
    add_image,
    create_card,
    get_card_by_cause,
    update_card,
)
from app.database.repositories.problem import (
    create_problem,
    deactivate_problem,
    delete_problem,
    get_inactive_problems,
    get_problem,
    get_problems,
    restore_problem,
    update_problem,
)
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
from app.database.repositories.user import get_users
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
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Раздел администрирования инструментов."""
    await state.clear()

    systems = await get_systems(session, 'tool')

    if not systems:
        await show(
            callback,
            '🧰 <b>Управление инструментами</b>\n\n'
            'Систем пока нет.',
            admin_back_keyboard(),
        )
        return

    text = [
        '🧰 <b>Управление инструментами</b>',
        '',
        *numbered_names(systems),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_tool_systems_keyboard(systems),
    )


@router.callback_query(AdminCB.filter(F.action == 'users'))
async def admin_users(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список пользователей со статистикой."""
    await state.clear()

    users = await get_users(session)

    text = [
        '👥 <b>Пользователи</b>',
        '',
        f'<b>Всего:</b> {len(users)}',
        '',
    ]

    if not users:
        text.append('Пользователей пока нет.')
    else:
        text.append('<b>Последние пользователи:</b>')
        text.append('')

        for user in users[-10:]:
            name = user.first_name or user.username or '—'
            login = f' (@{user.username})' if user.username else ''
            created = (
                user.created_at.strftime('%d.%m.%Y')
                if user.created_at
                else '—'
            )

            text.append(
                f'• {esc(name)}{login} — {created}'
            )

    await show(
        callback,
        '\n'.join(text),
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

    system_name = data.get('system_name')

    if system_name is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить название системы.\n'
            'Попробуйте добавить систему заново.'
        )
        return

    system = await create_system(
        session=session,
        name=system_name,
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

    system_id = data.get('system_id')
    system_name = data.get('system_name')

    if system_id is None or system_name is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные системы.\n'
            'Попробуйте отредактировать систему заново.'
        )
        return

    system = await get_system(
        session,
        int(system_id),
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
        name=system_name,
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
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список активных проблем системы."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    system = await get_system_or_alert(session, callback, system_id)

    if system is None:
        return

    await state.clear()

    problems = await get_problems(session, system_id)

    if not problems:
        await show(
            callback,
            f'🔴 <b>Проблемы системы</b>\n\n'
            f'<b>{esc(system.name)}</b>\n\n'
            'Проблем пока нет.',
            admin_problems_keyboard(problems, system_id),
        )
        return

    text = [
        '🔴 <b>Проблемы системы</b>',
        '',
        f'<b>{esc(system.name)}</b>',
        '',
        *numbered_names(problems),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_problems_keyboard(problems, system_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'problems_inactive')
)
async def admin_inactive_problems(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список отключённых проблем системы."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    system = await get_system_or_alert(session, callback, system_id)

    if system is None:
        return

    await state.clear()

    problems = await get_inactive_problems(session, system_id)

    if not problems:
        await show(
            callback,
            '🗑 <b>Отключённые проблемы</b>\n\n'
            'Отключённых проблем нет.',
            admin_inactive_problems_keyboard(problems, system_id),
        )
        return

    text = [
        '🗑 <b>Отключённые проблемы</b>',
        '',
        *numbered_names(problems),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_inactive_problems_keyboard(problems, system_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'problem')
)
async def open_admin_problem(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Карточка активной проблемы."""
    if (problem_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Проблема не найдена.')
        return

    problem = await get_problem(session, problem_id)

    if problem is None or not problem.is_active:
        await alert(callback, 'Проблема не найдена или отключена.')
        return

    await state.clear()

    await show(
        callback,
        '🔴 <b>Проблема</b>\n\n'
        f'<b>Название:</b> {esc(problem.name)}\n'
        f'<b>Порядок:</b> {problem.sort_order}',
        admin_problem_card_keyboard(problem.id, problem.system_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'inactive_problem')
)
async def open_inactive_admin_problem(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Карточка отключённой проблемы."""
    if (problem_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Проблема не найдена.')
        return

    problem = await get_problem(session, problem_id)

    if problem is None or problem.is_active:
        await alert(callback, 'Проблема не найдена или уже восстановлена.')
        return

    await state.clear()

    await show(
        callback,
        '🗑 <b>Отключённая проблема</b>\n\n'
        f'<b>Название:</b> {esc(problem.name)}\n'
        f'<b>Порядок:</b> {problem.sort_order}\n\n'
        'Проблема не отображается пользователям.',
        admin_inactive_problem_card_keyboard(problem.id, problem.system_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'problem_add')
)
async def admin_add_problem(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Начинает FSM-сценарий добавления проблемы."""
    if (system_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    await state.update_data(system_id=system_id)

    await state.set_state(AdminProblemStates.waiting_name)

    await show(
        callback,
        '➕ <b>Добавление проблемы</b>\n\n'
        'Введите название проблемы:',
    )


@router.message(
    AdminProblemStates.waiting_name
)
async def admin_problem_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Принимает название новой проблемы."""
    name = (message.text or '').strip()

    if not name:
        await message.answer(
            'Название не может быть пустым.\n\n'
            'Введите название проблемы:'
        )
        return

    await state.update_data(problem_name=name)

    await state.set_state(AdminProblemStates.waiting_sort_order)

    await message.answer(
        'Введите порядковый номер проблемы.\n\n'
        'Например: <code>1</code>'
    )


@router.message(
    AdminProblemStates.waiting_sort_order
)
async def admin_problem_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Принимает порядок сортировки и создаёт проблему."""
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
    problem_name = data.get('problem_name')

    if system_id is None or problem_name is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные проблемы.\n'
            'Попробуйте добавить проблему заново.'
        )
        return

    problem = await create_problem(
        session=session,
        system_id=int(system_id),
        name=problem_name,
        sort_order=sort_order,
    )

    await state.clear()

    problems = await get_problems(session, int(system_id))

    text = [
        '✅ <b>Проблема успешно добавлена!</b>',
        '',
        f'🔴 <b>{esc(problem.name)}</b>',
        f'Порядок: {problem.sort_order}',
        '',
        'Список проблем:',
        '',
        *numbered_names(problems),
    ]

    await message.answer(
        '\n'.join(text),
        reply_markup=admin_problems_keyboard(problems, int(system_id)),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'problem_edit')
)
async def edit_admin_problem(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинает FSM-сценарий редактирования проблемы."""
    if (problem_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Проблема не найдена.')
        return

    problem = await get_problem(session, problem_id)

    if problem is None or not problem.is_active:
        await alert(callback, 'Проблема не найдена.')
        return

    await state.update_data(
        problem_id=problem.id,
        system_id=problem.system_id,
    )

    await state.set_state(AdminProblemStates.editing_name)

    await show(
        callback,
        '✏️ <b>Редактирование проблемы</b>\n\n'
        f'Текущее название:\n'
        f'<b>{esc(problem.name)}</b>\n\n'
        'Введите новое название:',
    )


@router.message(
    AdminProblemStates.editing_name
)
async def edit_admin_problem_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Принимает новое название проблемы."""
    name = (message.text or '').strip()

    if not name:
        await message.answer(
            'Название не может быть пустым.\n\n'
            'Введите новое название:'
        )
        return

    await state.update_data(problem_name=name)

    await state.set_state(AdminProblemStates.editing_sort_order)

    await message.answer(
        'Введите новый порядковый номер.\n\n'
        'Например: <code>1</code>'
    )


@router.message(
    AdminProblemStates.editing_sort_order
)
async def edit_admin_problem_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Принимает новый порядок сортировки проблемы."""
    try:
        sort_order = int((message.text or '').strip())
    except ValueError:
        await message.answer(
            'Введите целое число.\n\n'
            'Например: <code>1</code>'
        )
        return

    data = await state.get_data()

    problem_id = data.get('problem_id')
    system_id = data.get('system_id')
    problem_name = data.get('problem_name')

    if problem_id is None or system_id is None or problem_name is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные проблемы.\n'
            'Попробуйте отредактировать проблему заново.'
        )
        return

    problem = await get_problem(session, int(problem_id))

    if problem is None or not problem.is_active:
        await state.clear()

        await message.answer(
            '❌ Проблема не найдена.'
        )
        return

    problem = await update_problem(
        session=session,
        problem=problem,
        name=problem_name,
        sort_order=sort_order,
    )

    await state.clear()

    await message.answer(
        '✅ <b>Проблема изменена</b>\n\n'
        f'<b>Название:</b> {esc(problem.name)}\n'
        f'<b>Порядок:</b> {problem.sort_order}',
        reply_markup=admin_problem_card_keyboard(
            problem.id,
            int(system_id),
        ),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'problem_deactivate')
)
async def deactivate_admin_problem(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Отключает проблему (мягкое удаление)."""
    if (problem_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Проблема не найдена.')
        return

    problem = await get_problem(session, problem_id)

    if problem is None or not problem.is_active:
        await alert(callback, 'Проблема уже отключена.')
        return

    system_id = problem.system_id

    await deactivate_problem(session, problem)

    await state.clear()

    problems = await get_problems(session, system_id)

    text = [
        '⛔ <b>Проблема отключена</b>',
        '',
        f'<s>{esc(problem.name)}</s>',
        '',
        'Активные проблемы:',
        '',
    ]

    text.extend(
        numbered_names(problems) or ['Активных проблем нет.']
    )

    await show(
        callback,
        '\n'.join(text),
        admin_problems_keyboard(problems, system_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'problem_restore')
)
async def restore_admin_problem(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Восстанавливает отключённую проблему."""
    if (problem_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Проблема не найдена.')
        return

    problem = await get_problem(session, problem_id)

    if problem is None or problem.is_active:
        await alert(callback, 'Проблема уже активна.')
        return

    system_id = problem.system_id

    problem = await restore_problem(session, problem)

    await state.clear()

    problems = await get_inactive_problems(session, system_id)

    await show(
        callback,
        '♻️ <b>Проблема восстановлена</b>\n\n'
        f'<b>{esc(problem.name)}</b>\n\n'
        'Она снова доступна в разделе диагностики.',
        admin_inactive_problems_keyboard(problems, system_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'problem_delete')
)
async def delete_admin_problem_warning(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Предупреждение перед окончательным удалением проблемы."""
    if (problem_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Проблема не найдена.')
        return

    problem = await get_problem(session, problem_id)

    if problem is None:
        await alert(callback, 'Проблема не найдена.')
        return

    if problem.is_active:
        await alert(callback, 'Сначала отключите проблему.')
        return

    await state.clear()

    await show(
        callback,
        '⚠️ <b>Окончательное удаление</b>\n\n'
        f'Проблема:\n'
        f'<b>{esc(problem.name)}</b>\n\n'
        'После удаления будут потеряны связанные '
        'данные этой проблемы.\n\n'
        'Это действие нельзя отменить.\n\n'
        '<b>Вы действительно хотите удалить проблему?</b>',
        admin_delete_problem_confirm_keyboard(
            problem.id,
            problem.system_id,
        ),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'problem_delete_confirm')
)
async def delete_admin_problem_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Окончательно удаляет проблему вместе с её данными."""
    if (problem_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Проблема не найдена.')
        return

    problem = await get_problem(session, problem_id)

    if problem is None:
        await alert(callback, 'Проблема не найдена.')
        return

    if problem.is_active:
        await alert(callback, 'Нельзя удалить активную проблему.')
        return

    system_id = problem.system_id
    problem_name = problem.name

    await delete_problem(session, problem)

    await state.clear()

    problems = await get_inactive_problems(session, system_id)

    text = [
        '✅ <b>Проблема удалена окончательно</b>',
        '',
        f'<s>{esc(problem_name)}</s>',
        '',
    ]

    if problems:
        text.extend(('🗑 <b>Отключённые проблемы:</b>', ''))
        text.extend(numbered_names(problems))
    else:
        text.append('Отключённых проблем больше нет.')

    await show(
        callback,
        '\n'.join(text),
        admin_inactive_problems_keyboard(problems, system_id),
        answer_text='Проблема удалена.',
    )


@router.callback_query(
    AdminCB.filter(F.action == 'problem_causes')
)
async def admin_problem_causes(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список активных причин проблемы."""
    if (problem_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Проблема не найдена.')
        return

    problem = await get_problem(session, problem_id)

    if problem is None or not problem.is_active:
        await alert(callback, 'Проблема не найдена или отключена.')
        return

    await state.clear()

    causes = await get_causes(session, problem_id)

    if not causes:
        await show(
            callback,
            f'⚠️ <b>Причины проблемы</b>\n\n'
            f'<b>{esc(problem.name)}</b>\n\n'
            'Причин пока нет.',
            admin_causes_keyboard(causes, problem_id),
        )
        return

    text = [
        '⚠️ <b>Причины проблемы</b>',
        '',
        f'<b>{esc(problem.name)}</b>',
        '',
        *numbered_names(causes),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_causes_keyboard(causes, problem_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'causes_inactive')
)
async def admin_inactive_causes(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Список отключённых причин проблемы."""
    if (problem_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Проблема не найдена.')
        return

    problem = await get_problem(session, problem_id)

    if problem is None:
        await alert(callback, 'Проблема не найдена.')
        return

    await state.clear()

    causes = await get_inactive_causes(session, problem_id)

    if not causes:
        await show(
            callback,
            '🗑 <b>Отключённые причины</b>\n\n'
            'Отключённых причин нет.',
            admin_inactive_causes_keyboard(causes, problem_id),
        )
        return

    text = [
        '🗑 <b>Отключённые причины</b>',
        '',
        *numbered_names(causes),
    ]

    await show(
        callback,
        '\n'.join(text),
        admin_inactive_causes_keyboard(causes, problem_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'cause')
)
async def open_admin_cause(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Карточка активной причины."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None or not cause.is_active:
        await alert(callback, 'Причина не найдена или отключена.')
        return

    await state.clear()

    await show(
        callback,
        '⚠️ <b>Причина</b>\n\n'
        f'<b>Название:</b> {esc(cause.name)}\n'
        f'<b>Порядок:</b> {cause.sort_order}',
        admin_cause_card_keyboard(cause.id, cause.problem_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'inactive_cause')
)
async def open_inactive_admin_cause(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Карточка отключённой причины."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None or cause.is_active:
        await alert(callback, 'Причина не найдена или уже восстановлена.')
        return

    await state.clear()

    await show(
        callback,
        '🗑 <b>Отключённая причина</b>\n\n'
        f'<b>Название:</b> {esc(cause.name)}\n'
        f'<b>Порядок:</b> {cause.sort_order}\n\n'
        'Причина не отображается пользователям.',
        admin_inactive_cause_card_keyboard(cause.id, cause.problem_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'cause_add')
)
async def admin_add_cause(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Начинает FSM-сценарий добавления причины."""
    if (problem_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Проблема не найдена.')
        return

    await state.update_data(problem_id=problem_id)

    await state.set_state(AdminCauseStates.waiting_name)

    await show(
        callback,
        '➕ <b>Добавление причины</b>\n\n'
        'Введите название причины:',
    )


@router.message(
    AdminCauseStates.waiting_name
)
async def admin_cause_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Принимает название новой причины."""
    name = (message.text or '').strip()

    if not name:
        await message.answer(
            'Название не может быть пустым.\n\n'
            'Введите название причины:'
        )
        return

    await state.update_data(cause_name=name)

    await state.set_state(AdminCauseStates.waiting_sort_order)

    await message.answer(
        'Введите порядковый номер причины.\n\n'
        'Например: <code>1</code>'
    )


@router.message(
    AdminCauseStates.waiting_sort_order
)
async def admin_cause_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Принимает порядок сортировки и создаёт причину."""
    try:
        sort_order = int((message.text or '').strip())
    except (TypeError, ValueError):
        await message.answer(
            'Введите целое число.\n\n'
            'Например: <code>1</code>'
        )
        return

    data = await state.get_data()

    problem_id = data.get('problem_id')
    cause_name = data.get('cause_name')

    if problem_id is None or cause_name is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные причины.\n'
            'Попробуйте добавить причину заново.'
        )
        return

    cause = await create_cause(
        session=session,
        problem_id=int(problem_id),
        name=cause_name,
        sort_order=sort_order,
    )

    await state.clear()

    causes = await get_causes(session, int(problem_id))

    text = [
        '✅ <b>Причина успешно добавлена!</b>',
        '',
        f'⚠️ <b>{esc(cause.name)}</b>',
        f'Порядок: {cause.sort_order}',
        '',
        'Список причин:',
        '',
        *numbered_names(causes),
    ]

    await message.answer(
        '\n'.join(text),
        reply_markup=admin_causes_keyboard(causes, int(problem_id)),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'cause_edit')
)
async def edit_admin_cause(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинает FSM-сценарий редактирования причины."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None or not cause.is_active:
        await alert(callback, 'Причина не найдена.')
        return

    await state.update_data(
        cause_id=cause.id,
        problem_id=cause.problem_id,
    )

    await state.set_state(AdminCauseStates.editing_name)

    await show(
        callback,
        '✏️ <b>Редактирование причины</b>\n\n'
        f'Текущее название:\n'
        f'<b>{esc(cause.name)}</b>\n\n'
        'Введите новое название:',
    )


@router.message(
    AdminCauseStates.editing_name
)
async def edit_admin_cause_name(
    message: Message,
    state: FSMContext,
) -> None:
    """Принимает новое название причины."""
    name = (message.text or '').strip()

    if not name:
        await message.answer(
            'Название не может быть пустым.\n\n'
            'Введите новое название:'
        )
        return

    await state.update_data(cause_name=name)

    await state.set_state(AdminCauseStates.editing_sort_order)

    await message.answer(
        'Введите новый порядковый номер.\n\n'
        'Например: <code>1</code>'
    )


@router.message(
    AdminCauseStates.editing_sort_order
)
async def edit_admin_cause_sort_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Принимает новый порядок сортировки причины."""
    try:
        sort_order = int((message.text or '').strip())
    except ValueError:
        await message.answer(
            'Введите целое число.\n\n'
            'Например: <code>1</code>'
        )
        return

    data = await state.get_data()

    cause_id = data.get('cause_id')
    problem_id = data.get('problem_id')
    cause_name = data.get('cause_name')

    if cause_id is None or problem_id is None or cause_name is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные причины.\n'
            'Попробуйте отредактировать причину заново.'
        )
        return

    cause = await get_cause(session, int(cause_id))

    if cause is None or not cause.is_active:
        await state.clear()

        await message.answer(
            '❌ Причина не найдена.'
        )
        return

    cause = await update_cause(
        session=session,
        cause=cause,
        name=cause_name,
        sort_order=sort_order,
    )

    await state.clear()

    await message.answer(
        '✅ <b>Причина изменена</b>\n\n'
        f'<b>Название:</b> {esc(cause.name)}\n'
        f'<b>Порядок:</b> {cause.sort_order}',
        reply_markup=admin_cause_card_keyboard(
            cause.id,
            int(problem_id),
        ),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'cause_deactivate')
)
async def deactivate_admin_cause(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Отключает причину (мягкое удаление)."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None or not cause.is_active:
        await alert(callback, 'Причина уже отключена.')
        return

    problem_id = cause.problem_id

    await deactivate_cause(session, cause)

    await state.clear()

    causes = await get_causes(session, problem_id)

    text = [
        '⛔ <b>Причина отключена</b>',
        '',
        f'<s>{esc(cause.name)}</s>',
        '',
        'Активные причины:',
        '',
    ]

    text.extend(
        numbered_names(causes) or ['Активных причин нет.']
    )

    await show(
        callback,
        '\n'.join(text),
        admin_causes_keyboard(causes, problem_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'cause_restore')
)
async def restore_admin_cause(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Восстанавливает отключённую причину."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None or cause.is_active:
        await alert(callback, 'Причина уже активна.')
        return

    problem_id = cause.problem_id

    cause = await restore_cause(session, cause)

    await state.clear()

    causes = await get_inactive_causes(session, problem_id)

    await show(
        callback,
        '♻️ <b>Причина восстановлена</b>\n\n'
        f'<b>{esc(cause.name)}</b>\n\n'
        'Она снова доступна в разделе диагностики.',
        admin_inactive_causes_keyboard(causes, problem_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'cause_delete')
)
async def delete_admin_cause_warning(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Предупреждение перед окончательным удалением причины."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None:
        await alert(callback, 'Причина не найдена.')
        return

    if cause.is_active:
        await alert(callback, 'Сначала отключите причину.')
        return

    await state.clear()

    await show(
        callback,
        '⚠️ <b>Окончательное удаление</b>\n\n'
        f'Причина:\n'
        f'<b>{esc(cause.name)}</b>\n\n'
        'После удаления будут потеряны связанные '
        'данные этой причины.\n\n'
        'Это действие нельзя отменить.\n\n'
        '<b>Вы действительно хотите удалить причину?</b>',
        admin_delete_cause_confirm_keyboard(
            cause.id,
            cause.problem_id,
        ),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'cause_delete_confirm')
)
async def delete_admin_cause_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Окончательно удаляет причину вместе с её данными."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None:
        await alert(callback, 'Причина не найдена.')
        return

    if cause.is_active:
        await alert(callback, 'Нельзя удалить активную причину.')
        return

    problem_id = cause.problem_id
    cause_name = cause.name

    await delete_cause(session, cause)

    await state.clear()

    causes = await get_inactive_causes(session, problem_id)

    text = [
        '✅ <b>Причина удалена окончательно</b>',
        '',
        f'<s>{esc(cause_name)}</s>',
        '',
    ]

    if causes:
        text.extend(('🗑 <b>Отключённые причины:</b>', ''))
        text.extend(numbered_names(causes))
    else:
        text.append('Отключённых причин больше нет.')

    await show(
        callback,
        '\n'.join(text),
        admin_inactive_causes_keyboard(causes, problem_id),
        answer_text='Причина удалена.',
    )


@router.callback_query(
    AdminCB.filter(F.action == 'cause_card')
)
async def open_admin_cause_card(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Показывает карточку причины."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None or not cause.is_active:
        await alert(callback, 'Причина не найдена.')
        return

    card = await get_card_by_cause(session, cause_id)

    if card is None:
        card = await create_card(session, cause_id=cause_id)

    await state.clear()

    text = [
        '📋 <b>Карточка причины</b>',
        '',
        f'<b>{esc(cause.name)}</b>',
        '',
    ]

    if card.description:
        text.extend(('📋 <b>Описание</b>', esc(card.description), ''))
    else:
        text.append('📋 Описание: <i>не заполнено</i>')
        text.append('')

    if card.inspection:
        text.extend(('🔍 <b>Проверка</b>', esc(card.inspection), ''))
    else:
        text.append('🔍 Проверка: <i>не заполнена</i>')
        text.append('')

    if card.recommendation:
        text.extend(('🛠 <b>Рекомендации</b>', esc(card.recommendation), ''))
    else:
        text.append('🛠 Рекомендации: <i>не заполнены</i>')
        text.append('')

    if card.images:
        text.append(f'🖼 Фото: {len(card.images)}')
    else:
        text.append('🖼 Фото: нет')

    await show(
        callback,
        '\n'.join(text),
        admin_card_keyboard(cause_id, cause.problem_id),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'card_edit_description')
)
async def edit_card_description(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинает редактирование описания карточки."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None or not cause.is_active:
        await alert(callback, 'Причина не найдена.')
        return

    card = await get_card_by_cause(session, cause_id)

    if card is None:
        card = await create_card(session, cause_id=cause_id)

    await state.update_data(
        card_id=card.id,
        cause_id=cause_id,
        problem_id=cause.problem_id,
    )

    await state.set_state(AdminCardStates.editing_description)

    current = (
        f'\n\nТекущее:\n{esc(card.description)}'
        if card.description
        else ''
    )

    await show(
        callback,
        '📝 <b>Редактирование описания</b>\n\n'
        'Введите новое описание (или <code>/</code> для очистки):'
        f'{current}',
    )


@router.message(
    AdminCardStates.editing_description
)
async def save_card_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Сохраняет описание карточки."""
    data = await state.get_data()

    card_id = data.get('card_id')
    cause_id = data.get('cause_id')
    problem_id = data.get('problem_id')

    if card_id is None or cause_id is None or problem_id is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные карточки.\n'
            'Попробуйте ещё раз.'
        )
        return

    text = (message.text or '').strip()

    card = await get_card_by_cause(session, int(cause_id))

    if card is None:
        await state.clear()

        await message.answer(
            '❌ Карточка не найдена.'
        )
        return

    description = None if text == '/' else (text or None)

    card = await update_card(
        session=session,
        card=card,
        description=description,
        inspection=card.inspection,
        recommendation=card.recommendation,
    )

    await state.clear()

    await message.answer(
        '✅ <b>Описание обновлено</b>',
        reply_markup=admin_card_keyboard(int(cause_id), int(problem_id)),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'card_edit_inspection')
)
async def edit_card_inspection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинает редактирование проверки карточки."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None or not cause.is_active:
        await alert(callback, 'Причина не найдена.')
        return

    card = await get_card_by_cause(session, cause_id)

    if card is None:
        card = await create_card(session, cause_id=cause_id)

    await state.update_data(
        card_id=card.id,
        cause_id=cause_id,
        problem_id=cause.problem_id,
    )

    await state.set_state(AdminCardStates.editing_inspection)

    current = (
        f'\n\nТекущее:\n{esc(card.inspection)}'
        if card.inspection
        else ''
    )

    await show(
        callback,
        '🔍 <b>Редактирование проверки</b>\n\n'
        'Введите методику проверки (или <code>/</code> для очистки):'
        f'{current}',
    )


@router.message(
    AdminCardStates.editing_inspection
)
async def save_card_inspection(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Сохраняет проверку карточки."""
    data = await state.get_data()

    cause_id = data.get('cause_id')
    problem_id = data.get('problem_id')

    if cause_id is None or problem_id is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные карточки.\n'
            'Попробуйте ещё раз.'
        )
        return

    text = (message.text or '').strip()
    card = await get_card_by_cause(session, int(cause_id))

    if card is None:
        await state.clear()

        await message.answer(
            '❌ Карточка не найдена.'
        )
        return

    inspection = None if text == '/' else (text or None)

    card = await update_card(
        session=session,
        card=card,
        description=card.description,
        inspection=inspection,
        recommendation=card.recommendation,
    )

    await state.clear()

    await message.answer(
        '✅ <b>Проверка обновлена</b>',
        reply_markup=admin_card_keyboard(int(cause_id), int(problem_id)),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'card_edit_recommendation')
)
async def edit_card_recommendation(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинает редактирование рекомендаций карточки."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None or not cause.is_active:
        await alert(callback, 'Причина не найдена.')
        return

    card = await get_card_by_cause(session, cause_id)

    if card is None:
        card = await create_card(session, cause_id=cause_id)

    await state.update_data(
        card_id=card.id,
        cause_id=cause_id,
        problem_id=cause.problem_id,
    )

    await state.set_state(AdminCardStates.editing_recommendation)

    current = (
        f'\n\nТекущее:\n{esc(card.recommendation)}'
        if card.recommendation
        else ''
    )

    await show(
        callback,
        '🛠 <b>Редактирование рекомендаций</b>\n\n'
        'Введите рекомендации (или <code>/</code> для очистки):'
        f'{current}',
    )


@router.message(
    AdminCardStates.editing_recommendation
)
async def save_card_recommendation(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Сохраняет рекомендации карточки."""
    data = await state.get_data()

    cause_id = data.get('cause_id')
    problem_id = data.get('problem_id')

    if cause_id is None or problem_id is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные карточки.\n'
            'Попробуйте ещё раз.'
        )
        return

    text = (message.text or '').strip()
    card = await get_card_by_cause(session, int(cause_id))

    if card is None:
        await state.clear()

        await message.answer(
            '❌ Карточка не найдена.'
        )
        return

    recommendation = None if text == '/' else (text or None)

    card = await update_card(
        session=session,
        card=card,
        description=card.description,
        inspection=card.inspection,
        recommendation=recommendation,
    )

    await state.clear()

    await message.answer(
        '✅ <b>Рекомендации обновлены</b>',
        reply_markup=admin_card_keyboard(int(cause_id), int(problem_id)),
    )


@router.callback_query(
    AdminCB.filter(F.action == 'card_add_image')
)
async def add_card_image(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинает добавление фото к карточке."""
    if (cause_id := unpack_id(callback, AdminCB)) is None:
        await alert(callback, 'Причина не найдена.')
        return

    cause = await get_cause(session, cause_id)

    if cause is None or not cause.is_active:
        await alert(callback, 'Причина не найдена.')
        return

    card = await get_card_by_cause(session, cause_id)

    if card is None:
        card = await create_card(session, cause_id=cause_id)

    await state.update_data(
        card_id=card.id,
        cause_id=cause_id,
        problem_id=cause.problem_id,
    )

    await state.set_state(AdminCardStates.waiting_image)

    await show(
        callback,
        '🖼 <b>Добавление фото</b>\n\n'
        'Пришлите фото для карточки:',
    )


@router.message(
    AdminCardStates.waiting_image,
    F.photo
)
async def save_card_image(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Сохраняет фото карточки."""
    data = await state.get_data()

    cause_id = data.get('cause_id')
    problem_id = data.get('problem_id')

    if cause_id is None or problem_id is None:
        await state.clear()

        await message.answer(
            '❌ Не удалось определить данные карточки.\n'
            'Попробуйте ещё раз.'
        )
        return

    card = await get_card_by_cause(session, int(cause_id))

    if card is None:
        await state.clear()

        await message.answer(
            '❌ Карточка не найдена.'
        )
        return

    if message.photo is None:
        await state.clear()

        await message.answer(
            '❌ Фото не получено.\n'
            'Попробуйте ещё раз.'
        )
        return

    photo = message.photo[-1]

    await add_image(
        session=session,
        card_id=card.id,
        telegram_file_id=photo.file_id,
        caption=message.caption,
        sort_order=len(card.images),
    )

    await state.clear()

    await message.answer(
        '✅ <b>Фото добавлено</b>',
        reply_markup=admin_card_keyboard(int(cause_id), int(problem_id)),
    )


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
