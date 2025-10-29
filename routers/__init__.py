# 导出路由
from .upload import router as upload_router
from .embedding import router as embedding_router
from .search import router as search_router
from .ai_agent import router as ai_agent_router

__all__ = ['upload_router', 'embedding_router', 'search_router', 'ai_agent_router']