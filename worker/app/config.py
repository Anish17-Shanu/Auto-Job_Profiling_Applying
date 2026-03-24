from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    internal_api_key: str = Field(default="change-this-internal-key", alias="INTERNAL_API_KEY")
    worker_poll_seconds: int = Field(default=3, alias="WORKER_POLL_SECONDS")


settings = WorkerSettings()

