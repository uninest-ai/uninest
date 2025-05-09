import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "your-database-url-in-env")
    
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
    
    # Open AI API Key
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # EC2_PUBLIC_IP: str = os.getenv("EC2_PUBLIC_IP", "3.15.186.50")
    EC2_PUBLIC_IP: str = os.getenv("EC2_PUBLIC_IP", "18.219.81.184")
    
    vite_api_base_url: Optional[str] = None
    class Config:
        env_file = ".env"

settings = Settings()