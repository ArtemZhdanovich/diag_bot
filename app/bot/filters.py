from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.services.admin import is_admin


class IsAdmin(BaseFilter):
    """Пропускает событие только от администратора из ADMIN_IDS.

    Вешается на роутер целиком (router.message.filter /
    router.callback_query.filter), чтобы проверка прав не зависела
    от ручного вызова в каждом хендлере — её невозможно забыть.
    """

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        """Разрешает хендлер только администраторам из ADMIN_IDS."""
        return (
            event.from_user is not None
            and is_admin(event.from_user.id)
        )