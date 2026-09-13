"""Общие фикстуры и настройки pytest.

Добавляет корень проекта в sys.path, чтобы тесты видели пакет `app`
даже без настройки pythonpath в конфиге pytest.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))