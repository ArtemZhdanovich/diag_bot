from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.callbacks import MenuCB


def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню пользователя; для админа добавляет раздел админки."""
    buttons = [
        [
            InlineKeyboardButton(
                text='🔧 Диагностика',
                callback_data=MenuCB(action='diagnosis').pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text='🧰 Инструмент',
                callback_data=MenuCB(action='tools').pack(),
            ),
        ],
    ]

    if is_admin:
        buttons.append(
            [
                InlineKeyboardButton(
                    text='⚙️ Админка',
                    callback_data=MenuCB(action='admin').pack(),
                ),
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)