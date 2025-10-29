#!/usr/bin/env python3
"""
UniMem AI 配置检查脚本
"""
import os
from dotenv import load_dotenv

def check_config():
    """检查系统配置"""
    print("🔍 UniMem AI 配置检查")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    # 检查必需的环境变量
    required_vars = {
        'NVIDIA_API_KEY': 'NVIDIA API密钥',
        'AWS_ACCESS_KEY_ID': 'AWS访问密钥ID',
        'AWS_SECRET_ACCESS_KEY': 'AWS秘密访问密钥',
        'S3_BUCKET_NAME': 'S3存储桶名称',
        'AWS_REGION': 'AWS区域'
    }
    
    missing_vars = []
    configured_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or value in ['your_nvidia_api_key_here', 'your_aws_access_key_here', 'your-s3-bucket-name']:
            missing_vars.append((var, description))
            print(f"❌ {var}: {description} - 未配置")
        else:
            configured_vars.append((var, description))
            print(f"✅ {var}: {description} - 已配置")
    
    print("\n" + "=" * 50)
    
    if missing_vars:
        print("❌ 配置不完整，需要设置以下环境变量：")
        print()
        for var, description in missing_vars:
            print(f"   {var}={description}")
        print()
        print("请在 .env 文件中设置这些变量，或通过环境变量设置。")
        print("示例 .env 文件内容：")
        print()
        print("# NVIDIA API配置")
        print("NVIDIA_API_KEY=your_actual_nvidia_api_key")
        print()
        print("# AWS配置")
        print("AWS_ACCESS_KEY_ID=your_actual_aws_access_key")
        print("AWS_SECRET_ACCESS_KEY=your_actual_aws_secret_key")
        print("S3_BUCKET_NAME=your-actual-s3-bucket-name")
        print("AWS_REGION=us-east-1")
        print()
        print("# 环境设置")
        print("ENVIRONMENT=development")
        return False
    else:
        print("✅ 所有必需配置都已设置！")
        print("🚀 可以启动服务器了：python main.py")
        return True

if __name__ == "__main__":
    check_config()
