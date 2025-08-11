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
    DEBUG: bool

    # aurinko related
    AURINKO_CLIENT_ID: str
    AURINKO_CLIENT_SECRET: str
    AURINKO_BASE_URL: str
    AURINKO_SYNC_DAYS_WITHIN: int

    # application urls
    FRONTEND_URL: str
    BACKEND_URL: str

    # database related
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int
    DATABASE_POOL_TIMEOUT: int
    DATABASE_MAX_OVERFLOW: int

    # security related
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # OpenAI/AI related
    OPENAI_API_KEY: str
    OPENAI_MODEL: str

    # # Vector Database related
    # VECTOR_DB_PATH: str = "./vector_dbs"
    # EMBEDDING_MODEL: str = "text-embedding-3-large"
    # CHUNK_SIZE: int = 1000
    # CHUNK_OVERLAP: int = 200


settings = Settings()
