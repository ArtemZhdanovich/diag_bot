from aiogram.fsm.state import State, StatesGroup


class AdminSystemStates(StatesGroup):
    """Состояния FSM добавления и редактирования системы."""

    waiting_name = State()
    waiting_sort_order = State()

    editing_name = State()
    editing_sort_order = State()


class AdminProblemStates(StatesGroup):
    """Состояния FSM добавления и редактирования проблемы."""

    waiting_name = State()
    waiting_sort_order = State()

    editing_name = State()
    editing_sort_order = State()


class AdminCauseStates(StatesGroup):
    """Состояния FSM добавления и редактирования причины."""

    waiting_name = State()
    waiting_sort_order = State()

    editing_name = State()
    editing_sort_order = State()


class AdminCardStates(StatesGroup):
    """Состояния FSM редактирования карточки причины."""

    editing_description = State()
    editing_inspection = State()
    editing_recommendation = State()
    waiting_image = State()


class AdminNodeStates(StatesGroup):
    """Состояния FSM добавления и редактирования узла."""

    waiting_name = State()
    waiting_sort_order = State()

    editing_name = State()
    editing_sort_order = State()


class AdminToolStates(StatesGroup):
    """Состояния FSM добавления и редактирования инструмента."""

    waiting_name = State()
    waiting_description = State()
    waiting_sort_order = State()

    editing_name = State()
    editing_description = State()
    editing_sort_order = State()
