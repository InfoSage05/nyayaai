"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings
from typing import Optional
import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Load .env file if it exists
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    
    # Groq Configuration
    groq_api_key: Optional[str] = os.environ.get("GROQ_API_KEY")
    
    # Tavily Search Configuration
    tavily_api_key: Optional[str] = os.environ.get("TAVILY_API_KEY")

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
        env_ignore_empty = True
        extra = "ignore"  # Allow extra env vars without validation error


# Global settings instance - handle .env file errors gracefully
def _load_settings():
    """Load settings with fallback if .env file has issues."""
    # Check if .env file exists and is readable
    env_file = ".env"
    can_read_env = False
    
    if os.path.exists(env_file):
        try:
            # Try to read the file to check permissions
            with open(env_file, 'r') as f:
                f.read(1)  # Try to read at least 1 byte
            can_read_env = True
        except (PermissionError, IOError):
            logger.warning(f"Cannot read .env file due to permissions. Using environment variables only.")
            can_read_env = False
    
    if can_read_env:
        try:
            return Settings()
        except Exception as e:
            logger.warning(f"Error loading .env file: {e}. Using environment variables and defaults.")
    
    # Fallback: Create Settings without .env file
    # We need to create a new class with env_file=None
    class SettingsNoEnv(Settings):
        class Config:
            env_file = None  # Don't read .env file
            env_file_encoding = "utf-8"
            case_sensitive = False
            env_ignore_empty = True
    
    # Load from environment variables only
    return SettingsNoEnv(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
        qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
    )


settings = _load_settings()
