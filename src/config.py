import json
import os
from typing import Dict, Any
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variables support"""
    
    # API Keys
    apify_api_token: str
    claude_api_key: str
    
    # Database
    database_url: str = "sqlite:///./data/ia_fiscal.db"
    
    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    
    # Email Settings
    smtp_username: str
    smtp_password: str
    admin_email: str
    
    # Telegram Settings
    telegram_bot_token: str
    telegram_chat_id: str
    
    # Security
    secret_key: str
    jwt_secret: str
    webhook_secret: str
    
    # External APIs
    precos_api_url: str = "https://api.precos.gov.br"
    catmat_api_url: str = "https://api.catmat.gov.br"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def load_config() -> Dict[str, Any]:
    """Load configuration from JSON file"""
    config_path = Path("config/config.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Global settings instance
settings = Settings()
config = load_config()