from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://app:app@localhost:5432/app"
    frontend_origin: str = "http://localhost:5173"
    # Built frontend served by the API in production. Skipped when the folder does not exist.
    static_dir: str = "static"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, v: str) -> str:
        # Hosts such as Fly.io give postgres:// or postgresql:// URLs. SQLAlchemy needs the driver name.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix) :]
        return v


settings = Settings()
