import pathlib

from dotenv import load_dotenv
from pydantic import BaseSettings

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "chat_app"
    jwt_secret_key: str = "your-secret-key"  # Change this to a secure random string
    jwt_algorithm: str = "HS256"


settings = Settings()
