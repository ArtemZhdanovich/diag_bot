import asyncio

from sqlalchemy import select

from app.database.models.cause import Cause
from app.database.models.cause_card import CauseCard
from app.database.models.problem import Problem
from app.database.models.system import System
from app.database.session import async_session_factory


async def seed() -> None:
    """Наполняет базу демонстрационными данными диагностики."""
    async with async_session_factory() as session:
        # Проверяем, есть ли уже данные
        existing_system = await session.scalar(
            select(System).where(
                System.name == 'Гидросистема рабочего оборудования'
            )
        )

        if existing_system is not None:
            print('Тестовые данные уже существуют.')
            return

        # ---------------------------------------------------------
        # Система
        # ---------------------------------------------------------

        system = System(
            name='Гидросистема рабочего оборудования',
            type='diagnosis',
            sort_order=1,
            is_active=True,
        )

        session.add(system)
        await session.flush()

        # ---------------------------------------------------------
        # Проблема №1
        # ---------------------------------------------------------

        problem_1 = Problem(
            system_id=system.id,
            name='Рабочее оборудование не поднимается',
            sort_order=1,
            is_active=True,
        )

        session.add(problem_1)
        await session.flush()

        cause_1 = Cause(
            problem_id=problem_1.id,
            name='Низкий уровень рабочей жидкости',
            sort_order=1,
            is_active=True,
        )

        cause_2 = Cause(
            problem_id=problem_1.id,
            name='Неисправен гидравлический насос',
            sort_order=2,
            is_active=True,
        )

        cause_3 = Cause(
            problem_id=problem_1.id,
            name='Засорён гидравлический фильтр',
            sort_order=3,
            is_active=True,
        )

        session.add_all([cause_1, cause_2, cause_3])
        await session.flush()

        # ---------------------------------------------------------
        # Карточки причин
        # ---------------------------------------------------------

        card_1 = CauseCard(
            cause_id=cause_1.id,
            description=(
                'Недостаточный уровень рабочей жидкости '
                'может привести к падению давления в гидросистеме.'
            ),
            inspection=(
                'Проверить уровень рабочей жидкости в баке '
                'согласно инструкции по эксплуатации.'
            ),
            recommendation=(
                'При необходимости долить рабочую жидкость '
                'соответствующего типа до требуемого уровня.'
            ),
        )

        card_2 = CauseCard(
            cause_id=cause_2.id,
            description=(
                'При неисправности гидравлического насоса '
                'система не создаёт необходимое рабочее давление.'
            ),
            inspection=(
                'Проверить давление на выходе насоса '
                'и состояние привода насоса.'
            ),
            recommendation=(
                'При подтверждении неисправности выполнить '
                'ремонт или заменить гидравлический насос.'
            ),
        )

        card_3 = CauseCard(
            cause_id=cause_3.id,
            description=(
                'Загрязнённый фильтр ограничивает поток рабочей '
                'жидкости и может привести к снижению давления.'
            ),
            inspection=(
                'Проверить состояние фильтрующего элемента '
                'и наличие загрязнения.'
            ),
            recommendation=(
                'Очистить или заменить фильтрующий элемент '
                'в соответствии с регламентом обслуживания.'
            ),
        )

        session.add_all([card_1, card_2, card_3])

        # ---------------------------------------------------------
        # Проблема №2
        # ---------------------------------------------------------

        problem_2 = Problem(
            system_id=system.id,
            name='Рабочее оборудование работает медленно',
            sort_order=2,
            is_active=True,
        )

        session.add(problem_2)
        await session.flush()

        cause_4 = Cause(
            problem_id=problem_2.id,
            name='Недостаточная производительность насоса',
            sort_order=1,
            is_active=True,
        )

        cause_5 = Cause(
            problem_id=problem_2.id,
            name='Засорение фильтра',
            sort_order=2,
            is_active=True,
        )

        session.add_all([cause_4, cause_5])
        await session.flush()

        card_4 = CauseCard(
            cause_id=cause_4.id,
            description=(
                'Снижение производительности насоса приводит '
                'к уменьшению расхода рабочей жидкости.'
            ),
            inspection=(
                'Проверить фактическую производительность насоса '
                'и рабочее давление системы.'
            ),
            recommendation=(
                'Проверить состояние насоса и при необходимости '
                'выполнить его ремонт или замену.'
            ),
        )

        card_5 = CauseCard(
            cause_id=cause_5.id,
            description=(
                'Засорённый фильтр ограничивает поток жидкости '
                'и снижает скорость работы исполнительных механизмов.'
            ),
            inspection=(
                'Проверить фильтр на наличие загрязнения '
                'и перепад давления.'
            ),
            recommendation=(
                'Заменить или очистить фильтрующий элемент.'
            ),
        )

        session.add_all([card_4, card_5])

        await session.commit()

        print('Тестовые данные успешно добавлены.')


if __name__ == '__main__':
    asyncio.run(seed())