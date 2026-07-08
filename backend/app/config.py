"""Application settings loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: str = "development"
    secret_key: str = "change-me-to-a-long-random-string"

    # Database (async driver — used by SQLAlchemy)
    database_url: str = (
        "postgresql+asyncpg://ethara:ethara_password@localhost:5432/ethara_db"
    )

    # Database (sync driver — used by Alembic)
    sync_database_url: str = (
        "postgresql+psycopg2://ethara:ethara_password@localhost:5432/ethara_db"
    )

    # CORS
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


settings = Settings()
