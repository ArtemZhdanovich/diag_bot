"""Смоук-тесты ключевых изменений после ревью.

Запуск: uv run pytest
"""

import os


os.environ.setdefault("BOT_TOKEN", "123:test")
os.environ.setdefault("ADMIN_IDS", "1")

from types import SimpleNamespace

import pytest
import pytest_asyncio

from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Импорт session включает PRAGMA foreign_keys=ON для всех движков
# (важно для теста каскадного удаления).
import app.database.models
import app.database.session  # noqa: F401

from app.bot.callbacks import AdminCB, DiagnosisCB, MenuCB, ToolsCB
from app.bot.filters import IsAdmin
from app.bot.helpers import SYSTEM_NOT_FOUND, show, unpack_id
from app.bot.keyboards.common import MENU_BUTTON_TEXT, button, stack, with_nav
from app.database.base import Base
from app.database.models.cause import Cause
from app.database.models.cause_card import CauseCard
from app.database.models.cause_image import CauseImage
from app.database.models.node import Node
from app.database.models.problem import Problem
from app.database.models.system import System
from app.database.models.tool import Tool
from app.database.repositories.node import (
    get_active_nodes_by_ids,
    get_tool_nodes,
)
from app.database.repositories.system import (
    create_system,
    deactivate_system,
    delete_system,
    get_inactive_systems,
    get_systems,
    restore_system,
    update_system,
)
from app.services.admin import is_admin
from app.services.formatting import numbered_names
from app.services.tools import format_tools_card, get_tools_for_nodes


pytestmark = pytest.mark.asyncio



@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    await engine.dispose()


async def test_create_system_fills_id_on_flush_without_commit(
    session_factory,
):
    """Репозиторий делает только flush: до коммита данные не видны извне."""
    async with session_factory() as session:
        system = await create_system(
            session,
            name="Тест",
            system_type="diagnosis",
            sort_order=1,
        )

        assert system.id is not None

    async with session_factory() as other_session:
        # Без коммита (его делает middleware) записи быть не должно.
        assert await get_systems(other_session, "diagnosis") == []


async def test_system_lifecycle(session_factory):
    async with session_factory() as session:
        system = await create_system(session, "S", "diagnosis", 1)

        await deactivate_system(session, system)
        assert (await get_systems(session, "diagnosis")) == []
        assert len(await get_inactive_systems(session, "diagnosis")) == 1

        restored = await restore_system(session, system)
        assert restored.is_active is True

        updated = await update_system(session, system, "S2", 5)
        assert updated.name == "S2"
        assert updated.sort_order == 5

        await delete_system(session, system)
        assert await get_systems(session, "diagnosis") == []


async def test_delete_system_cascades_related_data(session_factory):
    async with session_factory() as session:
        system = await create_system(session, "S", "diagnosis", 1)

        problem = Problem(system_id=system.id, name="P", sort_order=1)
        session.add(problem)
        await session.flush()

        cause = Cause(problem_id=problem.id, name="C", sort_order=1)
        session.add(cause)
        await session.flush()

        card = CauseCard(cause_id=cause.id, description="D")
        session.add(card)
        await session.flush()

        session.add(CauseImage(card_id=card.id, telegram_file_id="f"))

        tool = Tool(name="T", sort_order=1)
        session.add(tool)
        await session.flush()

        session.add(
            Node(system_id=system.id, name="N", sort_order=1, tools=[tool])
        )
        await session.flush()

        await delete_system(session, system)

        for model in (Problem, Cause, CauseCard, CauseImage, Node):
            remaining = (await session.scalars(select(model))).all()
            assert remaining == [], f"не удалены {model.__name__}"


async def test_get_tools_for_nodes_aggregates_and_deduplicates(
    session_factory,
):
    async with session_factory() as session:
        system = System(name="L", type="tool", sort_order=1)
        session.add(system)
        await session.flush()

        pressure = Tool(name="Манометр", sort_order=1)
        wrench = Tool(name="Ключи", sort_order=2)
        session.add_all([pressure, wrench])
        await session.flush()

        node_1 = Node(system_id=system.id, name="N1", sort_order=1)
        node_2 = Node(system_id=system.id, name="N2", sort_order=2)
        node_1.tools = [pressure, wrench]
        node_2.tools = [pressure]  # пересечение — дедуп по id
        session.add_all([node_1, node_2])
        await session.flush()

        tools = await get_tools_for_nodes(
            session,
            [node_1.id, node_2.id],
        )

        assert [tool.name for tool in tools] == ["Манометр", "Ключи"]

        # Неактивный узел не учитывается.
        node_1.is_active = False
        await session.flush()

        assert await get_tools_for_nodes(session, [node_1.id]) == []


async def test_get_tool_nodes_only_tool_systems(session_factory):
    async with session_factory() as session:
        tool_system = System(name="L", type="tool", sort_order=1)
        diag_system = System(name="D", type="diagnosis", sort_order=1)
        session.add_all([tool_system, diag_system])
        await session.flush()

        session.add_all([
            Node(system_id=tool_system.id, name="NT", sort_order=1),
            Node(system_id=diag_system.id, name="ND", sort_order=1),
        ])
        await session.flush()

        nodes = await get_tool_nodes(session)
        assert [node.name for node in nodes] == ["NT"]

        by_ids = await get_active_nodes_by_ids(
            session,
            [node.id for node in nodes],
        )
        assert len(by_ids) == 1

        # Пустой список не должен ронять запрос.
        assert await get_active_nodes_by_ids(session, []) == []


async def test_callback_data_pack_unpack_roundtrip():
    assert MenuCB(action="main").pack() == "menu:main"
    assert MenuCB.unpack("menu:diagnosis") == MenuCB(action="diagnosis")

    diagnosis = DiagnosisCB(action="system", id=3)
    assert DiagnosisCB.unpack(diagnosis.pack()) == diagnosis

    tools = ToolsCB(action="back_nodes", id=7)
    assert ToolsCB.unpack(tools.pack()) == tools

    admin = AdminCB(action="system_delete_confirm", id=42)
    assert AdminCB.unpack(admin.pack()) == admin


async def test_is_admin_reads_env_list():
    assert is_admin(1) is True
    assert is_admin(2) is False


async def test_is_admin_filter_rejects_missing_user():
    event = type("FakeEvent", (), {"from_user": None})()

    assert await IsAdmin()(event) is False

    event.from_user = type("FakeUser", (), {"id": 1})()
    assert await IsAdmin()(event) is True


async def test_format_tools_card_escapes_html():
    tool = Tool(
        id=1,
        name="Ключ <b>специальный</b>",
        description="для гаек & болтов",
        sort_order=1,
    )

    text = format_tools_card("Титул <i>x</i>", [tool])

    assert "Ключ &lt;b&gt;специальный&lt;/b&gt;" in text
    assert "гаек &amp; болтов" in text
    assert "Титул &lt;i&gt;x&lt;/i&gt;" in text
    # Сырой HTML в результат не попадает.
    assert "<b>специальный" not in text


class FakeMessage:
    def __init__(self, error=None):
        self.calls = []
        self._error = error

    async def edit_text(self, text, reply_markup=None):
        self.calls.append((text, reply_markup))

        if self._error is not None:
            raise self._error


class FakeCallback:
    def __init__(self, message, data=""):
        self.message = message
        self.data = data
        self.answers = []

    async def answer(self, text=None, show_alert=False):
        self.answers.append((text, show_alert))


def _not_modified_error():
    return TelegramBadRequest(
        method=object(),
        message="Bad Request: message is not modified",
    )


async def test_show_suppresses_not_modified():
    callback = FakeCallback(FakeMessage(error=_not_modified_error()))

    await show(callback, "Текст")

    assert callback.answers == [(None, False)]


async def test_show_raises_other_errors():
    error = TelegramBadRequest(
        method=object(),
        message="Bad Request: chat not found",
    )
    callback = FakeCallback(FakeMessage(error=error))

    with pytest.raises(TelegramBadRequest):
        await show(callback, "Текст")


async def test_show_answers_callback_with_text():
    callback = FakeCallback(FakeMessage())

    await show(callback, "Текст", answer_text="Готово")

    assert callback.answers == [("Готово", False)]


async def test_unpack_id_reads_id_from_callback_data():
    callback = FakeCallback(
        None,
        data=AdminCB(action="system", id=7).pack(),
    )
    assert unpack_id(callback, AdminCB) == 7

    callback_without_id = FakeCallback(
        None,
        data=AdminCB(action="system_add").pack(),
    )
    assert unpack_id(callback_without_id, AdminCB) is None


async def test_numbered_names_escapes_html():
    items = [
        SimpleNamespace(name="<b>Раз</b>"),
        SimpleNamespace(name="Два & три"),
    ]

    assert numbered_names(items) == [
        "1. &lt;b&gt;Раз&lt;/b&gt;",
        "2. Два &amp; три",
    ]
    assert numbered_names([]) == []


async def test_with_nav_appends_back_and_menu_rows():
    rows = with_nav(stack(button("A", "a")))
    assert [[item.text for item in row] for row in rows] == [
        ["A"],
        [MENU_BUTTON_TEXT],
    ]

    rows_with_back = with_nav(
        stack(button("A", "a")),
        back=button("⬅️ Назад", "back"),
    )
    assert [[item.text for item in row] for row in rows_with_back] == [
        ["A"],
        ["⬅️ Назад"],
        [MENU_BUTTON_TEXT],
    ]


async def test_stack_puts_each_button_in_its_own_row():
    rows = stack(button("A", "a"), button("B", "b"))

    assert [row[0].callback_data for row in rows] == ["a", "b"]


async def test_system_not_found_constant_is_used_by_helpers():
    assert SYSTEM_NOT_FOUND == "Система не найдена."


async def test_get_or_create_user_creates_and_updates(session_factory):
    from app.database.repositories.user import (
        count_users,
        get_or_create_user,
        get_users,
    )

    async with session_factory() as session:
        user = await get_or_create_user(
            session, telegram_id=100, username="a", first_name="A"
        )
        await session.commit()

        assert user.id is not None
        assert await count_users(session) == 1

        # Повторный вызов обновляет профиль, а не создаёт дубль.
        updated = await get_or_create_user(
            session, telegram_id=100, username="b", first_name="B"
        )
        await session.commit()

        assert updated.id == user.id
        assert updated.username == "b"
        assert await count_users(session) == 1
        assert len(await get_users(session)) == 1


async def test_problem_lifecycle(session_factory):
    from app.database.repositories.problem import (
        create_problem,
        deactivate_problem,
        delete_problem,
        get_inactive_problems,
        get_problem,
        get_problems,
        restore_problem,
        update_problem,
    )

    async with session_factory() as session:
        system = System(name="S", type="diagnosis", sort_order=1)
        session.add(system)
        await session.flush()

        problem = await create_problem(session, system.id, "P", 1)
        await session.commit()

        names = [p.name for p in await get_problems(session, system.id)]
        assert names == ["P"]

        await deactivate_problem(session, problem)
        await session.commit()
        assert await get_problems(session, system.id) == []
        assert len(await get_inactive_problems(session, system.id)) == 1

        await restore_problem(session, problem)
        await session.commit()
        assert problem.is_active is True

        updated = await update_problem(session, problem, "P2", 5)
        await session.commit()
        assert updated.name == "P2"
        assert updated.sort_order == 5

        await delete_problem(session, updated)
        await session.commit()
        assert await get_problem(session, updated.id) is None


async def test_cause_lifecycle(session_factory):
    from app.database.repositories.cause import (
        create_cause,
        deactivate_cause,
        delete_cause,
        get_cause,
        get_causes,
        get_inactive_causes,
        restore_cause,
        update_cause,
    )

    async with session_factory() as session:
        system = System(name="S", type="diagnosis", sort_order=1)
        session.add(system)
        await session.flush()

        problem = Problem(system_id=system.id, name="P", sort_order=1)
        session.add(problem)
        await session.flush()

        cause = await create_cause(session, problem.id, "C", 1)
        await session.commit()

        names = [c.name for c in await get_causes(session, problem.id)]
        assert names == ["C"]

        await deactivate_cause(session, cause)
        await session.commit()
        assert await get_causes(session, problem.id) == []
        assert len(await get_inactive_causes(session, problem.id)) == 1

        await restore_cause(session, cause)
        await session.commit()
        assert cause.is_active is True

        updated = await update_cause(session, cause, "C2", 3)
        await session.commit()
        assert updated.name == "C2"

        await delete_cause(session, updated)
        await session.commit()
        assert await get_cause(session, updated.id) is None


async def test_card_create_update_and_add_image(session_factory):
    from app.database.repositories.cause_card import (
        add_image,
        create_card,
        get_card_by_cause,
        update_card,
    )

    async with session_factory() as session:
        system = System(name="S", type="diagnosis", sort_order=1)
        session.add(system)
        await session.flush()

        problem = Problem(system_id=system.id, name="P", sort_order=1)
        session.add(problem)
        await session.flush()

        cause = Cause(problem_id=problem.id, name="C", sort_order=1)
        session.add(cause)
        await session.flush()

        card = await create_card(session, cause.id, description="D")
        await session.commit()

        found = await get_card_by_cause(session, cause.id)
        assert found is not None
        assert found.description == "D"
        assert found.images == []

        await add_image(session, card.id, telegram_file_id="f1", sort_order=0)
        await session.commit()

        # expire_on_commit=False: сбрасываем кэш отношений.
        session.expire(found)
        found = await get_card_by_cause(session, cause.id)
        assert len(found.images) == 1
        assert found.images[0].telegram_file_id == "f1"

        await update_card(
            session,
            found,
            description="D2",
            inspection="I",
            recommendation="R",
        )
        await session.commit()

        session.expire(found)
        found = await get_card_by_cause(session, cause.id)
        assert found.description == "D2"
        assert found.inspection == "I"
        assert found.recommendation == "R"


async def test_tool_and_node_lifecycle(session_factory):
    from app.database.repositories.node import (
        create_node,
        deactivate_node,
        delete_node,
        get_inactive_nodes,
        get_nodes,
        restore_node,
        update_node,
    )
    from app.database.repositories.tool import (
        create_tool,
        deactivate_tool,
        delete_tool,
        get_inactive_tools,
        get_tools,
        restore_tool,
        update_tool,
    )

    async with session_factory() as session:
        system = System(name="L", type="tool", sort_order=1)
        session.add(system)
        await session.flush()

        tool = await create_tool(session, "T", description="D", sort_order=1)
        node = await create_node(session, system.id, "N", 1)
        await session.commit()

        assert [t.name for t in await get_tools(session)] == ["T"]
        assert [n.name for n in await get_nodes(session, system.id)] == ["N"]

        await deactivate_tool(session, tool)
        await deactivate_node(session, node)
        await session.commit()
        assert await get_tools(session) == []
        assert await get_nodes(session, system.id) == []
        assert len(await get_inactive_tools(session)) == 1
        assert len(await get_inactive_nodes(session, system.id)) == 1

        await restore_tool(session, tool)
        await restore_node(session, node)
        await session.commit()
        assert tool.is_active is True
        assert node.is_active is True

        await update_tool(session, tool, "T2", None, 2)
        await update_node(session, node, "N2", 2)
        await session.commit()
        assert tool.name == "T2"
        assert tool.description is None
        assert node.name == "N2"

        await delete_node(session, node)
        await delete_tool(session, tool)
        await session.commit()
        assert await get_tools(session) == []
        assert await get_nodes(session, system.id) == []


async def test_get_system_by_slug(session_factory):
    from app.database.repositories.system import get_system_by_slug

    async with session_factory() as session:
        active = System(
            name="Активная", type="tool", slug="loading", sort_order=1
        )
        inactive = System(
            name="Отключённая",
            type="tool",
            slug="brakes",
            is_active=False,
        )
        session.add_all([active, inactive])
        await session.commit()

        assert (await get_system_by_slug(session, "loading")) is not None
        assert (await get_system_by_slug(session, "brakes")) is None
        assert (await get_system_by_slug(session, "missing")) is None
