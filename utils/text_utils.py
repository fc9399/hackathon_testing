# 文本处理工具函数
import re
import string
from typing import List, Dict, Any
from collections import Counter

def clean_text(text: str) -> str:
    """清理文本内容"""
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    
    # 移除特殊字符但保留基本标点
    text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
    
    # 去除首尾空白
    text = text.strip()
    
    return text

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """提取关键词"""
    if not text:
        return []
    
    # 转换为小写
    text = text.lower()
    
    # 移除标点符号
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # 分割单词
    words = text.split()
    
    # 过滤停用词（简化版）
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
        'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
    }
    
    # 过滤单词
    filtered_words = [
        word for word in words 
        if len(word) > 2 and word not in stop_words
    ]
    
    # 计算词频
    word_counts = Counter(filtered_words)
    
    # 返回最常见的词
    return [word for word, count in word_counts.most_common(max_keywords)]

def generate_summary(text: str, max_length: int = 200) -> str:
    """生成文本摘要"""
    if not text:
        return ""
    
    # 清理文本
    cleaned_text = clean_text(text)
    
    # 如果文本长度小于最大长度，直接返回
    if len(cleaned_text) <= max_length:
        return cleaned_text
    
    # 截断到最大长度并添加省略号
    summary = cleaned_text[:max_length].rstrip()
    
    # 确保不在单词中间截断
    last_space = summary.rfind(' ')
    if last_space > max_length * 0.8:  # 如果最后一个空格位置合理
        summary = summary[:last_space]
    
    return summary + "..."

def extract_entities(text: str) -> Dict[str, List[str]]:
    """提取实体（简化版）"""
    entities = {
        'emails': [],
        'urls': [],
        'phone_numbers': [],
        'dates': []
    }
    
    # 提取邮箱
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    entities['emails'] = re.findall(email_pattern, text)
    
    # 提取URL
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    entities['urls'] = re.findall(url_pattern, text)
    
    # 提取电话号码（简化版）
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    entities['phone_numbers'] = re.findall(phone_pattern, text)
    
    # 提取日期（简化版）
    date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
    entities['dates'] = re.findall(date_pattern, text)
    
    return entities

def calculate_text_similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度（基于词汇重叠）"""
    if not text1 or not text2:
        return 0.0
    
    # 清理文本
    clean_text1 = clean_text(text1).lower()
    clean_text2 = clean_text(text2).lower()
    
    # 分割为单词
    words1 = set(clean_text1.split())
    words2 = set(clean_text2.split())
    
    # 计算Jaccard相似度
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def format_text_for_embedding(text: str) -> str:
    """格式化文本用于embedding生成"""
    # 清理文本
    cleaned = clean_text(text)
    
    # 限制长度（大多数embedding模型有长度限制）
    max_length = 8000  # 保守估计
    
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned
