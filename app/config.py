from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    SECRET_KEY: str = "gV64m9aIzFG4qpgVphvQbPQrtAO0nM-7YwwOvu0XPt5KJOjAy4AfgLkqJXYEt"
    DEBUG: bool = True
    ALGORITHM: str = "HS256"
    COOKIE_NAME: str = "access_token"
    REFRESH_COOKIE_NAME: str = "refresh_token"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TG_TOKEN: str = "7106874206:AAGEbotJoabRmsngGgsxX-TwZ04MpoJiYQ0"

    DB_USER: str = "postgres"
    DB_PASSWORD: str = "12345678"
    DB_NAME: str = "cert"
    DATABASE_URL: str = "postgresql://postgres:12345678@localhost:5432/cert"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()