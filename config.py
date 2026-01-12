from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict

class Settings(BaseSettings):
    FASTWRAP_API_KEY: str
    REDIS_API_KEY: str
    REDIS_USER: str
    REDIS_USER_PW: str
    REDIS_HOST: str
    REDIS_PORT: int
    PORT: int
    HOST: str
    MODEL: str
    MODEL_KEY: str
    MODEL_PROVIDER: str | None = None
    LANGCHAIN_API_KEY: str | None = None
    LANGSMITH_TRACING_V2: bool = True
    model_config = ConfigDict(env_file=".env")

settings = Settings()
