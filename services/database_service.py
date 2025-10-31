# 数据库服务
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from config import settings
import boto3
from botocore.exceptions import ClientError
import numpy as np
from schemas import MemoryUnit, SearchResult

class DatabaseService:
    """
    数据库服务 - 管理记忆单元的存储和检索
    使用 DynamoDB 存储元数据，S3 存储大文件，本地存储向量（生产环境可集成 Pinecone/Weaviate）
    """
    
    def __init__(self):
        # 检查AWS配置
        if (not settings.AWS_ACCESS_KEY_ID or 
            settings.AWS_ACCESS_KEY_ID == "your_aws_access_key_here" or
            not settings.S3_BUCKET_NAME or
            settings.S3_BUCKET_NAME == "your-s3-bucket-name"):
            raise ValueError("AWS配置未完成，请设置AWS_ACCESS_KEY_ID、AWS_SECRET_ACCESS_KEY和S3_BUCKET_NAME环境变量")
        
        # DynamoDB 客户端
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # 表名
        self.memories_table_name = f"unimem-memories-{settings.ENVIRONMENT}"
        self.embeddings_table_name = f"unimem-embeddings-{settings.ENVIRONMENT}"
        
        # 初始化表
        self.dynamodb_disabled = False
        self._init_tables()
        
        # 内存中的向量存储（用于快速搜索）
        self.vector_store = {}
        
        # 从DynamoDB加载现有向量到内存
        self._load_vectors_to_memory()
    
    def _init_tables(self):
        """初始化 DynamoDB 表"""
        try:
            # 检查表是否存在
            try:
                self.dynamodb.Table(self.memories_table_name).load()
                print(f"📋 Table already exists: {self.memories_table_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # 表不存在，尝试创建
                    print(f"🔨 Creating table: {self.memories_table_name}")
                    memories_table = self.dynamodb.create_table(
                        TableName=self.memories_table_name,
                        KeySchema=[
                            {'AttributeName': 'id', 'KeyType': 'HASH'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'id', 'AttributeType': 'S'},
                            {'AttributeName': 'created_at', 'AttributeType': 'S'},
                            {'AttributeName': 'memory_type', 'AttributeType': 'S'}
                        ],
                        GlobalSecondaryIndexes=[
                            {
                                'IndexName': 'created_at_index',
                                'KeySchema': [
                                    {'AttributeName': 'created_at', 'KeyType': 'HASH'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            },
                            {
                                'IndexName': 'memory_type_index',
                                'KeySchema': [
                                    {'AttributeName': 'memory_type', 'KeyType': 'HASH'},
                                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                                ],
                                'Projection': {'ProjectionType': 'ALL'}
                            }
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    print(f"✅ Table created: {self.memories_table_name}")
                else:
                    print(f"❌ Error checking table {self.memories_table_name}: {e}")
                    raise
            
            # 检查向量存储表
            try:
                self.dynamodb.Table(self.embeddings_table_name).load()
                print(f"📋 Table already exists: {self.embeddings_table_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # 表不存在，尝试创建
                    print(f"🔨 Creating table: {self.embeddings_table_name}")
                    embeddings_table = self.dynamodb.create_table(
                        TableName=self.embeddings_table_name,
                        KeySchema=[
                            {'AttributeName': 'id', 'KeyType': 'HASH'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'id', 'AttributeType': 'S'}
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    print(f"✅ Table created: {self.embeddings_table_name}")
                else:
                    print(f"❌ Error checking table {self.embeddings_table_name}: {e}")
                    raise
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                print(f"⚠️  Access denied accessing DynamoDB. Please ensure your AWS user has DynamoDB permissions.")
                print(f"   Required permissions: CreateTable, DescribeTable, PutItem, GetItem, UpdateItem, DeleteItem, Query, Scan")
                print(f"   Or manually create tables: {self.memories_table_name}, {self.embeddings_table_name}")
                print(f"   Continuing without DynamoDB functionality...")
                self.dynamodb = None
                self.dynamodb_disabled = True
            else:
                print(f"❌ Error with tables: {e}")
                raise
    
    def _load_vectors_to_memory(self):
        """从DynamoDB加载向量到内存"""
        if self.dynamodb_disabled:
            print("⚠️  DynamoDB disabled, skipping vector loading")
            return
            
        try:
            vectors_table = self.dynamodb.Table(self.embeddings_table_name)
            response = vectors_table.scan()
            
            loaded_count = 0
            for item in response.get('Items', []):
                memory_id = item['id']
                decimal_embedding = item['embedding']
                
                # 将Decimal转换回浮点数
                float_embedding = [float(x) for x in decimal_embedding]
                
                # 存储到内存向量存储
                # ✅ 修复：添加user_id
                self.vector_store[memory_id] = {
                    'embedding': np.array(float_embedding),
                    'memory_id': memory_id,
                    'user_id': item.get('user_id')  # ✅ 添加这行！
                }
                loaded_count += 1
            
            print(f"✅ Loaded {loaded_count} vectors from DynamoDB to memory")
            
        except Exception as e:
            print(f"⚠️  Failed to load vectors from DynamoDB: {e}")
            # 不抛出异常，允许系统继续运行
    
    def create_memory(
        self,
        content: str,
        memory_type: str,
        embedding: List[float],
        user_id: str,
        metadata: Dict[str, Any] = None,
        source: str = None,
        summary: str = None,
        tags: List[str] = None
    ) -> str:
        """
        创建新的记忆单元
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型 (text, image, audio, document)
            embedding: 向量嵌入
            user_id: 用户ID
            metadata: 元数据
            source: 来源
            summary: 摘要
            tags: 标签
            
        Returns:
            str: 记忆ID
        """
        if self.dynamodb_disabled:
            print("⚠️  DynamoDB disabled, memory not persisted")
            return None
            
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # 准备记忆数据
        memory_data = {
            'id': memory_id,
            'user_id': user_id,
            'content': content,
            'memory_type': memory_type,
            'metadata': metadata or {},
            'created_at': now,
            'updated_at': now,
            'source': source,
            'summary': summary,
            'tags': tags or []
        }
        
        # 准备向量数据 - 将浮点数转换为Decimal
        from decimal import Decimal
        
        # 将embedding中的浮点数转换为Decimal
        decimal_embedding = [Decimal(str(float(x))) for x in embedding]
        
        vector_data = {
            'id': memory_id,
            'user_id': user_id,
            'embedding': decimal_embedding,  # 存储Decimal类型的向量
            'memory_id': memory_id,
            'created_at': now
        }
        
        # 存储到数据库
        try:
            # DynamoDB存储记忆元数据
            memories_table = self.dynamodb.Table(self.memories_table_name)
            memories_table.put_item(Item=memory_data)
            
            # DynamoDB存储向量数据
            vectors_table = self.dynamodb.Table(self.embeddings_table_name)
            vectors_table.put_item(Item=vector_data)
            
            # 同时存储到内存（用于快速搜索）
            self.vector_store[memory_id] = {
                'embedding': np.array(embedding),
                'memory_id': memory_id
            }
            
            print(f"✅ Memory created: {memory_id}")
            print(f"✅ Vector stored: {len(embedding)} dimensions")
            return memory_id
            
        except Exception as e:
            print(f"❌ Failed to create memory: {e}")
            raise
    
    def semantic_search(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        语义搜索
        
        Args:
            query_embedding: 查询向量
            user_id: 用户ID
            limit: 返回数量限制
            threshold: 相似度阈值
            
        Returns:
            List[Dict]: 搜索结果
        """
        import time
        start_time = time.time()
        
        query_vector = np.array(query_embedding)
        results = []
        
        # 计算相似度（使用余弦相似度）
        print(f"🔍 Searching in {len(self.vector_store)} vectors with threshold {threshold} for user {user_id}")
        
        for memory_id, vector_data in self.vector_store.items():
            # 检查是否属于当前用户
            if vector_data.get('user_id') != user_id:
                continue
                
            embedding = vector_data['embedding']
            
            # 计算余弦相似度
            similarity = np.dot(query_vector, embedding) / (
                np.linalg.norm(query_vector) * np.linalg.norm(embedding)
            )
            
            print(f"📊 Memory {memory_id[:8]}... similarity: {similarity:.4f}")
            
            if similarity >= threshold:
                # 获取记忆元数据
                memory = self.get_memory_by_id(memory_id)
                if memory and memory.get('user_id') == user_id:
                    results.append({
                        'memory': memory,
                        'similarity_score': float(similarity),
                        'search_time': time.time() - start_time
                    })
                    print(f"✅ Added result: {memory_id[:8]}... (similarity: {similarity:.4f})")
                else:
                    print(f"⚠️  Memory not found or not owned by user for {memory_id[:8]}...")
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return results[:limit]
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取记忆"""
        if self.dynamodb_disabled:
            return None
            
        try:
            table = self.dynamodb.Table(self.memories_table_name)
            response = table.get_item(Key={'id': memory_id})
            
            if 'Item' in response:
                return response['Item']
            return None
            
        except Exception as e:
            print(f"❌ Failed to get memory {memory_id}: {e}")
            return None
    
    def get_memories(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        memory_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取记忆列表"""
        if self.dynamodb_disabled:
            return []
            
        try:
            table = self.dynamodb.Table(self.memories_table_name)
            
            # 构建查询参数
            if memory_type:
                # 使用 GSI 查询
                response = table.query(
                    IndexName='memory_type_index',
                    KeyConditionExpression='memory_type = :mt',
                    FilterExpression='user_id = :user_id',
                    ExpressionAttributeValues={
                        ':mt': memory_type,
                        ':user_id': user_id
                    },
                    Limit=limit,
                    ScanIndexForward=False  # 按时间倒序
                )
            else:
                # 扫描表
                filter_expression = 'user_id = :user_id'
                expression_values = {':user_id': user_id}
                
                if start_date and end_date:
                    filter_expression += ' AND created_at BETWEEN :start AND :end'
                    expression_values[':start'] = start_date
                    expression_values[':end'] = end_date
                
                response = table.scan(
                    Limit=limit,
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=expression_values
                )
            
            memories = response.get('Items', [])
            
            # 按时间排序
            memories.sort(key=lambda x: x['created_at'], reverse=True)
            
            return memories[offset:offset + limit]
            
        except Exception as e:
            print(f"❌ Failed to get memories: {e}")
            return []
    
    def get_related_memories(
        self,
        memory_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """获取相关记忆"""
        # 获取当前记忆的向量
        if memory_id not in self.vector_store:
            return []
        
        current_embedding = self.vector_store[memory_id]['embedding']
        
        # 搜索相关记忆
        results = self.semantic_search(
            query_embedding=current_embedding.tolist(),
            limit=limit + 1,  # +1 因为会包含自己
            threshold=0.5
        )
        
        # 过滤掉自己
        related = [r for r in results if r['memory']['id'] != memory_id]
        
        return related[:limit]
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            # 删除记忆元数据
            memories_table = self.dynamodb.Table(self.memories_table_name)
            memories_table.delete_item(Key={'id': memory_id})
            
            # 删除向量数据
            vectors_table = self.dynamodb.Table(self.embeddings_table_name)
            vectors_table.delete_item(Key={'id': memory_id})
            
            # 从内存向量存储删除
            if memory_id in self.vector_store:
                del self.vector_store[memory_id]
            
            print(f"✅ Memory deleted: {memory_id}")
            print(f"✅ Vector deleted: {memory_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete memory {memory_id}: {e}")
            return False
    
    def get_search_stats(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        try:
            # DynamoDB存储模式
            table = self.dynamodb.Table(self.memories_table_name)
            response = table.scan(Select='COUNT')
            
            total_memories = response['Count']
            vector_count = len(self.vector_store)
            
            # 按类型统计
            type_stats = {}
            for memory_id in self.vector_store.keys():
                memory = self.get_memory_by_id(memory_id)
                if memory:
                    memory_type = memory.get('memory_type', 'unknown')
                    type_stats[memory_type] = type_stats.get(memory_type, 0) + 1
            
            return {
                'total_memories': total_memories,
                'vector_count': vector_count,
                'type_distribution': type_stats,
                'storage_mode': 'dynamodb',
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {
                'total_memories': 0,
                'vector_count': 0,
                'type_distribution': {},
                'storage_mode': 'dynamodb',
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if self.dynamodb_disabled:
            return {
                'status': 'degraded',
                'storage': 'disabled',
                'dynamodb': 'disabled',
                'vector_store': 'active',
                'total_memories': len(self.vector_store),
                'message': 'DynamoDB disabled due to permissions'
            }
            
        try:
            # 检查 DynamoDB 连接
            table = self.dynamodb.Table(self.memories_table_name)
            self.dynamodb.meta.client.describe_table(TableName=self.memories_table_name)
            
            return {
                'status': 'healthy',
                'storage': 'dynamodb',
                'dynamodb': 'connected',
                'vector_store': 'active',
                'total_memories': len(self.vector_store),
                'persistent_storage': 'enabled',
                'memory_type': 'long_term'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'storage': 'dynamodb',
                'error': str(e)
            }

# 全局实例
database_service = DatabaseService()

