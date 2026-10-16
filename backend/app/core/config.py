from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./cnizos.db"
    SYNC_DATABASE_URL: str = "sqlite:///./cnizos.db"
    JWT_SECRET: str = "dev_secret_change_me_please_32_chars_min"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TTL: int = 900  # 15 min
    JWT_REFRESH_TTL: int = 2592000  # 30d
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    APP_NAME: str = "CnizOS"
    COOKIE_SECURE: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

@lru_cache
def get_settings() -> Settings:
    return Settings()
