from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Auto-Job Profiling Applying API", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    secret_key: str = Field(default="change-this-secret-key", alias="SECRET_KEY")
    internal_api_key: str = Field(default="change-this-internal-key", alias="INTERNAL_API_KEY")
    access_token_expire_minutes: int = Field(default=720, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    database_url: str = Field(default="sqlite:///./autojob.db", alias="DATABASE_URL")
    cors_origins_raw: str = Field(default="http://localhost:5173,http://localhost:8080", alias="CORS_ORIGINS")
    demo_admin_email: str = Field(default="admin@autojobdemo.com", alias="DEMO_ADMIN_EMAIL")
    demo_admin_password: str = Field(default="ChangeMe123!", alias="DEMO_ADMIN_PASSWORD")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
