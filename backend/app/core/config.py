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

    # Task queue / Redis
    # Use 127.0.0.1 to avoid IPv6 localhost resolution issues on Windows
    REDIS_URL: str
    SYNC_LOCK_TTL_SECONDS: int

    # HTTP client settings for external calls (Aurinko)
    HTTP_CONNECT_TIMEOUT: float = 10.0
    HTTP_READ_TIMEOUT: float = 60.0
    HTTP_WRITE_TIMEOUT: float = 10.0
    HTTP_POOL_TIMEOUT: float = 60.0
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20

    # HTTP retry/backoff settings
    HTTP_RETRY_ATTEMPTS: int = 5
    HTTP_RETRY_BACKOFF_BASE: float = 0.5
    HTTP_RETRY_BACKOFF_CAP: float = 8.0
    HTTP_RETRY_JITTER: float = 0.2
    HTTP_RETRY_STATUS_CODES: list[int] = [429, 500, 502, 503, 504]

    # # Vector Database related
    # VECTOR_DB_PATH: str = "./vector_dbs"
    # EMBEDDING_MODEL: str = "text-embedding-3-large"
    # CHUNK_SIZE: int = 1000
    # CHUNK_OVERLAP: int = 200


settings = Settings()
