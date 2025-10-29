#!/usr/bin/env python3
"""
UniMem AI - 安全检查脚本
检查代码中是否包含敏感信息，确保不会泄露到GitHub
"""

import os
import re
import sys
from pathlib import Path

# 敏感信息模式
SENSITIVE_PATTERNS = [
    # API密钥和令牌
    (r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?', 'API密钥'),
    (r'token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?', '访问令牌'),
    (r'secret["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?', '密钥'),
    
    # AWS凭证
    (r'aws[_-]?access[_-]?key[_-]?id["\']?\s*[:=]\s*["\']?[A-Z0-9]{20}["\']?', 'AWS Access Key ID'),
    (r'aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9/+=]{40}["\']?', 'AWS Secret Access Key'),
    
    # 数据库连接字符串
    (r'mongodb://[^"\s]+', 'MongoDB连接字符串'),
    (r'postgresql://[^"\s]+', 'PostgreSQL连接字符串'),
    (r'mysql://[^"\s]+', 'MySQL连接字符串'),
    
    # 密码
    (r'password["\']?\s*[:=]\s*["\']?[^"\']{8,}["\']?', '密码'),
    (r'pwd["\']?\s*[:=]\s*["\']?[^"\']{8,}["\']?', '密码'),
    
    # 私钥
    (r'-----BEGIN [A-Z ]+ PRIVATE KEY-----', '私钥'),
    (r'-----BEGIN RSA PRIVATE KEY-----', 'RSA私钥'),
    
    # 邮箱和敏感信息
    (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '邮箱地址'),
    (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '信用卡号'),
    (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN'),
]

# 需要检查的文件扩展名
CHECK_EXTENSIONS = {'.py', '.js', '.ts', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'}

# 需要跳过的目录
SKIP_DIRS = {'__pycache__', '.git', '.pytest_cache', 'node_modules', '.venv', 'venv', 'env'}

# 需要跳过的文件
SKIP_FILES = {'.gitignore', 'security_check.py', 'env.example'}

def check_file(file_path):
    """检查单个文件是否包含敏感信息"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description in SENSITIVE_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # 检查是否是注释或示例
                        stripped_line = line.strip()
                        if not (stripped_line.startswith('#') or 
                               stripped_line.startswith('//') or 
                               stripped_line.startswith('*') or
                               'example' in stripped_line.lower() or
                               'your_' in stripped_line.lower() or
                               'placeholder' in stripped_line.lower()):
                            issues.append({
                                'file': str(file_path),
                                'line': line_num,
                                'content': line.strip(),
                                'type': description
                            })
    except Exception as e:
        print(f"⚠️  无法读取文件 {file_path}: {e}")
    
    return issues

def scan_directory(directory):
    """扫描目录中的所有文件"""
    all_issues = []
    file_count = 0
    
    for root, dirs, files in os.walk(directory):
        # 跳过不需要检查的目录
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            file_path = Path(root) / file
            
            # 跳过不需要检查的文件
            if file in SKIP_FILES:
                continue
                
            # 只检查特定扩展名的文件
            if file_path.suffix.lower() not in CHECK_EXTENSIONS:
                continue
            
            file_count += 1
            issues = check_file(file_path)
            all_issues.extend(issues)
    
    return all_issues, file_count

def main():
    """主函数"""
    print("🔍 UniMem AI - 安全检查")
    print("=" * 50)
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    
    print(f"📁 扫描目录: {project_root}")
    print(f"🔍 检查文件类型: {', '.join(CHECK_EXTENSIONS)}")
    print(f"⏭️  跳过目录: {', '.join(SKIP_DIRS)}")
    print()
    
    # 扫描文件
    issues, file_count = scan_directory(project_root)
    
    print(f"📊 扫描完成: 检查了 {file_count} 个文件")
    print()
    
    if issues:
        print("❌ 发现潜在的安全问题:")
        print("=" * 50)
        
        for issue in issues:
            print(f"🚨 {issue['type']}")
            print(f"   文件: {issue['file']}")
            print(f"   行号: {issue['line']}")
            print(f"   内容: {issue['content']}")
            print()
        
        print("⚠️  建议:")
        print("1. 检查上述文件，确保没有硬编码的敏感信息")
        print("2. 将敏感信息移到环境变量文件中")
        print("3. 确保 .env 文件在 .gitignore 中")
        print("4. 使用 env.example 作为配置模板")
        
        return 1
    else:
        print("✅ 安全检查通过！没有发现敏感信息泄露风险")
        print()
        print("💡 安全建议:")
        print("1. 定期运行此检查脚本")
        print("2. 确保 .env 文件不被提交到版本控制")
        print("3. 使用强密码和安全的API密钥")
        print("4. 定期轮换访问凭证")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())
