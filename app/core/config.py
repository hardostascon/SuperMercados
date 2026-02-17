from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Comparador de Precios de Supermercados"
    DEBUG: bool = False
    SCRAPY_USER_AGENT: str = "Mozilla/5.0"
    DOWNLOAD_DELAY: int = 2
    CONCURRENT_REQUESTS: int = 8
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    class Config:
        env_file_encoding = "utf-8"
        case_sensitive = True
        populate_by_name = True
    
    @classmethod
    def _get_env_file(cls):
        possible_locations = [
            ".env",
            "../.env",
            "../../.env",
            os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        ]
        for loc in possible_locations:
            path = Path(loc).resolve()
            if path.exists():
                return str(path)
        return ".env"
    
    @classmethod
    def from_env(cls, **overrides):
        env_file = cls._get_env_file()
        return cls(_env_file=env_file, **overrides)

settings = Settings.from_env()
