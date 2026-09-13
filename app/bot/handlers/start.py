from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main import main_menu_keyboard
from app.database.repositories.user import get_or_create_user
from app.services.admin import is_admin


router = Router()


@router.message(CommandStart())
async def command_start(
    message: Message,
    session: AsyncSession,
) -> None:
    """Обрабатывает команду /start: регистрация, приветствие и меню."""
    user = message.from_user

    admin = is_admin(user.id) if user else False

    if user is not None:
        # Регистрируем пользователя (или обновляем профиль).
        await get_or_create_user(
            session,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
        )

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
