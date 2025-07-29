import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))


class Settings(BaseSettings):
    db_url: str
    db_host: str
    db_port: str
    db_test_url: str
    secret_key: str
    pythonpath: str | None = None
    postgres_db: str | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "forbid"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings
