# diag_bot — Telegram-справочник диагноста

Референсный бот на **aiogram 3 + async SQLAlchemy 2**: справочник
неисправностей гидравлических систем и инструмента для диагностики.

## Возможности

- **Диагностика** — иерархия «система → проблема → причина»,
  карточка причины с текстом и изображениями (`answer_photo`).
- **Инструменты** — категории (системы типа `tool`), узлы, карточки
  инструментов, сводная карточка по нескольким выбранным узлам
  (FSM-выбор с чекбоксами).
- **Админка** (доступ по `ADMIN_IDS`, фильтр `IsAdmin` на уровне
  роутера) — CRUD систем диагностики: создание, редактирование
  (FSM), мягкое отключение/восстановление, окончательное удаление
  с каскадом зависимостей и подтверждением.

## Стек

| Слой | Технологии |
| --- | --- |
| Бот | aiogram 3, FSM (MemoryStorage) |
| БД | SQLite (aiosqlite), SQLAlchemy 2 async, Alembic |
| Конфиг | pydantic-settings (`BOT_TOKEN`, `ADMIN_IDS`, `DATABASE_URL`) |
| Качество | ruff (E/F/Q/D/N), mypy, pytest + pytest-asyncio |

## Структура

```
app/
├── bot/
│   ├── callbacks.py        # CallbackData-фабрики (MenuCB, DiagnosisCB, ToolsCB, AdminCB)
│   ├── filters.py          # IsAdmin — роутер-уровень админки
│   ├── helpers.py          # show / refresh / alert / unpack_id / get_*_or_alert
│   ├── keyboards/          # common (button, stack, with_nav) + модули клавиатур
│   ├── handlers/           # navigation, diagnosis, tools, admin
│   ├── middlewares/        # DatabaseMiddleware: сессия + commit/rollback
│   └── states/             # FSM-состояния
├── database/
│   ├── models/             # ORM-модели (System, Node, Problem, Cause, …)
│   ├── repositories/       # запросы; только flush — коммитит middleware
│   ├── session.py          # engine + PRAGMA foreign_keys=ON
│   └── seed*.py            # демо-данные
├── services/               # бизнес-логика и HTML-форматтеры (экранирование)
├── config.py               # pydantic-settings
└── main.py                 # long polling
migrations/                 # Alembic (autogenerate по app.database.models)
tests/test_smoke.py         # 17 смоук-тестов
```

## Запуск

```bash
uv sync
BOT_TOKEN=<токен> ADMIN_IDS=<id через запятую> uv run alembic upgrade head
BOT_TOKEN=<токен> ADMIN_IDS=<id> uv run python -m app.main
```

`DATABASE_URL` по умолчанию — `sqlite+aiosqlite:///./diagnostic_bot.db`.

## База данных и миграции

Файл SQLite создавать вручную не нужно — он появляется автоматически
при первом применении миграций (`alembic upgrade head`). Миграции
живут в `migrations/versions/`, `migrations/env.py` берёт схему из
`app.database.models`, а URL БД — из настройки `DATABASE_URL`.

**Первый запуск (создать базу и накатить схему):**

```bash
uv run alembic upgrade head
```

**Создать новую миграцию** (после изменения моделей в
`app/database/models/`):

```bash
# 1. Сгенерировать миграцию по разнице моделей и схемы БД
uv run alembic revision --autogenerate -m 'описание изменений'

# 2. Просмотреть сгенерированный файл в migrations/versions/

# 3. Проверить, что схемы моделей и БД согласованы
uv run alembic check

# 4. Накатить
uv run alembic upgrade head
```

> Для чистого autogenerate база должна быть актуальна
> (на последней ревизии): сначала `uv run alembic upgrade head`,
> затем `alembic revision --autogenerate`.

**Полезные команды:**

```bash
uv run alembic current      # текущая ревизия БД
uv run alembic history      # история миграций
uv run alembic downgrade -1 # откатить последнюю миграцию
```

**Демо-данные** (опционально, после применения миграций):

```bash
uv run python -m app.database.seed        # системы, проблемы, причины
uv run python -m app.database.seed_tools  # инструменты
```

## Проверки и текущее состояние

После полного ревью (P0/P1 исправлены) и DRY-рефакторинга:

- Дублирование хендлеров/клавиатур устранено: общие сцены и хелперы
  `show()/alert()/unpack_id()/get_*_or_alert()/numbered_names()`;
  «message is not modified» подавляется в `show()/refresh()`.
- Транзакции централизованы в `DatabaseMiddleware`; включены
  внешние ключи SQLite; `delete_system` использует каскад БД.
- Весь HTML из БД экранируется; N+1 устранены
  (`get_tool_nodes`/`get_active_nodes_by_ids`).
- Типизация: `ruff check .` — 0 замечаний, `mypy app` в
  **strict**-режиме — 0 ошибок (45 файлов).
- Тесты: `uv run pytest -q` — 17 passed (репозитории, каскадное
  удаление, CallbackData, хелперы, клавиатуры, форматтеры).
- Миграции: `alembic check` — расхождений моделей и схемы нет.

### Известные заглушки

- Раздел «Пользователи» в админке — экран-заглушка.
- Администрирование проблем/причин/карточек — пункты меню
  отвечают «в разработке» (callback-фабрики уже готовы).

