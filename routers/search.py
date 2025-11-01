# 搜索路由
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from services.database_service import database_service
from services.embedding_service import embedding_service
from services.auth_service import auth_service
from schemas import SearchRequest, SearchResponse, MemoryUnit, User
import json

router = APIRouter(prefix="/api/search", tags=["search"])

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
    """获取当前用户"""
    token = credentials.credentials
    token_data = auth_service.verify_token(token)
    user = await auth_service.get_user_by_username(token_data.username)
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(request: SearchRequest, current_user: User = Depends(get_current_user)):
    """
    语义搜索 - 在记忆库中搜索相关内容
    
    Example:
        POST /api/search/semantic
        {
            "query": "上周会议讨论了什么？",
            "limit": 10,
            "threshold": 0.7
        }
    """
    try:
        # 生成查询的embedding
        # 修改！同样的文本，passage和query的相似度只有0.3992，所以input_type改为passage
        query_embedding = embedding_service.generate_embedding(
            text=request.query,
            input_type="passage" # ← 改为 passage
        )
        
        # 在向量数据库中搜索
        search_results = database_service.semantic_search(
            query_embedding=query_embedding,
            user_id=current_user.id,
            limit=request.limit,
            threshold=request.threshold
        )
        
        # 计算总搜索时间
        total_search_time = 0
        if search_results:
            total_search_time = search_results[0].get("search_time", 0)
        
        return {
            "query": request.query,
            "results": search_results,
            "total": len(search_results),
            "search_time": total_search_time
        }
        
    except Exception as e:
        import traceback
        error_detail = f"Search failed: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(f"❌ Search error: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/memories")
async def get_memories(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    memory_type: Optional[str] = Query(None, description="过滤记忆类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD")
):
    """
    获取记忆列表 - 支持分页和过滤
    
    Parameters:
        limit: 返回数量限制
        offset: 偏移量
        memory_type: 记忆类型过滤 (text, image, audio, document)
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        memories = database_service.get_memories(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            memory_type=memory_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "memories": memories,
            "total": len(memories),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memories: {str(e)}")

@router.get("/memories/{memory_id}")
async def get_memory_by_id(memory_id: str):
    """
    根据ID获取特定记忆详情
    """
    try:
        memory = database_service.get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return memory
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory: {str(e)}")

@router.post("/memories/{memory_id}/related")
async def get_related_memories(
    memory_id: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user)  # ✅ 添加用户认证
):
    """
    获取相关记忆 - 基于语义相似度
    
    Parameters:
        memory_id: 记忆ID
        limit: 返回数量限制
        
    Returns:
        相关记忆列表
    """
    try:
        # 1. 验证记忆是否存在且属于当前用户
        memory = database_service.get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        if memory.get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 2. ✅ 获取相关记忆（传入 user_id）
        related_memories = database_service.get_related_memories(
            memory_id=memory_id,
            user_id=current_user.id,  # ✅ 传入 user_id
            limit=limit
        )
        
        return {
            "memory_id": memory_id,
            "related_memories": related_memories,
            "count": len(related_memories)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Failed to get related memories: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=f"Failed to get related memories: {str(e)}")

@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """
    删除记忆
    """
    try:
        success = database_service.delete_memory(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {
            "success": True,
            "message": f"Memory {memory_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")

@router.get("/stats")
async def get_search_stats():
    """
    获取搜索统计信息
    """
    try:
        stats = database_service.get_search_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/health")
async def search_health_check():
    """检查搜索服务健康状态"""
    return database_service.health_check()
