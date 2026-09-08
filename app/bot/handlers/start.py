from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.main import main_menu_keyboard
from app.services.admin import is_admin


router = Router()


@router.message(CommandStart())
async def command_start(message: Message) -> None:
    """Обрабатывает команду /start: приветствие и меню."""
    user = message.from_user

    admin = is_admin(user.id) if user else False

    text = (
        '👋 <b>Добро пожаловать!</b>\n\n'
        'Это справочник диагноста.\n\n'
        'Здесь вы можете найти информацию о возможных '
        'неисправностях гидравлических систем и необходимом '
        'для диагностики инструменте.\n\n'
        'Выберите нужный раздел:'
    )

    await message.answer(
        text,
        reply_markup=main_menu_keyboard(admin),
    )
