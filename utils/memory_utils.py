# 记忆相关工具函数
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any
import numpy as np

def generate_memory_id() -> str:
    """生成唯一的记忆ID"""
    return str(uuid.uuid4())

def generate_content_hash(content: str) -> str:
    """生成内容哈希值用于去重"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def format_timestamp(timestamp: datetime = None) -> str:
    """格式化时间戳"""
    if timestamp is None:
        timestamp = datetime.utcnow()
    return timestamp.isoformat()

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # 计算余弦相似度
    similarity = np.dot(vec1, vec2) / (
        np.linalg.norm(vec1) * np.linalg.norm(vec2)
    )
    
    return float(similarity)

def create_memory_metadata(
    content: str,
    memory_type: str,
    source: str = None,
    tags: List[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """创建记忆元数据"""
    return {
        'content_hash': generate_content_hash(content),
        'memory_type': memory_type,
        'source': source,
        'tags': tags or [],
        'created_at': format_timestamp(),
        'updated_at': format_timestamp(),
        **kwargs
    }

def validate_memory_data(data: Dict[str, Any]) -> bool:
    """验证记忆数据格式"""
    required_fields = ['content', 'memory_type', 'embedding']
    
    for field in required_fields:
        if field not in data:
            return False
    
    # 验证embedding是数字列表
    if not isinstance(data['embedding'], list) or not all(
        isinstance(x, (int, float)) for x in data['embedding']
    ):
        return False
    
    return True

def merge_memory_metadata(
    existing: Dict[str, Any],
    new: Dict[str, Any]
) -> Dict[str, Any]:
    """合并记忆元数据"""
    merged = existing.copy()
    
    # 更新字段
    for key, value in new.items():
        if key == 'tags' and key in merged:
            # 合并标签
            merged[key] = list(set(merged[key] + value))
        elif key == 'updated_at':
            # 总是更新修改时间
            merged[key] = value
        else:
            merged[key] = value
    
    return merged
