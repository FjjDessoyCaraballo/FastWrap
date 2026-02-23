from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict

class Settings(BaseSettings):
    FASTWRAP_API_KEY: str = "1234"
    API_LIMIT: int = 100
    API_WINDOW: int = 10
    API_WINDOW_EXPIRE: int = 10
    REDIS_USER: str = "default"
    REDIS_USER_PW: str = "dummy"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    PORT: int = 8555
    HOST: str = "0.0.0.0"
    MODEL: str = "gpt-4o-mini"
    MODEL_KEY: str | None = None
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
    VECTOR_CHAT_STORE_ENABLED: bool = True
    VECTOR_CHAT_MEMORY_ENABLED: bool = True
    VECTOR_CHAT_ENTITY_TYPE: str = "chat"
    VECTOR_CHAT_MEMORY_TOP_K_CHAT: int = 4
    VECTOR_CHAT_MEMORY_TOP_K_KB: int = 4
    VECTOR_CHAT_MEMORY_MAX_CHARS: int = 2400
    model_config = ConfigDict(env_file=".env")

settings = Settings()
