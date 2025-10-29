#!/usr/bin/env python3
"""
UniMem AI系统完整测试脚本
测试所有核心功能是否正常工作
"""

import requests
import json
import time
import os
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8011"
TEST_FILE_PATH = "test_document.txt"

def print_header(title):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_result(success, message):
    """打印测试结果"""
    status = "✅ 成功" if success else "❌ 失败"
    print(f"{status}: {message}")

def test_health_check():
    """测试健康检查"""
    print_header("健康检查测试")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print_result(True, f"系统状态: {health_data['status']}")
            
            # 检查各个服务状态
            services = health_data.get('services', {})
            for service_name, service_data in services.items():
                status = service_data.get('status', 'unknown')
                print(f"  📊 {service_name}: {status}")
            
            return health_data['status'] == 'healthy'
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"连接失败: {e}")
        return False

def test_upload_text():
    """测试文本上传"""
    print_header("文本上传测试")
    
    test_text = """
    JavaScript是一种高级编程语言，主要用于网页开发。
    它具有以下特点：
    1. 动态类型语言
    2. 支持面向对象编程
    3. 可以运行在浏览器和服务器端
    4. 拥有丰富的生态系统
    
    React是一个用于构建用户界面的JavaScript库。
    它使用组件化开发模式，提高了代码的可维护性。
    """
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/upload/text",
            params={"text": test_text, "source": "test_script"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result(True, f"文本上传成功，创建了 {result.get('memories_created', 0)} 个记忆")
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"上传失败: {e}")
        return False

def test_semantic_search():
    """测试语义搜索"""
    print_header("语义搜索测试")
    
    test_queries = [
        "JavaScript的特点是什么？",
        "React是什么？",
        "编程语言有哪些类型？"
    ]
    
    success_count = 0
    for query in test_queries:
        try:
            response = requests.post(
                f"{BASE_URL}/api/search/semantic",
                json={
                    "query": query,
                    "limit": 3,
                    "threshold": 0.1
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                results_count = len(result.get('results', []))
                print(f"  🔍 查询: '{query}' -> 找到 {results_count} 个结果")
                
                if results_count > 0:
                    success_count += 1
                    # 显示第一个结果的部分内容
                    first_result = result['results'][0]
                    memory_content = first_result['memory']['content'][:100]
                    similarity = first_result['similarity_score']
                    print(f"    📄 最佳匹配: {memory_content}... (相似度: {similarity:.3f})")
            else:
                print(f"  ❌ 查询失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 查询异常: {e}")
    
    print_result(success_count > 0, f"成功完成 {success_count}/{len(test_queries)} 个查询")
    return success_count > 0

def test_ai_chat():
    """测试AI对话"""
    print_header("AI对话测试")
    
    test_messages = [
        "你好，请介绍一下你自己",
        "关于JavaScript，你能告诉我什么？",
        "什么是React？它有什么特点？"
    ]
    
    success_count = 0
    for i, message in enumerate(test_messages, 1):
        try:
            response = requests.post(
                f"{BASE_URL}/api/agent/chat",
                json={
                    "message": message,
                    "conversation_id": f"test_conversation_{i}",
                    "use_memory": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '')
                context_used = result.get('context_used', 0)
                
                print(f"  💬 用户: {message}")
                print(f"  🤖 AI: {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
                print(f"  📚 使用记忆: {context_used} 个")
                print()
                
                if ai_response and len(ai_response) > 10:
                    success_count += 1
            else:
                print(f"  ❌ 对话失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 对话异常: {e}")
    
    print_result(success_count > 0, f"成功完成 {success_count}/{len(test_messages)} 个对话")
    return success_count > 0

def test_memory_management():
    """测试记忆管理"""
    print_header("记忆管理测试")
    
    try:
        # 获取记忆列表
        response = requests.get(f"{BASE_URL}/api/search/memories?limit=5", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            total = result.get('total', 0)
            
            print_result(True, f"成功获取记忆列表，共 {total} 个记忆")
            
            if memories:
                print("  📋 最近的记忆:")
                for i, memory in enumerate(memories[:3], 1):
                    content = memory.get('content', '')[:100]
                    memory_type = memory.get('memory_type', 'unknown')
                    created_at = memory.get('created_at', 'unknown')
                    print(f"    {i}. [{memory_type}] {content}... ({created_at})")
            
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"获取记忆失败: {e}")
        return False

def test_conversation_history():
    """测试对话历史"""
    print_header("对话历史测试")
    
    try:
        response = requests.get(f"{BASE_URL}/api/agent/conversations", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            conversations = result.get('conversations', [])
            
            print_result(True, f"成功获取对话历史，共 {len(conversations)} 个对话")
            
            if conversations:
                print("  💭 最近的对话:")
                for i, conv in enumerate(conversations[:3], 1):
                    conv_id = conv.get('conversation_id', 'unknown')
                    turn_count = conv.get('turn_count', 0)
                    last_activity = conv.get('last_activity', 'unknown')
                    print(f"    {i}. {conv_id} ({turn_count} 轮对话) - {last_activity}")
            
            return True
        else:
            print_result(False, f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"获取对话历史失败: {e}")
        return False

def test_api_documentation():
    """测试API文档"""
    print_header("API文档测试")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        
        if response.status_code == 200:
            print_result(True, "API文档可访问")
            print(f"  📖 文档地址: {BASE_URL}/docs")
            return True
        else:
            print_result(False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"访问文档失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 UniMem AI系统完整测试")
    print("=" * 60)
    
    # 检查服务器是否运行
    print("🔍 检查服务器状态...")
    if not test_health_check():
        print("\n❌ 服务器未运行或健康检查失败！")
        print("请先启动服务器: python main.py")
        return
    
    # 执行所有测试
    tests = [
        ("文本上传", test_upload_text),
        ("语义搜索", test_semantic_search),
        ("AI对话", test_ai_chat),
        ("记忆管理", test_memory_management),
        ("对话历史", test_conversation_history),
        ("API文档", test_api_documentation),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    # 测试总结
    print_header("测试总结")
    print(f"📊 通过测试: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！UniMem AI系统运行正常！")
        print("\n🌟 系统功能确认:")
        print("  ✅ 健康检查正常")
        print("  ✅ 文本上传和解析")
        print("  ✅ 语义搜索")
        print("  ✅ AI智能对话")
        print("  ✅ 记忆管理")
        print("  ✅ 对话历史")
        print("  ✅ API文档")
        
        print(f"\n🌐 访问地址:")
        print(f"  📖 API文档: {BASE_URL}/docs")
        print(f"  🔍 健康检查: {BASE_URL}/health")
        print(f"  💬 AI对话: POST {BASE_URL}/api/agent/chat")
        print(f"  🔎 语义搜索: POST {BASE_URL}/api/search/semantic")
        
    else:
        print(f"⚠️  有 {total_tests - passed_tests} 个测试失败，请检查系统配置")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
