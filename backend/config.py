"""Configuration management using Pydantic Settings."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    flask_env: str = "development"
    secret_key: str
    database_url: str = "sqlite:///./scheduler.db"
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_url: str = "http://localhost:3000"
    
    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    
    # Mistral AI
    mistral_api_key: str
    mistral_model: str = "mistral-small-latest"
    
    # Security
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000"
    session_cookie_secure: bool = False
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "Lax"
    csrf_secret: str
    
    # Rate Limiting
    ai_rate_limit: int = 50
    api_rate_limit: int = 1000
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Create global settings instance
settings = Settings()
