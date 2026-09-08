from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.callbacks import MenuCB
from app.bot.helpers import show
from app.bot.keyboards.main import main_menu_keyboard
from app.services.admin import is_admin


router = Router()


@router.callback_query(MenuCB.filter(F.action == 'main'))
async def back_to_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Показывает главное меню и сбрасывает FSM-состояние."""
    await state.clear()

    user_id = callback.from_user.id

    await show(
        callback,
        '📋 <b>Главное меню</b>\n\n'
        'Выберите нужный раздел:',
        main_menu_keyboard(is_admin(user_id)),
    )
