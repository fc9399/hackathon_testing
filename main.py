# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload_router, embedding_router, search_router, ai_agent_router, auth
from services.s3_service import s3_service
from services.embedding_service import embedding_service
from services.database_service import database_service
from services.ai_agent_service import ai_agent_service
from config import settings

app = FastAPI(
    title="Personal Memory Hub API",
    description="AWS & NVIDIA Hackathon Project - File Upload & Embedding Service",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)  # 认证路由
app.include_router(upload_router)
app.include_router(embedding_router)
app.include_router(search_router)
app.include_router(ai_agent_router)

@app.get("/")
def root():
    """根路径 - 服务信息"""
    return {
        "service": "Personal Memory Hub API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "embedding_service": "NIM (Production)" if settings.ENVIRONMENT == "production" else "NVIDIA API (Development)",
        "endpoints": {
            "upload": "/api/upload",
            "upload_text": "/api/upload/text",
            "embedding": "/api/embeddings/generate",
            "batch_embedding": "/api/embeddings/batch",
            "search": "/api/search/semantic",
            "memories": "/api/search/memories",
            "chat": "/api/agent/chat",
            "conversations": "/api/agent/conversations",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """整体健康检查"""
    
    # 检查S3服务
    s3_health = s3_service.health_check()
    
    # 检查Embedding服务
    embedding_health = embedding_service.health_check()
    
    # 检查数据库服务
    database_health = database_service.health_check()
    
    # 检查AI Agent服务
    ai_agent_health = ai_agent_service.health_check()
    
    # 判断整体状态
    overall_status = "healthy" if (
        s3_health["status"] == "healthy" and 
        embedding_health["status"] == "healthy" and
        database_health["status"] in ["healthy", "degraded"] and  # 允许degraded状态
        ai_agent_health["status"] in ["healthy", "degraded"]  # 允许degraded状态
    ) else "unhealthy"
    
    return {
        "status": overall_status,
        "environment": settings.ENVIRONMENT,
        "services": {
            "s3": s3_health,
            "embedding": embedding_health,
            "database": database_health,
            "ai_agent": ai_agent_health
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Personal Memory Hub API...")
    print(f"📦 S3 Bucket: {settings.S3_BUCKET_NAME}")
    print(f"🌍 AWS Region: {settings.AWS_REGION}")
    print(f"🔧 Environment: {settings.ENVIRONMENT}")
    print(f"🤖 Embedding Model: {settings.EMBEDDING_MODEL}")
    uvicorn.run(app, host="0.0.0.0", port=8012)








