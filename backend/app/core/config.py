"""
GrantThrive Configuration Management
Enterprise-grade configuration with environment-based settings
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "GrantThrive API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "grantthrive"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Email (for future implementation)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        values = info.data if hasattr(info, 'data') else {}
        return f"postgresql://{values.get('DB_USER', 'postgres')}:{values.get('DB_PASSWORD', 'password')}@{values.get('DB_HOST', 'localhost')}:{values.get('DB_PORT', 5432)}/{values.get('DB_NAME', 'grantthrive')}"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# Global settings instance
settings = Settings()

