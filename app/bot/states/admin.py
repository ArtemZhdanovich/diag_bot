from aiogram.fsm.state import State, StatesGroup


class AdminSystemStates(StatesGroup):
    """Состояния FSM добавления и редактирования системы."""

    waiting_name = State()
    waiting_sort_order = State()

    editing_name = State()
    editing_sort_order = State()
