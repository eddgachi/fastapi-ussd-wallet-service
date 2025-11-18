from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg2://fastapi_user:fastapi_password@db/umoja_loans"
    )

    # Redis & Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # M-Pesa Daraja API (for future integration)
    MPESA_CONSUMER_KEY: Optional[str] = None
    MPESA_CONSUMER_SECRET: Optional[str] = None
    MPESA_SHORTCODE: Optional[str] = None

    # Africa's Talking USSD/SMS (for future integration)
    AT_API_KEY: Optional[str] = None
    AT_USERNAME: Optional[str] = None

    # Environment
    ENV: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
