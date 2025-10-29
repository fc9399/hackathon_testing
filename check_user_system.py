#!/usr/bin/env python3
"""
用户系统配置检查脚本
检查用户系统相关的配置和依赖
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """检查依赖包"""
    print("🔍 检查依赖包...")
    
    required_packages = [
        'fastapi',
        'uvicorn', 
        'boto3',
        'jose',
        'passlib',
        'pydantic',
        'numpy',
        'PIL',
        'PyPDF2',
        'docx',
        'pytesseract',
        'pdf2image'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            elif package == 'jose':
                from jose import jwt
            elif package == 'passlib':
                from passlib.context import CryptContext
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ 所有依赖包已安装")
        return True

def check_config_files():
    """检查配置文件"""
    print("\n🔍 检查配置文件...")
    
    config_files = [
        'config.py',
        'schemas.py',
        'services/auth_service.py',
        'routers/auth.py',
        'main.py'
    ]
    
    missing_files = []
    
    for file_path in config_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ 缺少配置文件: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ 所有配置文件存在")
        return True

def check_environment_variables():
    """检查环境变量"""
    print("\n🔍 检查环境变量...")
    
    # 加载.env文件
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'SECRET_KEY',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'S3_BUCKET_NAME',
        'AWS_REGION'
    ]
    
    optional_vars = [
        'NVIDIA_API_KEY',
        'NIM_EMBEDDING_URL',
        'ACCESS_TOKEN_EXPIRE_MINUTES',
        'REFRESH_TOKEN_EXPIRE_DAYS'
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}_here" and value != "your-secret-key-here-change-in-production":
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} (必需)")
            missing_required.append(var)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}_here":
            print(f"  ✅ {var}")
        else:
            print(f"  ⚠️  {var} (可选)")
            missing_optional.append(var)
    
    if missing_required:
        print(f"\n❌ 缺少必需环境变量: {', '.join(missing_required)}")
        print("请编辑 .env 文件并设置这些变量")
        return False
    else:
        print("\n✅ 必需环境变量已配置")
        if missing_optional:
            print(f"⚠️  可选环境变量未配置: {', '.join(missing_optional)}")
        return True

def check_imports():
    """检查模块导入"""
    print("\n🔍 检查模块导入...")
    
    try:
        # 检查主要模块
        from config import settings
        print("  ✅ config.settings")
        
        from schemas import User, UserCreate, Token
        print("  ✅ schemas (用户模型)")
        
        from services.auth_service import auth_service
        print("  ✅ services.auth_service")
        
        from routers.auth import router as auth_router
        print("  ✅ routers.auth")
        
        from main import app
        print("  ✅ main.app")
        
        print("\n✅ 所有模块导入成功")
        return True
        
    except Exception as e:
        print(f"\n❌ 模块导入失败: {e}")
        return False

def check_database_tables():
    """检查数据库表结构"""
    print("\n🔍 检查数据库表结构...")
    
    try:
        from services.database_service import database_service
        from services.auth_service import auth_service
        
        # 检查健康状态
        db_health = database_service.health_check()
        auth_health = auth_service.health_check()
        
        print(f"  📊 数据库服务: {db_health.get('status', 'unknown')}")
        print(f"  🔐 认证服务: {auth_health.get('status', 'unknown')}")
        
        if db_health.get('status') == 'healthy' and auth_health.get('status') == 'healthy':
            print("\n✅ 数据库服务正常")
            return True
        else:
            print("\n⚠️  数据库服务可能有问题")
            return False
            
    except Exception as e:
        print(f"\n❌ 数据库检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 UniMem AI 用户系统配置检查")
    print("=" * 50)
    
    checks = [
        ("依赖包", check_dependencies),
        ("配置文件", check_config_files),
        ("环境变量", check_environment_variables),
        ("模块导入", check_imports),
        ("数据库服务", check_database_tables)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n❌ {check_name}检查出错: {e}")
            results.append((check_name, False))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📊 检查结果总结:")
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("🎉 所有检查通过！系统已准备就绪。")
        print("\n🚀 可以启动服务器:")
        print("   python main.py")
        print("\n🧪 可以运行测试:")
        print("   python test_user_system.py")
    else:
        print("⚠️  部分检查失败，请根据上述信息修复问题。")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
