# Embedding服务
from openai import OpenAI
from typing import List
from config import settings

class EmbeddingService:
    """
    Embedding服务：支持开发环境和生产环境
    - 开发环境：调用NVIDIA托管API（快速测试）
    - 生产环境：调用AWS EKS上部署的NIM服务
    """
    
    def __init__(self):
        # 检查API密钥
        if not settings.NVIDIA_API_KEY or settings.NVIDIA_API_KEY == "your_nvidia_api_key_here":
            raise ValueError("NVIDIA API密钥未配置，请设置NVIDIA_API_KEY环境变量")
        
        # 根据环境选择不同的base_url
        if settings.ENVIRONMENT == "production":
            self.base_url = settings.NIM_EMBEDDING_URL
            print(f"🚀 Using production NIM: {self.base_url}")
        else:
            self.base_url = settings.NVIDIA_API_BASE_URL
            print(f"🔧 Using development API: {self.base_url}")
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=settings.NVIDIA_API_KEY
        )
        self.model = settings.EMBEDDING_MODEL
    
    def generate_embedding(
        self, 
        text: str, 
        input_type: str = "passage"
    ) -> List[float]:
        """
        生成单个文本的embedding
        
        Args:
            text: 输入文本
            input_type: "passage" (文档) 或 "query" (查询)
        
        Returns:
            List[float]: embedding向量
        """
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=self.model,
                encoding_format="float",
                extra_body={
                    "input_type": input_type,
                    "truncate": "NONE"
                }
            )
            embedding = response.data[0].embedding
            print(f"✅ Generated embedding, dimension: {len(embedding)}")
            return embedding
        except Exception as e:
            print(f"❌ Embedding generation failed: {str(e)}")
            raise
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        input_type: str = "passage"
    ) -> List[List[float]]:
        """
        批量生成embedding
        
        Args:
            texts: 文本列表
            input_type: "passage" 或 "query"
        
        Returns:
            List[List[float]]: embedding向量列表
        """
        embeddings = []
        for i, text in enumerate(texts):
            print(f"🔄 Processing {i+1}/{len(texts)}")
            embedding = self.generate_embedding(text, input_type)
            embeddings.append(embedding)
        return embeddings
    
    def health_check(self) -> dict:
        """健康检查：测试embedding服务是否正常"""
        try:
            test_embedding = self.generate_embedding("health check test", "query")
            return {
                "status": "healthy",
                "environment": settings.ENVIRONMENT,
                "base_url": self.base_url,
                "model": self.model,
                "embedding_dimension": len(test_embedding)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "environment": settings.ENVIRONMENT,
                "error": str(e)
            }

# 全局实例
embedding_service = EmbeddingService()