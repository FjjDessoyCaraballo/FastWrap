from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    vanaciprime_api_key: str
    port: int

    class Config:
        env_file = ".env"

settings = Settings()
