# UniMem AI 快速启动指南

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd UniMem

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件
nano .env
```

**必需配置项：**
```bash
# AWS配置
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
S3_BUCKET_NAME=your-s3-bucket-name
AWS_REGION=us-east-1

# NVIDIA配置
NVIDIA_API_KEY=your_nvidia_api_key_here

# 安全配置
SECRET_KEY=your-secret-key-here-change-in-production
```

### 3. 启动服务
```bash
# 启动服务器
python main.py
```

服务将在 `http://localhost:8012` 启动

### 4. 测试系统
```bash
# 测试基础功能
python test_api.py

# 测试用户系统
python test_user_system.py
```

### 5. 访问API文档
打开浏览器访问：`http://localhost:8012/docs`

## 🔐 用户系统使用

### 1. 注册用户
```bash
curl -X POST "http://localhost:8012/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'
```

### 2. 用户登录
```bash
curl -X POST "http://localhost:8012/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword123"
  }'
```

### 3. 使用认证令牌
```bash
# 获取访问令牌后，在所有API请求中添加认证头
curl -X GET "http://localhost:8012/api/search/memories" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📁 文件上传

### 1. 上传文本
```bash
curl -X POST "http://localhost:8012/api/upload/text?text=这是一个测试文本" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. 上传文件
```bash
curl -X POST "http://localhost:8012/api/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@document.pdf"
```

## 🔍 搜索和对话

### 1. 语义搜索
```bash
curl -X POST "http://localhost:8012/api/search/semantic" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "搜索内容",
    "limit": 10,
    "threshold": 0.7
  }'
```

### 2. AI对话
```bash
curl -X POST "http://localhost:8012/api/agent/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，请介绍一下你自己",
    "use_memory": true
  }'
```

## 🏗️ 生产部署

### 1. AWS EKS部署
参考 `DEPLOYMENT_GUIDE.md` 进行完整的生产环境部署

### 2. 关键配置
- 使用强密码和安全的SECRET_KEY
- 配置正确的AWS权限
- 设置NVIDIA NIM服务
- 配置监控和日志

## 🛠️ 故障排除

### 1. 常见问题
- **服务器启动失败**: 检查环境变量配置
- **认证失败**: 检查JWT密钥配置
- **文件上传失败**: 检查S3配置和权限
- **搜索无结果**: 检查embedding服务配置

### 2. 日志查看
```bash
# 查看服务器日志
tail -f logs/unimem.log

# 查看Docker日志（如果使用Docker）
docker logs unimem-ai
```

### 3. 健康检查
```bash
# 检查服务状态
curl http://localhost:8012/health
```

## 📚 更多信息

- **完整文档**: 访问 `http://localhost:8012/docs`
- **部署指南**: 查看 `DEPLOYMENT_GUIDE.md`
- **项目状态**: 查看 `PROJECT_STATUS.md`
- **API测试**: 运行 `test_user_system.py`

## 🎯 下一步

1. 配置生产环境
2. 部署到AWS EKS
3. 添加前端界面
4. 集成更多AI模型
5. 扩展功能特性

---

**注意**: 这是一个多用户系统，每个用户的数据都是隔离的。确保在生产环境中使用强密码和安全的配置。
