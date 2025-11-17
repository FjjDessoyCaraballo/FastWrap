from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    VANACIPRIME_API_KEY: str
    PORT: int
    HOST: str
    MODEL: str
    MODEL_KEY: str
    MODEL_PROVIDER: str | None = None
    class Config:
        env_file = ".env"

settings = Settings()
