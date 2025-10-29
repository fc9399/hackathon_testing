# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # AWS配置
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    
    # NVIDIA NIM配置
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # development or production
    NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')
    
    # 开发环境：使用NVIDIA托管API
    NVIDIA_API_BASE_URL = "https://integrate.api.nvidia.com/v1"
    
    # 生产环境：使用自己部署的NIM
    NIM_EMBEDDING_URL = os.getenv('NIM_EMBEDDING_URL', 'http://embedding-nim.nim-service:8000/v1')
    
    # Embedding模型配置
    EMBEDDING_MODEL = "nvidia/llama-3.2-nv-embedqa-1b-v2"
    EMBEDDING_DIMENSION = 2048
    
    # 文件上传配置
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'md'}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    # 用户认证配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

settings = Settings()