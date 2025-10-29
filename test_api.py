#!/usr/bin/env python3
"""
UniMem AI API 测试脚本
"""
import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查错误: {e}")

def test_upload_text():
    """测试文本上传"""
    print("\n📝 测试文本上传...")
    try:
        params = {
            "text": "这是一个测试记忆，用于验证系统功能。",
            "source": "test_script"
        }
        response = requests.post(f"{BASE_URL}/api/upload/text", params=params)
        if response.status_code == 200:
            print("✅ 文本上传成功")
            result = response.json()
            print(f"   记忆ID: {result['memory_id']}")
            return result['memory_id']
        else:
            print(f"❌ 文本上传失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 文本上传错误: {e}")
    return None

def test_search(memory_id):
    """测试搜索功能"""
    print("\n🔍 测试搜索功能...")
    try:
        data = {
            "query": "测试记忆",
            "limit": 5,
            "threshold": 0.5
        }
        response = requests.post(f"{BASE_URL}/api/search/semantic", json=data)
        if response.status_code == 200:
            print("✅ 搜索成功")
            result = response.json()
            print(f"   找到 {result['total']} 个相关记忆")
            for i, memory in enumerate(result['results'][:3], 1):
                print(f"   {i}. {memory['memory']['content'][:50]}...")
        else:
            print(f"❌ 搜索失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 搜索错误: {e}")

def test_chat():
    """测试AI对话"""
    print("\n💬 测试AI对话...")
    try:
        data = {
            "message": "你好，你能记住我刚才上传的内容吗？",
            "use_memory": True
        }
        response = requests.post(f"{BASE_URL}/api/agent/chat", json=data)
        if response.status_code == 200:
            print("✅ 对话成功")
            result = response.json()
            print(f"   AI回复: {result['response']}")
            print(f"   使用了 {result['context_used']} 个相关记忆")
        else:
            print(f"❌ 对话失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 对话错误: {e}")

def test_memories():
    """测试记忆列表"""
    print("\n📚 测试记忆列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/search/memories?limit=5")
        if response.status_code == 200:
            print("✅ 获取记忆列表成功")
            result = response.json()
            print(f"   总共有 {result['total']} 个记忆")
            for i, memory in enumerate(result['memories'][:3], 1):
                print(f"   {i}. {memory['content'][:50]}...")
        else:
            print(f"❌ 获取记忆列表失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 获取记忆列表错误: {e}")

def main():
    """主测试函数"""
    print("🧠 UniMem AI API 测试")
    print("=" * 50)
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    time.sleep(2)
    
    # 运行测试
    test_health()
    memory_id = test_upload_text()
    test_search(memory_id)
    test_chat()
    test_memories()
    
    print("\n🎉 测试完成！")
    print("📖 访问 http://localhost:8000/docs 查看API文档")

if __name__ == "__main__":
    main()
