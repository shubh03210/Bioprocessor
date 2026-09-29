from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "bbp-backend"
    environment: str = "development"
    api_prefix: str = "/api"

    # SQLite by default; switch DATABASE_URL for PostgreSQL later
    database_url: str = "sqlite:///./bbp.db"

    # Path to fermentation run CSVs (relative to repo root or absolute)
    data_kit_path: str = "../data_kit"

    # Control-loop defaults (used in later phases)
    replay_process_minutes_per_wall_second: float = 1.0
    feed_rate_min: float = 0.0
    feed_rate_max: float = 30.0
    actuator_lag_process_minutes: float = 5.0
    controller_dwell_process_minutes: float = 5.0
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()
