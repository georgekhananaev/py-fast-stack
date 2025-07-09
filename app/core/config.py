import os
import secrets
from functools import lru_cache

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    app_name: str = "PyFastStack"
    app_version: str = "1.0.0"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./pyfaststack.db"

    secret_key: str = Field(
        default_factory=lambda: os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Security settings
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    allowed_hosts: list[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Allowed host headers"
    )
    
    # Development settings (optional)
    dummy_user_password: str | None = Field(
        default=None,
        description="Password for dummy users in development"
    )

    @field_validator('secret_key')
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is not the default."""
        if v == "your-secret-key-here-change-in-production":
            return secrets.token_urlsafe(32)
        return v

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
