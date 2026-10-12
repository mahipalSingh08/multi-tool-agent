from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    web_search_api_key: str = ""
    weather_api_key: str = ""
    frontend_origin: str = "http://localhost:4200"
    port: int = 8000

    @property
    def is_openai_configured(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def is_web_search_configured(self) -> bool:
        return bool(self.web_search_api_key.strip())

    @property
    def is_weather_configured(self) -> bool:
        return bool(self.weather_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
