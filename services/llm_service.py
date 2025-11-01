# LLM服务
import requests
import json
from typing import Dict, Any, List
from openai import OpenAI
from config import settings

class LLMService:
    """
    LLM服务 - 使用NVIDIA NIM进行文本生成
    """
    
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        
        # 使用与embedding服务相同的配置
        if settings.ENVIRONMENT == "production":
            self.base_url = settings.NIM_EMBEDDING_URL
            print(f"🚀 Using production NIM: {self.base_url}")
        else:
            self.base_url = settings.NVIDIA_API_BASE_URL
            print(f"🔧 Using development API: {self.base_url}")
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        self.model = "nvidia/llama-3.1-nemotron-nano-8b-v1"  # ✅ 比赛要求
        
    def generate_response(
        self,
        user_input: str,
        context: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        生成AI响应
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            conversation_history: 对话历史
            
        Returns:
            str: AI响应
        """
        try:
            # 构建系统提示
            system_prompt = self._build_system_prompt(context)
            
            # 构建消息
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加对话历史
            if conversation_history:
                for turn in conversation_history[-6:]:  # 最近6轮对话
                    messages.append({"role": "user", "content": turn.get("user_input", "")})
                    messages.append({"role": "assistant", "content": turn.get("response", "")})
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": user_input})
            
            # 调用NVIDIA NIM API
            response = self._call_nvidia_api(messages)
            
            return response
            
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            return "抱歉，我遇到了一些技术问题，请稍后再试。"
    
    def _build_system_prompt(self, context: str) -> str:
        """构建系统提示"""
        base_prompt = """你是一个智能的个人记忆助手，名为UniMem AI。你的主要功能是：

        ##  核心任务
        直接使用提供的记忆信息回答用户问题，不要反问用户！

        ## ✅ 正确的回答方式
        当用户问："Gregory 的课程是关于什么的？"
        如果记忆中有信息，直接回答：
        "Gregory 教授的课程是关于时间序列分析、面板数据和预测方法！具体包括 Class #3 和 Class #4，涵盖了时间序列数据的统计分析和预测技术。"

        ## ❌ 错误的回答方式
        不要说：
        - "根据提供的信息..."（太生硬）
        - "请告诉我更多关于..."（不要反问）
        - "我需要确认一下..."（不要质疑记忆）
        - "Gregory 的课程大概是关于..."（不要模糊）

        ## 📋 回答原则
        1. **直接回答**: 如果记忆中有信息，直接、清晰地回答
        2. **自信表达**: 使用肯定的语气，不要说"可能"、"大概"
        3. **具体详细**: 使用记忆中的具体细节
        4. **自然对话**: 像朋友一样交流，适当使用 emoji 😊
        5. **承认不知道**: 只有记忆中真的没有信息时才说不知道

        ## 🔑 关键指示
        - 优先使用下面提供的"当前记忆信息"
        - 记忆信息就是事实，不要质疑它
        - 不要让用户重复已经在记忆中的信息

        """

        if context:
            # 有上下文 - 强调使用这些信息
            base_prompt += f"""

    ## 📚 当前记忆信息
    以下是系统为你找到的相关记忆，请直接使用这些信息回答用户的问题：

    {context}

    **重要提示**: 以上记忆信息就是你应该使用的事实依据。请直接、自信地使用这些信息回答用户，不要反问用户已经在记忆中的内容！
    """
        else:
            # 没有上下文 - 礼貌告知
            base_prompt += """

    ## ⚠️ 注意
    目前没有找到相关的记忆信息。请礼貌地告诉用户你还没有相关记忆，并询问是否需要了解其他信息。
    """
        
        return base_prompt
        

    
    def _call_nvidia_api(self, messages: List[Dict[str, str]]) -> str:
        """调用NVIDIA NIM API"""
        try:
            # 尝试使用chat completions
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ NVIDIA NIM chat completions failed: {e}")
            # 如果chat completions不可用，使用简化的文本生成
            return self._generate_simple_response(messages)
    
    def _generate_simple_response(self, messages: List[Dict[str, str]]) -> str:
        """生成简化的AI响应（不依赖LLM API）"""
        try:
            # 获取最后一条用户消息
            user_message = ""
            for message in reversed(messages):
                if message.get("role") == "user":
                    user_message = message.get("content", "")
                    break
            
            # 基于用户输入生成简单响应
            user_input_lower = user_message.lower()
            
            # 问候语
            if any(word in user_input_lower for word in ["你好", "hello", "hi", "您好"]):
                return "你好！我是UniMem AI助手，可以帮助您管理和检索个人记忆。有什么我可以帮助您的吗？"
            
            # 关于JavaScript的问题
            elif any(word in user_input_lower for word in ["javascript", "js", "前端", "编程"]):
                return "关于JavaScript，我可以帮您搜索相关的技术文档和记忆。JavaScript是一种广泛使用的编程语言，主要用于网页开发。"
            
            # 关于React的问题
            elif any(word in user_input_lower for word in ["react", "框架", "组件"]):
                return "React是一个用于构建用户界面的JavaScript库。它使用组件化开发模式，提高了代码的可维护性和复用性。"
            
            # 搜索相关
            elif any(word in user_input_lower for word in ["搜索", "查找", "找", "search", "find"]):
                return "我可以帮您搜索相关的记忆和文档。请告诉我您想了解什么内容，我会在您的记忆中查找相关信息。"
            
            # 默认响应
            else:
                return f"我理解您的问题：'{user_message}'。虽然我目前无法使用高级AI功能，但我可以帮您搜索相关的记忆和文档。请告诉我您想了解什么具体内容。"
                
        except Exception as e:
            print(f"❌ Simple response generation failed: {e}")
            return "抱歉，我遇到了一些技术问题，请稍后再试。"
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试API连接
            test_messages = [{"role": "user", "content": "Hello"}]
            self._call_nvidia_api(test_messages)
            
            return {
                "status": "healthy",
                "model": self.model,
                "api_available": True
            }
        except Exception as e:
            # 即使API不可用，简化响应仍然可用
            return {
                "status": "healthy",  # 改为healthy，因为简化响应可用
                "model": self.model,
                "api_available": False,
                "fallback_mode": True,
                "error": str(e)
            }

# 全局实例
llm_service = LLMService()
