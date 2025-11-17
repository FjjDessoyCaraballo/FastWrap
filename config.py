from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    VANACIPRIME_API_KEY: str
    PORT: int
    HOST: str
    MODEL: str
    MODEL_KEY: str
    class Config:
        env_file = ".env"

settings = Settings()
