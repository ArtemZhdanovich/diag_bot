from html import escape as esc

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks import DiagnosisCB, MenuCB
from app.bot.helpers import (
    CAUSE_NOT_FOUND,
    PROBLEM_NOT_FOUND,
    SYSTEM_NOT_FOUND,
    alert,
    get_cause_or_alert,
    get_problem_or_alert,
    get_system_or_alert,
    show,
    unpack_id,
)
from app.bot.keyboards.diagnosis import (
    cause_card_keyboard,
    diagnosis_causes_keyboard,
    diagnosis_problems_keyboard,
    diagnosis_systems_keyboard,
)
from app.bot.states.diagnosis import DiagnosisStates
from app.database.models import Problem, System
from app.database.repositories.cause import get_causes
from app.database.repositories.problem import get_problems
from app.database.repositories.system import get_systems
from app.services.cards import format_cause_card


router = Router()


async def show_diagnosis_systems(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Экран выбора системы — общий для входа и кнопки «Назад»."""
    systems = await get_systems(session, 'diagnosis')

    await state.set_state(DiagnosisStates.system)

    if not systems:
        await show(
            callback,
            '🔧 <b>Диагностика</b>\n\n'
            'Раздел пока не заполнен.',
        )
        return

    await show(
        callback,
        '🔧 <b>Диагностика</b>\n\n'
        'Выберите систему:',
        diagnosis_systems_keyboard(systems),
    )


async def show_system_problems(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    system: System,
    system_id: int,
) -> None:
    """Экран проблем системы — общий для выбора системы и «Назад»."""
    problems = await get_problems(session, system_id)

    await state.update_data(
        system_id=system_id,
        system_name=system.name,
    )
    await state.set_state(DiagnosisStates.problem)

    if not problems:
        await show(
            callback,
            f'🔧 <b>{esc(system.name)}</b>\n\n'
            'Для этой системы пока нет проблем.',
        )
        return

    await show(
        callback,
        f'🔧 <b>{esc(system.name)}</b>\n\n'
        'Выберите проблему:',
        diagnosis_problems_keyboard(problems),
    )


async def show_problem_causes(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    problem: Problem,
    problem_id: int,
) -> None:
    """Экран причин проблемы — общий для выбора проблемы и «Назад»."""
    causes = await get_causes(session, problem_id)

    await state.update_data(
        problem_id=problem_id,
        problem_name=problem.name,
    )
    await state.set_state(DiagnosisStates.cause)

    if not causes:
        await show(
            callback,
            f'⚠️ <b>{esc(problem.name)}</b>\n\n'
            'Вероятные причины пока не добавлены.',
        )
        return

    await show(
        callback,
        f'⚠️ <b>{esc(problem.name)}</b>\n\n'
        'Выберите вероятную причину:',
        diagnosis_causes_keyboard(causes),
    )


@router.callback_query(MenuCB.filter(F.action == 'diagnosis'))
async def open_diagnosis(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Открывает раздел диагностики."""
    await state.clear()

    await show_diagnosis_systems(callback, state, session)


@router.callback_query(DiagnosisCB.filter(F.action == 'system'))
async def select_diagnosis_system(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Показывает проблемы выбранной системы."""
    if (system_id := unpack_id(callback, DiagnosisCB)) is None:
        await alert(callback, SYSTEM_NOT_FOUND)
        return

    system = await get_system_or_alert(session, callback, system_id)

    if system is None:
        return

    await show_system_problems(callback, state, session, system, system_id)


@router.callback_query(DiagnosisCB.filter(F.action == 'problem'))
async def select_diagnosis_problem(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Показывает причины выбранной проблемы."""
    if (problem_id := unpack_id(callback, DiagnosisCB)) is None:
        await alert(callback, PROBLEM_NOT_FOUND)
        return

    problem = await get_problem_or_alert(session, callback, problem_id)

    if problem is None:
        return

    await show_problem_causes(
        callback,
        state,
        session,
        problem,
        problem_id,
    )


@router.callback_query(DiagnosisCB.filter(F.action == 'cause'))
async def open_cause_card(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Показывает карточку причины с изображениями."""
    if (cause_id := unpack_id(callback, DiagnosisCB)) is None:
        await alert(callback, CAUSE_NOT_FOUND)
        return

    cause = await get_cause_or_alert(session, callback, cause_id)

    if cause is None:
        return

    await state.update_data(
        cause_id=cause_id,
        cause_name=cause.name,
    )

    images = cause.card.images if cause.card else []

    message = callback.message

    if message is None or isinstance(message, InaccessibleMessage):
        await alert(callback, 'Сообщение недоступно.')
        return

    for image in images:
        await message.answer_photo(
            photo=image.telegram_file_id,
            caption=(
                esc(image.caption)
                if image.caption
                else None
            ),
        )

    await show(
        callback,
        format_cause_card(cause),
        cause_card_keyboard(),
    )


@router.callback_query(DiagnosisCB.filter(F.action == 'back_systems'))
async def back_to_systems(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Возвращает к списку систем диагностики."""
    await show_diagnosis_systems(callback, state, session)


@router.callback_query(DiagnosisCB.filter(F.action == 'back_problems'))
async def back_to_problems(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Возвращает к списку проблем системы."""
    data = await state.get_data()

    system_id = data.get('system_id')

    if system_id is None:
        await alert(callback, 'Не удалось определить систему.')
        return

    system = await get_system_or_alert(session, callback, system_id)

    if system is None:
        return

    await show_system_problems(callback, state, session, system, system_id)


@router.callback_query(DiagnosisCB.filter(F.action == 'back_causes'))
async def back_to_causes(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Возвращает к списку причин проблемы."""
    data = await state.get_data()

    problem_id = data.get('problem_id')

    if problem_id is None:
        await alert(callback, 'Не удалось определить проблему.')
        return

    problem = await get_problem_or_alert(session, callback, problem_id)

    if problem is None:
        return

    await show_problem_causes(
        callback,
        state,
        session,
        problem,
        problem_id,
    )
