
import json
import os
from typing import Dict, Any, List
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variables support"""
    
    # Application
    environment: str = "development"
    debug: bool = False
    api_port: int = 8000
    dashboard_port: int = 8501
    
    # API Keys
    apify_api_token: str
    claude_api_key: str
    
    # Database
    database_url: str = "sqlite:///./data/ia_fiscal.db"
    redis_url: str = "redis://localhost:6379/0"
    
    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    
    # Email Settings
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    smtp_from_email: str = ""
    admin_email: str
    
    # Telegram Settings
    telegram_bot_token: str
    telegram_chat_id: str
    
    # Security
    secret_key: str
    jwt_secret: str
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    webhook_secret: str
    session_secret: str = ""
    
    # External APIs
    precos_api_url: str = "https://api.precos.gov.br"
    catmat_api_url: str = "https://api.catmat.gov.br"
    
    # LLM APIs
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # Oracle connections
    oracle_epm_host: str = ""
    oracle_epm_port: int = 443
    oracle_epm_username: str = ""
    oracle_epm_password: str = ""
    oracle_epm_service_name: str = "FCCS"
    oracle_fusion_host: str = ""
    oracle_fusion_username: str = ""
    oracle_fusion_password: str = ""
    
    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    sentry_dsn: str = ""
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "logs/ia_fiscal.log"
    
    # Performance
    cache_ttl_seconds: int = 3600
    max_concurrent_requests: int = 100
    request_timeout_seconds: int = 30
    
    # Security
    cors_origins: str = "*"
    allowed_hosts: str = "*"
    ssl_cert_path: str = "/etc/nginx/ssl/cert.pem"
    ssl_key_path: str = "/etc/nginx/ssl/key.pem"
    
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
