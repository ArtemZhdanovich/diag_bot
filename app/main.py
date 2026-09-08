import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import (
    admin,
    diagnosis,
    navigation,
    start,
    tools,
)
from app.bot.middlewares.database import DatabaseMiddleware
from app.config import get_settings


async def main() -> None:
    """Точка входа: запускает long polling бота."""
    settings = get_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dp = Dispatcher()

    dp.update.middleware(DatabaseMiddleware())

    dp.include_router(start.router)
    dp.include_router(navigation.router)
    dp.include_router(diagnosis.router)
    dp.include_router(tools.router)
    dp.include_router(admin.router)

    logging.basicConfig(
        level=logging.INFO,
    )

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
