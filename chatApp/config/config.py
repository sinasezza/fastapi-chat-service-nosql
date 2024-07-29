from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    debug: bool = Field(default=False)

    # database settings
    database_url: str = Field(default="mongodb://localhost:27017")
    database_name: str = Field(default="chat_app")
    max_pool_size: int = 10
    min_pool_size: int = 1

    # jwt settings
    jwt_secret_key: SecretStr = Field(default="your-secret-key")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=1440)

    # CORS settings
    cors_allow_origins: list[str] = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])

    # Trusted hosts settings
    trusted_hosts: list[str] = Field(default=["127.0.0.1", "localhost"])

    # logs settings
    log_level: str = Field(default="INFO")
    log_file_path: Path = Field(default=BASE_DIR / "logs/app.log")
    log_max_bytes: int = Field(default=1048576)  # 1 MB
    log_backup_count: int = Field(default=3)

    # upload settings
    upload_dir: Path = Field(default=BASE_DIR / "uploads")
    max_upload_size: int = Field(default=(5 * 1024 * 1024))

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
