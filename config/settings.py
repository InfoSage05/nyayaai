"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    
    # Groq Configuration
    groq_api_key: Optional[str] = None
    
    # Embedding Model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Application
    app_name: str = "NyayaAI"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Make .env file optional - don't fail if it doesn't exist
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
