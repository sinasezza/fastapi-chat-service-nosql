from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    debug: bool = Field(default=False)
    database_url: str = "mongodb://localhost:27017"
    database_name: str = "chat_app"
    jwt_secret_key: str = "your-secret-key"
    jwt_algorithm: str = Field(default="HS256")

    # CORS settings
    cors_allow_origins: list[str] = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


UPLOAD_DIR = BASE_DIR / "uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
