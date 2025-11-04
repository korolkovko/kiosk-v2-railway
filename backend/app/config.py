from functools import lru_cache
from typing import List, Union
from pathlib import Path
import os
import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Загружаем переменные из .env конкретно для backend-приложения
# По умолчанию используем backend/.env; путь можно переопределить через BACKEND_ENV_FILE
env_path = Path(__file__).resolve().parents[1] / ".env"
env_file = os.getenv("BACKEND_ENV_FILE", str(env_path))
load_dotenv(dotenv_path=env_file)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(env_file),
        env_file_encoding="utf-8",
        extra="ignore"  # ← 🔧 позволяет игнорировать лишние переменные в .env
    )

    HOST: str = Field(default="0.0.0.0", description="Bind address for the FastAPI server (e.g., 127.0.0.1 or 0.0.0.0)")
    PORT: int = Field(default=8000, description="Port for the FastAPI server (e.g., 8000)")

    # Application Settings
    PROJECT_NAME: str = "KIOSK Application"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., description="Secret key for the application")

    # Database Settings
    DATABASE_URL: str = Field(..., description="Database connection URL")

    # Authentication Settings
    JWT_SECRET_KEY: str = Field(..., description="JWT secret key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Refresh token expiry in days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Kiosk Authentication Settings - Extended JWT for self-service kiosks
    KIOSK_JWT_SECRET_KEY: str = Field(..., description="Kiosk JWT secret key for long-lived tokens")
    KIOSK_JWT_ALGORITHM: str = "HS256"
    KIOSK_ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    KIOSK_REFRESH_TOKEN_EXPIRE_DAYS: int = 90
    KIOSK_JWT_KEY_ID: str = Field(..., description="Key identifier for kiosk JWT tokens")

    # File Upload Settings
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_PATH: str = "./uploads"

    # ============================================
    # MEDIA STORAGE CONFIGURATION
    # ============================================
    # Purpose: Configurable path for serving media assets (images, videos)
    #          Frontend loads media from this location via HTTP
    #
    # Usage:
    #   - Development: "./media" or "../frontend/apps/kiosk/public" (relative to backend)
    #   - Production: "/var/kiosk/media" (absolute path on host filesystem)
    #   - Docker: Mount volume to this path in docker-compose.yml
    #
    # Future Enhancement: When implementing full CMS, this will be replaced by
    #                     storage provider abstraction (local/S3/MinIO) in
    #                     backend/app/services/storage/ (similar to frontend)
    #
    # Note: This is a temporary config-only solution. Backend simply serves
    #       files from this directory - no business logic, no upload handling.
    MEDIA_PATH: str = "./media"

    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/app.log"

    # CORS Settings
    # Accepts multiple input formats via validator:
    # 1. Comma-separated string (Railway, Heroku, cloud platforms): "http://localhost,http://localhost:3000"
    # 2. JSON array string (backward compatibility): '["http://localhost", "http://localhost:3000"]'
    # 3. List from Python code (defaults): ["http://localhost", "http://localhost:3000"]
    #
    # IMPORTANT: Type is Union to prevent Pydantic from auto-parsing before validator runs
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost,http://localhost:3000"

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Parse ALLOWED_ORIGINS from multiple formats to ensure universal compatibility.

        This validator runs BEFORE Pydantic's automatic type coercion, allowing us to
        handle comma-separated strings from Railway and other cloud platforms.
        """
        # If already a list, return as-is (from Python defaults or programmatic config)
        if isinstance(v, list):
            return v

        # If string, try different parsing strategies
        if isinstance(v, str):
            # Remove whitespace
            v = v.strip()

            # Empty string returns default
            if not v:
                return ["http://localhost", "http://localhost:3000"]

            # Try parsing as JSON array (backward compatibility)
            if v.startswith('[') and v.endswith(']'):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass

            # Parse as comma-separated string (Railway, Heroku, most cloud platforms)
            return [origin.strip() for origin in v.split(',') if origin.strip()]

        # Fallback to default for any unexpected type
        return ["http://localhost", "http://localhost:3000"]

    # External Integrations
    POS_API_URL: str = ""
    POS_API_KEY: str = ""
    PAYMENT_API_URL: str = ""
    PAYMENT_API_KEY: str = ""


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    print("✅ Settings loaded from:", env_file)
    print("✅ Loaded .env — SECRET_KEY:", os.getenv("SECRET_KEY"))
    return settings