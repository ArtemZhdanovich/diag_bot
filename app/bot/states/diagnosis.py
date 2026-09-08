from aiogram.fsm.state import State, StatesGroup


class DiagnosisStates(StatesGroup):
    """Состояния навигации по разделу диагностики."""

    system = State()
    problem = State()
    cause = State()
