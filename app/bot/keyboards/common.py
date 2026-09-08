"""Общие помощники для сборки инлайн-клавиатур.

Убирают дублирование навигационных рядов «⬅️ Назад» / «🏠 В меню»,
которые раньше копировались вручную в каждой клавиатуре.
"""

from aiogram.types import InlineKeyboardButton

from app.bot.callbacks import MenuCB


MENU_BUTTON_TEXT = '🏠 В меню'


def button(text: str, callback_data: str) -> InlineKeyboardButton:
    """Создаёт инлайн-кнопку с текстом и callback_data."""
    return InlineKeyboardButton(
        text=text,
        callback_data=callback_data,
    )


def stack(*buttons_: InlineKeyboardButton) -> list[list[InlineKeyboardButton]]:
    """Раскладывает кнопки по одной в ряд."""
    return [[item] for item in buttons_]


def with_nav(
    rows: list[list[InlineKeyboardButton]],
    back: InlineKeyboardButton | None = None,
    menu: bool = True,
) -> list[list[InlineKeyboardButton]]:
    """Добавляет к рядам кнопок ряды навигации.

    back — готовая кнопка «Назад» (None — не добавлять);
    menu — добавить ли ряд «🏠 В меню».
    """
    result = list(rows)

    if back is not None:
        result.append([back])

    if menu:
        result.append(
            [button(MENU_BUTTON_TEXT, MenuCB(action='main').pack())]
        )

    return result