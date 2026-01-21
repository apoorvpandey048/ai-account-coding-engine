"""Configuration management using Pydantic settings."""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service settings
    SERVICE_NAME: str = "ai-account-coding-service"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # API settings
    API_KEY_REQUIRED: bool = True
    VALID_API_KEYS: List[str] = []
    
    # Azure OpenAI settings
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""  # Also accepts AZURE_OPENAI_KEY
    AZURE_OPENAI_KEY: str = ""  # Alternative key name
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4"
    
    # Chart of accounts (can be loaded from file or database)
    CHART_OF_ACCOUNTS_FILE: str = ""
    
    # Feedback storage
    FEEDBACK_STORAGE_TYPE: str = "file"  # file, blob, database
    FEEDBACK_FILE_PATH: str = "feedback_log.jsonl"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra env vars we don't explicitly define
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Parse API keys from comma-separated string if provided
        if isinstance(self.VALID_API_KEYS, str):
            self.VALID_API_KEYS = [
                key.strip() 
                for key in self.VALID_API_KEYS.split(",") 
                if key.strip()
            ]
        
        # Support both AZURE_OPENAI_KEY and AZURE_OPENAI_API_KEY
        if not self.AZURE_OPENAI_API_KEY and self.AZURE_OPENAI_KEY:
            self.AZURE_OPENAI_API_KEY = self.AZURE_OPENAI_KEY


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
