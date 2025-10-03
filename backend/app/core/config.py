import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('ENV', 'local')}",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    database_url: str
    log_level: str = "info"
    log_file_path: str = "logs/app/app.log"

    openai_secret_key: str
    vector_store_data_dir: str = "data/index"

    root_path: str = ""
    openapi_url: str = ""
    docs_url: str = ""
    redoc_url: str = ""

    # Database connection pool settings (PostgreSQL optimized)
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    db_pool_pre_ping: bool = True


settings = Settings()
