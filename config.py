from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict

class Settings(BaseSettings):
    FASTWRAP_API_KEY: str = 1234
    REDIS_API_KEY: str
    REDIS_USER: str = "User123"
    REDIS_USER_PW: str
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    PORT: int = 8555
    HOST: str = "0.0.0.0"
    MODEL: str = "gpt-4o-mini"
    MODEL_KEY: str
    MODEL_PROVIDER: str | None = None
    LANGCHAIN_API_KEY: str | None = None
    LANGSMITH_TRACING_V2: bool = True
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "fastwrap_db"
    POSTGRES_USER: str
    POSTGRES_PW: str 
    DATABASE_URL: str
    EMBEDDING_MODEL: str = 'text-embedding-3-small'
    EMBEDDING_DIM: int = 1536
    model_config = ConfigDict(env_file=".env")

settings = Settings()
