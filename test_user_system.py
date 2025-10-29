#!/usr/bin/env python3
"""
用户系统测试脚本
测试用户注册、登录、文件隔离等功能
"""

import requests
import json
import time
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8012"
API_BASE = f"{BASE_URL}/api"

class UserSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_server_health(self) -> bool:
        """测试服务器健康状态"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                self.log_test("服务器健康检查", True, "服务器运行正常")
                return True
            else:
                self.log_test("服务器健康检查", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("服务器健康检查", False, f"连接失败: {str(e)}")
            return False
    
    def test_user_registration(self) -> bool:
        """测试用户注册"""
        try:
            user_data = {
                "username": f"testuser_{int(time.time())}",
                "email": f"test_{int(time.time())}@example.com",
                "password": "testpassword123",
                "full_name": "Test User"
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/register",
                json=user_data
            )
            
            if response.status_code == 201:
                user_info = response.json()
                self.user_id = user_info.get("id")
                self.log_test("用户注册", True, f"用户ID: {self.user_id}")
                return True
            else:
                self.log_test("用户注册", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_test("用户注册", False, f"异常: {str(e)}")
            return False
    
    def test_user_login(self) -> bool:
        """测试用户登录"""
        try:
            login_data = {
                "username": f"testuser_{int(time.time())}",
                "password": "testpassword123"
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                token_info = response.json()
                self.access_token = token_info.get("access_token")
                self.log_test("用户登录", True, "获取访问令牌成功")
                return True
            else:
                self.log_test("用户登录", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_test("用户登录", False, f"异常: {str(e)}")
            return False
    
    def test_authenticated_request(self) -> bool:
        """测试需要认证的请求"""
        if not self.access_token:
            self.log_test("认证请求测试", False, "没有访问令牌")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{API_BASE}/auth/me",
                headers=headers
            )
            
            if response.status_code == 200:
                user_info = response.json()
                self.log_test("认证请求测试", True, f"获取用户信息: {user_info.get('username')}")
                return True
            else:
                self.log_test("认证请求测试", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("认证请求测试", False, f"异常: {str(e)}")
            return False
    
    def test_text_upload_with_auth(self) -> bool:
        """测试带认证的文本上传"""
        if not self.access_token:
            self.log_test("文本上传测试", False, "没有访问令牌")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {
                "text": "这是一个测试文本，用于验证用户隔离功能。",
                "source": "test_script"
            }
            
            response = self.session.post(
                f"{API_BASE}/upload/text",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("文本上传测试", True, f"记忆ID: {result.get('memory_id')}")
                return True
            else:
                self.log_test("文本上传测试", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_test("文本上传测试", False, f"异常: {str(e)}")
            return False
    
    def test_semantic_search_with_auth(self) -> bool:
        """测试带认证的语义搜索"""
        if not self.access_token:
            self.log_test("语义搜索测试", False, "没有访问令牌")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            search_data = {
                "query": "测试文本",
                "limit": 5,
                "threshold": 0.5
            }
            
            response = self.session.post(
                f"{API_BASE}/search/semantic",
                headers=headers,
                json=search_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("语义搜索测试", True, f"找到 {result.get('total', 0)} 个结果")
                return True
            else:
                self.log_test("语义搜索测试", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_test("语义搜索测试", False, f"异常: {str(e)}")
            return False
    
    def test_ai_chat_with_auth(self) -> bool:
        """测试带认证的AI对话"""
        if not self.access_token:
            self.log_test("AI对话测试", False, "没有访问令牌")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            chat_data = {
                "message": "你好，请介绍一下你自己",
                "use_memory": True
            }
            
            response = self.session.post(
                f"{API_BASE}/agent/chat",
                headers=headers,
                json=chat_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("AI对话测试", True, f"对话ID: {result.get('conversation_id')}")
                return True
            else:
                self.log_test("AI对话测试", False, f"状态码: {response.status_code}, 响应: {response.text}")
                return False
        except Exception as e:
            self.log_test("AI对话测试", False, f"异常: {str(e)}")
            return False
    
    def test_unauthorized_access(self) -> bool:
        """测试未授权访问"""
        try:
            # 不带认证头访问受保护的端点
            response = self.session.get(f"{API_BASE}/search/memories")
            
            if response.status_code == 401:
                self.log_test("未授权访问测试", True, "正确拒绝未授权访问")
                return True
            else:
                self.log_test("未授权访问测试", False, f"应该返回401，实际返回: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("未授权访问测试", False, f"异常: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始用户系统测试...")
        print("=" * 50)
        
        # 基础测试
        if not self.test_server_health():
            print("❌ 服务器不可用，停止测试")
            return
        
        # 用户认证测试
        if not self.test_user_registration():
            print("❌ 用户注册失败，停止测试")
            return
        
        if not self.test_user_login():
            print("❌ 用户登录失败，停止测试")
            return
        
        # 认证功能测试
        self.test_authenticated_request()
        self.test_text_upload_with_auth()
        self.test_semantic_search_with_auth()
        self.test_ai_chat_with_auth()
        
        # 安全测试
        self.test_unauthorized_access()
        
        # 输出测试结果
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"✅ 通过: {passed}/{total}")
        print(f"❌ 失败: {total - passed}/{total}")
        
        if passed == total:
            print("🎉 所有测试通过！用户系统工作正常。")
        else:
            print("⚠️  部分测试失败，请检查配置。")
        
        print("\n详细结果:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")

def main():
    """主函数"""
    print("🚀 UniMem AI 用户系统测试")
    print("确保服务器正在运行在 http://localhost:8012")
    print()
    
    tester = UserSystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
