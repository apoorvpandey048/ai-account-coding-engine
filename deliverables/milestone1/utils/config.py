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
    API_KEY_REQUIRED: bool = False
    VALID_API_KEYS: List[str] = []
    
    # Azure OpenAI settings
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4-1-mini"
    AZURE_OPENAI_MODEL: str = "gpt-4.1-mini"
    AZURE_OPENAI_MAX_INPUT_TOKENS: int = 3000000
    AZURE_OPENAI_MAX_CACHED_INPUT_TOKENS: int = 1200000
    AZURE_OPENAI_MAX_OUTPUT_TOKENS: int = 1000000
    AZURE_OPENAI_TEMPERATURE: float = 0.3
    AZURE_OPENAI_TOP_P: float = 1.0
    
    # Storage settings
    STORAGE_ACCOUNT_NAME: str = ""
    CONTAINER_RAW: str = "raw-invoices"
    CONTAINER_PROCESSED: str = "processed"
    CONTAINER_FEEDBACK: str = "feedback"
    
    # Chart of accounts (can be loaded from file or database)
    CHART_OF_ACCOUNTS_FILE: str = ""
    
    # Feedback storage
    FEEDBACK_STORAGE_TYPE: str = "file"  # file, blob, database
    FEEDBACK_FILE_PATH: str = "feedback_log.jsonl"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Parse API keys from comma-separated string if provided
        if isinstance(self.VALID_API_KEYS, str):
            self.VALID_API_KEYS = [
                key.strip() 
                for key in self.VALID_API_KEYS.split(",") 
                if key.strip()
            ]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
