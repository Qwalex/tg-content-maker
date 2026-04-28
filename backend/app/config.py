from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/tg_content_maker"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = "google/gemini-3.1-flash-lite-preview"
    alert_webhook_url: str = "https://notify.qwalex.one/"
    telegram_api_id: str = ""
    telegram_api_hash: str = ""
    telegram_session_string: str = ""
    redis_url: str = "redis://localhost:6379/0"
    max_publish_retries: int = 5
    max_openrouter_retries: int = 3
    edit_window_minutes: int = 10
    internal_ingest_token: str = ""
    auto_create_schema: bool = False
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
