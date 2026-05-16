import os
import json
import secrets
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables
    )

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT != "production"

    # Database - Credentials MUST come from environment variables
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/detections_db"
    )
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_POOL_PRE_PING: bool = True

    # Server
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = DEBUG
    API_TITLE: str = "Object Detection API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Real-Time Object Detection using YOLOv8"

    # Gradio
    GRADIO_HOST: str = os.getenv("GRADIO_HOST", "0.0.0.0")
    GRADIO_PORT: int = int(os.getenv("GRADIO_PORT", "7860"))
    GRADIO_SHARE: bool = False

    # Security - CRITICAL: Never hardcode secrets, use environment variables
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32) if DEBUG else None)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # YOLOv8 Model Configuration
    MODEL_PATH: str = os.getenv("MODEL_PATH", "yolov8n.pt")
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    IOU_THRESHOLD: float = float(os.getenv("IOU_THRESHOLD", "0.45"))
    IMAGE_SIZE: int = int(os.getenv("IMAGE_SIZE", "640"))
    MAX_DETECTIONS: int = 100
    DEVICE: str = os.getenv("DEVICE", "0")

    # Cloud Storage - Credentials from environment variables ONLY
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    ENABLE_CLOUDINARY: bool = os.getenv("ENABLE_CLOUDINARY", "false").lower() == "true"

    # CORS - Production-safe configuration
    ALLOWED_ORIGINS: List[str] = (
        os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if os.getenv("ALLOWED_ORIGINS")
        else (
            [
                "http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176",
                "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5174",
                "http://127.0.0.1:5175", "http://127.0.0.1:5176"
            ]
            if DEBUG
            else []
        )
    )
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOW_HEADERS: List[str] = ["Content-Type", "Authorization", "Accept", "Origin"]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/app.log"

    # Processing and Security Limits
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    MAX_IMAGE_SIZE: int = 52428800  # 50MB
    MAX_VIDEO_SIZE: int = 524288000  # 500MB
    REQUEST_TIMEOUT: int = 300  # 5 minutes
    MAX_REQUEST_BODY_SIZE: int = 52428800  # 50MB
    BATCH_SIZE: int = 16
    NUM_WORKERS: int = 4

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Features
    ENABLE_TRAINING: bool = True
    ENABLE_EXPORT: bool = True

    # Security Headers
    SECURE_HSTS_SECONDS: int = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = True
    SECURE_HSTS_PRELOAD: bool = True


# Create settings instance with error handling
try:
    settings = Settings()
except Exception as e:
    print(f"⚠️  Warning: Error loading settings: {str(e)}")
    settings = Settings()  # Use defaults
