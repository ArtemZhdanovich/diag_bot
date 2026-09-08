from sqlalchemy import select

from app.database.models.node import Node
from app.database.models.system import System
from app.database.models.tool import Tool
from app.database.session import async_session_factory


async def seed_tools() -> None:
    """Наполняет базу справочником инструментов."""
    async with async_session_factory() as session:
        existing = await session.scalar(
            select(System.id)
            .where(
                System.type == 'tool',
                System.name == 'Гидросистема погрузочного оборудования',
            )
        )

        if existing is not None:
            print('Тестовые данные инструментов уже существуют.')
            return

        # ---------------------------------------------------------
        # 1. Категории инструментов
        # ---------------------------------------------------------

        loading = System(
            name='Гидросистема погрузочного оборудования',
            type='tool',
            sort_order=1,
        )

        steering = System(
            name='Гидросистема рулевого управления',
            type='tool',
            sort_order=2,
        )

        brakes = System(
            name='Гидросистема тормозов',
            type='tool',
            sort_order=3,
        )

        session.add_all([
            loading,
            steering,
            brakes,
        ])

        await session.flush()

        # ---------------------------------------------------------
        # 2. Инструменты
        # ---------------------------------------------------------

        pressure_gauge = Tool(
            name='Манометр',
            description='Для проверки давления в гидросистеме.',
            sort_order=1,
        )

        multimeter = Tool(
            name='Мультиметр',
            description='Для проверки электрических цепей и датчиков.',
            sort_order=2,
        )

        wrench_set = Tool(
            name='Набор гаечных ключей',
            description='Для демонтажа и монтажа гидравлических компонентов.',
            sort_order=3,
        )

        diagnostic_kit = Tool(
            name='Комплект для диагностики гидросистемы',
            description='Комплект измерительных приборов и переходников.',
            sort_order=4,
        )

        session.add_all([
            pressure_gauge,
            multimeter,
            wrench_set,
            diagnostic_kit,
        ])

        await session.flush()

        # ---------------------------------------------------------
        # 3. Узлы
        # ---------------------------------------------------------

        loading_pump = Node(
            system_id=loading.id,
            name='Гидравлический насос',
            sort_order=1,
        )

        loading_filter = Node(
            system_id=loading.id,
            name='Гидравлический фильтр',
            sort_order=2,
        )

        steering_pump = Node(
            system_id=steering.id,
            name='Насос рулевого управления',
            sort_order=1,
        )

        brake_unit = Node(
            system_id=brakes.id,
            name='Тормозной гидроузел',
            sort_order=1,
        )

        # Важно:
        # связи Node -> Tool задаём непосредственно через relationship.
        # Никакого чтения loading_pump.tools здесь не происходит.

        loading_pump.tools = [
            pressure_gauge,
            wrench_set,
            diagnostic_kit,
        ]

        loading_filter.tools = [
            pressure_gauge,
            wrench_set,
        ]

        steering_pump.tools = [
            pressure_gauge,
            multimeter,
            wrench_set,
        ]

        brake_unit.tools = [
            pressure_gauge,
            multimeter,
            diagnostic_kit,
        ]

        session.add_all([
            loading_pump,
            loading_filter,
            steering_pump,
            brake_unit,
        ])

        # ---------------------------------------------------------
        # 4. Сохраняем всё одной транзакцией
        # ---------------------------------------------------------

        await session.commit()

        print('Тестовые данные инструментов успешно добавлены.')


if __name__ == '__main__':
    import asyncio

    asyncio.run(seed_tools())