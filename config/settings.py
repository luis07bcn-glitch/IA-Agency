from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str = ""
    default_model: str = "claude-sonnet-4-6"

    # App
    log_level: str = "INFO"
    debug: bool = False

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"


settings = Settings()
