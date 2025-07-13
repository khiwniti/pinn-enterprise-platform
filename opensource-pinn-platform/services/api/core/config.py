"""
Configuration settings for the PINN Platform
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://pinn:secure123@postgres:5432/pinn"
    
    # Redis
    redis_url: str = "redis://:secure123@redis:6379/0"
    
    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "secure123"
    minio_secure: bool = False
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Security
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # API
    api_rate_limit: int = 100
    max_workers: int = 4
    max_memory_per_worker: str = "4G"
    max_training_time: int = 3600
    
    # Monitoring
    enable_monitoring: bool = True
    enable_tracing: bool = True
    enable_logging: bool = True
    
    # CORS
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()