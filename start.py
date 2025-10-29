#!/usr/bin/env python3
"""
UniMem AI 启动脚本
"""
import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查.env文件
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ 未找到.env文件，请创建并配置环境变量")
        print("📝 需要配置的变量：")
        print("   - AWS_ACCESS_KEY_ID")
        print("   - AWS_SECRET_ACCESS_KEY")
        print("   - AWS_REGION")
        print("   - S3_BUCKET_NAME")
        print("   - NVIDIA_API_KEY")
        print("   - ENVIRONMENT (development/production)")
        return False
    
    print("✅ .env文件存在")
    return True

def install_dependencies():
    """安装依赖"""
    print("📦 安装依赖包...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def start_server():
    """启动服务器"""
    print("🚀 启动UniMem AI服务器...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 服务器启动失败: {e}")

def main():
    """主函数"""
    print("🧠 UniMem AI - 个人记忆中心")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        return
    
    # 安装依赖
    if not install_dependencies():
        return
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()
