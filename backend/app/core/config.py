from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Vibration Game Backend"
    API_V1_STR: str = "/api/v1"
    
    # Example: Database configuration
    # SQLALCHEMY_DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

    # Example: Redis configuration
    # REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    # REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
