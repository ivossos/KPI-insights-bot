"""
Production Configuration for KPI Insight Bot
"""

import os
from pathlib import Path
from pydantic import BaseSettings
from typing import List, Optional

class ProductionSettings(BaseSettings):
    # Application
    environment: str = "production"
    debug: bool = False
    secret_key: str = os.getenv("SECRET_KEY", "default-secret-key")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    dashboard_port: int = int(os.getenv("DASHBOARD_PORT", "8502"))
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://kpi_user:kpi_password@localhost:5432/kpi_bot")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # LLM APIs
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    claude_api_key: str = os.getenv("CLAUDE_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Oracle EPM
    oracle_epm_host: str = os.getenv("ORACLE_EPM_HOST", "")
    oracle_epm_port: int = int(os.getenv("ORACLE_EPM_PORT", "443"))
    oracle_epm_username: str = os.getenv("ORACLE_EPM_USERNAME", "")
    oracle_epm_password: str = os.getenv("ORACLE_EPM_PASSWORD", "")
    oracle_epm_service_name: str = os.getenv("ORACLE_EPM_SERVICE_NAME", "FCCS")
    
    # Oracle Fusion
    oracle_fusion_host: str = os.getenv("ORACLE_FUSION_HOST", "")
    oracle_fusion_username: str = os.getenv("ORACLE_FUSION_USERNAME", "")
    oracle_fusion_password: str = os.getenv("ORACLE_FUSION_PASSWORD", "")
    
    # Authentication
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Google OAuth
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "")
    
    # Email/SMTP
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "")
    admin_email: str = os.getenv("ADMIN_EMAIL", "")
    
    # Apify
    apify_api_token: str = os.getenv("APIFY_API_TOKEN", "")
    
    # Monitoring
    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
    prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "9090"))
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")
    log_file: str = os.getenv("LOG_FILE", "logs/kpi_bot.log")
    
    # Performance
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "100"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    
    # Security
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    allowed_hosts: List[str] = os.getenv("ALLOWED_HOSTS", "*").split(",")
    session_secret: str = os.getenv("SESSION_SECRET", "session-secret")
    
    # SSL/TLS
    ssl_cert_path: str = os.getenv("SSL_CERT_PATH", "/etc/nginx/ssl/cert.pem")
    ssl_key_path: str = os.getenv("SSL_KEY_PATH", "/etc/nginx/ssl/key.pem")
    
    # Paths
    data_dir: Path = Path("data")
    logs_dir: Path = Path("logs")
    reports_dir: Path = Path("reports")
    chroma_db_path: Path = Path("chroma_db")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = ProductionSettings()

# Ensure directories exist
for directory in [settings.data_dir, settings.logs_dir, settings.reports_dir, settings.chroma_db_path]:
    directory.mkdir(parents=True, exist_ok=True)

# Configuration for different components
config = {
    "api": {
        "host": "0.0.0.0",
        "port": settings.api_port,
        "debug": settings.debug,
        "reload": False,
        "log_level": settings.log_level.lower(),
        "access_log": True
    },
    "dashboard": {
        "host": "0.0.0.0",
        "port": settings.dashboard_port,
        "debug": settings.debug,
        "theme": {
            "base": "dark",
            "primaryColor": "#ffd700",
            "backgroundColor": "#1a1a1a",
            "secondaryBackgroundColor": "#2d2d2d",
            "textColor": "#ffffff"
        }
    },
    "database": {
        "url": settings.database_url,
        "echo": settings.debug,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True
    },
    "redis": {
        "url": settings.redis_url,
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "retry_on_timeout": True
    },
    "oracle": {
        "epm": {
            "host": settings.oracle_epm_host,
            "port": settings.oracle_epm_port,
            "username": settings.oracle_epm_username,
            "password": settings.oracle_epm_password,
            "service_name": settings.oracle_epm_service_name,
            "connection_timeout": 30,
            "read_timeout": 60
        },
        "fusion": {
            "host": settings.oracle_fusion_host,
            "username": settings.oracle_fusion_username,
            "password": settings.oracle_fusion_password,
            "connection_timeout": 30,
            "read_timeout": 60
        }
    },
    "auth": {
        "jwt_secret": settings.jwt_secret_key,
        "jwt_algorithm": settings.jwt_algorithm,
        "jwt_expiration_hours": settings.jwt_expiration_hours,
        "google_client_id": settings.google_client_id,
        "google_client_secret": settings.google_client_secret,
        "google_redirect_uri": settings.google_redirect_uri
    },
    "llm": {
        "openai_api_key": settings.openai_api_key,
        "claude_api_key": settings.claude_api_key,
        "anthropic_api_key": settings.anthropic_api_key,
        "default_model": "gpt-4",
        "fallback_model": "gpt-3.5-turbo",
        "max_tokens": 1000,
        "temperature": 0.3
    },
    "notifications": {
        "smtp": {
            "host": settings.smtp_host,
            "port": settings.smtp_port,
            "username": settings.smtp_username,
            "password": settings.smtp_password,
            "from_email": settings.smtp_from_email,
            "use_tls": True
        },
        "admin_email": settings.admin_email
    },
    "monitoring": {
        "prometheus_enabled": settings.prometheus_enabled,
        "prometheus_port": settings.prometheus_port,
        "sentry_dsn": settings.sentry_dsn,
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "log_file": settings.log_file
    },
    "security": {
        "cors_origins": settings.cors_origins,
        "allowed_hosts": settings.allowed_hosts,
        "session_secret": settings.session_secret,
        "ssl_cert_path": settings.ssl_cert_path,
        "ssl_key_path": settings.ssl_key_path
    },
    "performance": {
        "cache_ttl": settings.cache_ttl_seconds,
        "max_concurrent_requests": settings.max_concurrent_requests,
        "request_timeout": settings.request_timeout_seconds
    }
}