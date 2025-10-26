import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "your-database-url-please-change-in-production")
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-jwt-please-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Add AWS credentials
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", "your-AWS_ACCESS_KEY_ID-please-change-in-production")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", "your-AWS_SECRET_ACCESS_KEY-please-change-in-production")
    s3_bucket_name: Optional[str] = os.getenv("S3_BUCKET_NAME", "your-AWS_s3_bucket_name")
    
    # PASSWORD CHECK
    PASSWORD_MIN_LENGTH: int = 8
    
    # API settings
    API_V1_STR: str = "/api/v1"
    
    # AI API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")  # Optional - expensive
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")  # Recommended - cheap & powerful

    # Frontend and deployment settings
    vite_api_base_url: Optional[str] = os.getenv("VITE_API_BASE_URL", "")
    ec2_public_ip: Optional[str] = os.getenv("EC2_PUBLIC_IP", "")

    # External API keys
    rapidapi_key: Optional[str] = os.getenv("RAPIDAPI_KEY", "")
    admin_secret: Optional[str] = os.getenv("ADMIN_SECRET", "")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env

settings = Settings()