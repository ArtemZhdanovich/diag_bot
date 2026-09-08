"""Типизированные фабрики callback_data вместо ручного парсинга строк.

Каждая фабрика сериализуется в строку вида "<prefix>:<field>:..." и
валидуется при разборе, поэтому хендлерам больше не нужны
split(":") и int() вручную.
"""

from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix='menu'):
    """Действия главного меню."""

    action: str  # main | diagnosis | tools | admin


class DiagnosisCB(CallbackData, prefix='diagnosis'):
    """Навигация в разделе диагностики."""

    # system | problem | cause | back_systems | back_problems
    # | back_causes
    action: str
    id: int | None = None


class ToolsCB(CallbackData, prefix='tools'):
    """Навигация в разделе инструментов."""

    # category | node | select_node | confirm_nodes
    # | back_categories | back_nodes
    action: str
    id: int | None = None  # id узла; для back_nodes — id системы
    category: str | None = None  # ключ категории для action="category"


class AdminCB(CallbackData, prefix='admin'):
    """Навигация в админ-панели."""

    action: str  # см. хендлеры в app.bot.handlers.admin
    id: int | None = None
