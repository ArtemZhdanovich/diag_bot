from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""

    bot_token: str
    admin_ids: str
    database_url: str = 'sqlite+aiosqlite:///./diagnostic_bot.db'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @property
    def admin_id_list(self) -> list[int]:
        """Список id администраторов из строки ADMIN_IDS."""
        return [
            int(admin_id.strip())
            for admin_id in self.admin_ids.split(',')
            if admin_id.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    # Обязательные поля приходят из окружения / .env, поэтому
    # конструктор без аргументов для mypy — подавляемое замечание.
    """Возвращает кешированные настройки приложения."""
    return Settings()  # type: ignore[call-arg]
