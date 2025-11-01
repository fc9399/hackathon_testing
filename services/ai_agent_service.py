# AI Agent服务
from typing import List, Dict, Any, Optional
from datetime import datetime
from services.database_service import database_service
from services.embedding_service import embedding_service
from services.llm_service import llm_service
from utils.text_utils import clean_text, extract_keywords, generate_summary
from utils.memory_utils import calculate_similarity
import json

class AIAgentService:
    """
    AI Agent服务 - 基于记忆的推理和对话
    使用NVIDIA NIM LLM进行智能对话和记忆检索
    """
    
    def __init__(self):
        self.conversation_history = {}  # 改为字典存储对话历史
        self.max_context_memories = 5
        self.similarity_threshold = 0.1  # 降低阈值以找到更多相关记忆
    
    async def chat_with_memory(
        self,
        user_input: str,
        user_id: str,
        conversation_id: str = None,
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        基于记忆的对话
        
        Args:
            user_input: 用户输入
            user_id: 用户ID
            conversation_id: 对话ID
            use_memory: 是否使用记忆检索
            
        Returns:
            Dict: 对话响应
        """
        try:
            # 清理用户输入
            cleaned_input = clean_text(user_input)
            
            # 如果启用记忆检索，搜索相关记忆
            relevant_memories = []
            if use_memory:
                relevant_memories = await self._retrieve_relevant_memories(cleaned_input, user_id)
            
            # 构建上下文
            context = self._build_context(relevant_memories, conversation_id)
            
            # 生成响应（使用NVIDIA NIM LLM）
            response = await self._generate_response(cleaned_input, context, conversation_id)
            
            # 保存对话历史
            self._save_conversation_turn(user_input, response, conversation_id)
            
            # 如果响应中包含新信息，创建记忆
            if self._should_create_memory(response):
                await self._create_conversation_memory(user_input, response, user_id, conversation_id)
            
            return {
                'response': response,
                'conversation_id': conversation_id or f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'relevant_memories': relevant_memories,
                'context_used': len(relevant_memories),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Chat failed: {e}")
            return {
                'response': "抱歉，我遇到了一些问题，请稍后再试。",
                'conversation_id': conversation_id or f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'relevant_memories': [],
                'context_used': 0,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    async def _retrieve_relevant_memories(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        try:
            # 生成查询embedding
            query_embedding = embedding_service.generate_embedding(
                text=query,
                input_type="query"
            )
            
            # 搜索相关记忆
            search_results = database_service.semantic_search(
                query_embedding=query_embedding,
                user_id=user_id,
                limit=self.max_context_memories,
                threshold=self.similarity_threshold
            )
            
            return search_results
            
        except Exception as e:
            print(f"❌ Memory retrieval failed: {e}")
            return []
    
    def _build_context(self, memories: List[Dict[str, Any]], conversation_id: str = None) -> str:
        """构建对话上下文"""
        context_parts = []
        
        # 添加相关记忆
        if memories:
            context_parts.append("相关记忆:")
            for i, memory_data in enumerate(memories, 1):
                memory = memory_data.get('memory', {})
                similarity = memory_data.get('similarity_score', 0)
                
                context_parts.append(
                    f"{i}. {memory.get('summary', memory.get('content', ''))[:100]}... "
                    f"(相似度: {similarity:.2f})"
                )
        
        # 添加对话历史
        if conversation_id and conversation_id in self.conversation_history:
            recent_turns = self.conversation_history[conversation_id][-3:]  # 最近3轮对话
            if recent_turns:
                context_parts.append("\n最近对话:")
                for turn in recent_turns:
                    context_parts.append(f"用户: {turn['user_input']}")
                    context_parts.append(f"助手: {turn['response']}")
        
        return "\n".join(context_parts)
    
    async def _generate_response(self, user_input: str, context: str, conversation_id: str = None) -> str:
        """生成AI响应（使用NVIDIA NIM LLM）"""
        try:
            # 获取对话历史
            conversation_history = []
            if conversation_id and conversation_id in self.conversation_history:
                conversation_history = self.conversation_history[conversation_id]
            
            # 使用LLM生成响应
            response = llm_service.generate_response(
                user_input=user_input,
                context=context,
                conversation_history=conversation_history
            )
            
            return response
            
        except Exception as e:
            print(f"❌ LLM response generation failed: {e}")
            # 回退到简化响应
            return await self._fallback_response(user_input, context)
    
    async def _fallback_response(self, user_input: str, context: str) -> str:
        """回退响应（当LLM不可用时）"""
        if context:
            return f"我理解您说的。根据我的记忆：\n\n{context}\n\n您还有什么想了解的吗？"
        else:
            return "我听到了您的话。虽然我没有相关的记忆，但我很乐意帮助您。您可以告诉我更多信息。"
    
    def _analyze_intent(self, user_input: str) -> str:
        """分析用户意图"""
        user_input_lower = user_input.lower()
        
        # 搜索相关关键词
        search_keywords = ['搜索', '查找', '找', 'search', 'find', 'look for']
        if any(keyword in user_input_lower for keyword in search_keywords):
            return "search"
        
        # 问题相关关键词
        question_keywords = ['什么', '怎么', '为什么', '如何', 'what', 'how', 'why', 'when', 'where']
        if any(keyword in user_input_lower for keyword in question_keywords):
            return "question"
        
        # 记忆相关关键词
        memory_keywords = ['记得', '记忆', '之前', 'remember', 'memory', 'before']
        if any(keyword in user_input_lower for keyword in memory_keywords):
            return "memory"
        
        return "general"
    
    async def _handle_search_intent(self, user_input: str, context: str) -> str:
        """处理搜索意图"""
        if context:
            return f"根据我的记忆，我找到了以下相关信息：\n\n{context}\n\n这些信息可能对您有帮助。"
        else:
            return "我没有找到与您搜索内容相关的记忆。您可以上传一些文档或记录，让我学习更多信息。"
    
    async def _handle_question_intent(self, user_input: str, context: str) -> str:
        """处理问题意图"""
        if context:
            return f"基于我的记忆，我可以回答您的问题：\n\n{context}\n\n如果您需要更详细的信息，请告诉我。"
        else:
            return "我目前没有足够的信息来回答您的问题。您可以提供更多背景信息或上传相关文档。"
    
    async def _handle_memory_intent(self, user_input: str, context: str) -> str:
        """处理记忆意图"""
        if context:
            return f"是的，我记得这些信息：\n\n{context}\n\n这些是我之前学习到的内容。"
        else:
            return "我没有找到相关的记忆。您可以告诉我更多信息，我会记住的。"
    
    async def _handle_general_intent(self, user_input: str, context: str) -> str:
        """处理一般意图"""
        if context:
            return f"我理解您说的。根据我的记忆：\n\n{context}\n\n您还有什么想了解的吗？"
        else:
            return "我听到了您的话。虽然我没有相关的记忆，但我很乐意帮助您。您可以告诉我更多信息。"
    
    def _should_create_memory(self, response: str) -> bool:
        """判断是否应该创建记忆"""
        # 如果响应包含新信息或用户提供了有价值的内容，创建记忆
        return len(response) > 50 and "记忆" not in response
    
    async def _create_conversation_memory(
        self,
        user_input: str,
        response: str,
        user_id: str,
        conversation_id: str = None
    ) -> str:
        """创建对话记忆"""
        try:
            # 组合用户输入和AI响应
            conversation_text = f"用户: {user_input}\n助手: {response}"
            
            # 生成embedding
            embedding = embedding_service.generate_embedding(
                text=conversation_text,
                input_type="passage"
            )
            
            # 创建记忆
            memory_id = database_service.create_memory(
                content=conversation_text,
                memory_type='conversation',
                embedding=embedding,
                user_id=user_id,
                metadata={
                    'conversation_id': conversation_id,
                    'user_input': user_input,
                    'ai_response': response,
                    'source': 'ai_agent'
                },
                source=f"conversation_{conversation_id}" if conversation_id else "ai_agent",
                summary=generate_summary(conversation_text, 100),
                tags=['conversation', 'ai_chat']
            )
            
            return memory_id
            
        except Exception as e:
            print(f"❌ Failed to create conversation memory: {e}")
            return None
    
    def _save_conversation_turn(
        self,
        user_input: str,
        response: str,
        conversation_id: str = None
    ):
        """保存对话轮次"""
        if not conversation_id:
            conversation_id = f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
        
        self.conversation_history[conversation_id].append({
            'user_input': user_input,
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # 限制历史长度
        if len(self.conversation_history[conversation_id]) > 20:
            self.conversation_history[conversation_id] = self.conversation_history[conversation_id][-20:]
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.conversation_history.get(conversation_id, [])
    
    async def clear_conversation_history(self, conversation_id: str = None):
        """清除对话历史"""
        if conversation_id:
            if conversation_id in self.conversation_history:
                del self.conversation_history[conversation_id]
        else:
            self.conversation_history.clear()
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        llm_health = llm_service.health_check()
        
        return {
            'status': 'healthy' if llm_health['status'] == 'healthy' else 'degraded',
            'active_conversations': len(self.conversation_history),
            'total_turns': sum(len(conv) for conv in self.conversation_history.values()),
            'max_context_memories': self.max_context_memories,
            'similarity_threshold': self.similarity_threshold,
            'llm_status': llm_health['status'],
            'llm_model': llm_health.get('model', 'unknown'),
            'llm_api_available': llm_health.get('api_available', False)
        }

# 全局实例
ai_agent_service = AIAgentService()
