from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="forbid",
        validate_assignment=True,
        case_sensitive=False
    )
    # system level config
    DEBUG: bool = False

    # aurinko related
    AURINKO_CLIENT_ID: str
    AURINKO_CLIENT_SECRET: str
    AURINKO_BASE_URL: str
    AURINKO_SYNC_DAYS_WITHIN: int = 3

    # application urls
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # database related
    DATABASE_URL: str = 'postgresql://neondb_owner:npg_04KthxyolXZd@ep-aged-mode-a5db6d24-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require'
    DATABASE_POOL_SIZE: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_MAX_OVERFLOW: int = 20

    # security related
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1

    # OpenAI/AI related
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"


settings = Settings()
