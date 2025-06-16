from pydantic import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore"
    )
    # system level config
    DEBUG : bool = False
    
    # aurinko related
    AURINKO_CLIENT_ID : str
    AURINKO_CLIENT_SECRET : str
    AURINKO_BASE_URL: str

    # application urls
    FRONTEND_URL : str = "http://localhost:3000"
    BACKEND_URL : str = "http://localhost:8000"

    # database related

settings = Settings()
