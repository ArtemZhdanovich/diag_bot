from aiogram.fsm.state import State, StatesGroup


class ToolsStates(StatesGroup):
    """Состояния навигации и выбора узлов инструментов."""

    selecting_nodes = State()
