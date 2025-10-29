# 日期时间工具函数
from datetime import datetime, timedelta
from typing import Optional, Tuple
import re

def format_date_range(start_date: str, end_date: str) -> Tuple[Optional[str], Optional[str]]:
    """格式化日期范围"""
    try:
        # 解析开始日期
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            start_date = start_dt.isoformat()
        else:
            start_date = None
        
        # 解析结束日期
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            end_date = end_dt.isoformat()
        else:
            end_date = None
        
        return start_date, end_date
        
    except ValueError:
        return None, None

def parse_relative_date(relative_str: str) -> Optional[datetime]:
    """解析相对日期字符串"""
    if not relative_str:
        return None
    
    now = datetime.utcnow()
    relative_str = relative_str.lower().strip()
    
    # 今天
    if relative_str in ['today', '今天']:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 昨天
    if relative_str in ['yesterday', '昨天']:
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 本周
    if relative_str in ['this week', '本周']:
        days_since_monday = now.weekday()
        return (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 上周
    if relative_str in ['last week', '上周']:
        days_since_monday = now.weekday()
        last_monday = now - timedelta(days=days_since_monday + 7)
        return last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 本月
    if relative_str in ['this month', '本月']:
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 上月
    if relative_str in ['last month', '上月']:
        if now.month == 1:
            return now.replace(year=now.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return now.replace(month=now.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 解析 "N days ago" 格式
    days_ago_match = re.search(r'(\d+)\s*days?\s*ago', relative_str)
    if days_ago_match:
        days = int(days_ago_match.group(1))
        return now - timedelta(days=days)
    
    # 解析 "N weeks ago" 格式
    weeks_ago_match = re.search(r'(\d+)\s*weeks?\s*ago', relative_str)
    if weeks_ago_match:
        weeks = int(weeks_ago_match.group(1))
        return now - timedelta(weeks=weeks)
    
    # 解析 "N months ago" 格式
    months_ago_match = re.search(r'(\d+)\s*months?\s*ago', relative_str)
    if months_ago_match:
        months = int(months_ago_match.group(1))
        # 简化处理：按30天计算
        return now - timedelta(days=months * 30)
    
    return None

def get_time_range_filters(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    relative_period: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """获取时间范围过滤条件"""
    
    # 如果提供了相对期间，优先使用
    if relative_period:
        relative_start = parse_relative_date(relative_period)
        if relative_start:
            return relative_start.isoformat(), None
    
    # 否则使用提供的日期范围
    return format_date_range(start_date or "", end_date or "")

def format_timestamp_for_display(timestamp: str) -> str:
    """格式化时间戳用于显示"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return timestamp

def get_relative_time_description(timestamp: str) -> str:
    """获取相对时间描述"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 0:
            if diff.days == 1:
                return "昨天"
            elif diff.days < 7:
                return f"{diff.days}天前"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks}周前"
            elif diff.days < 365:
                months = diff.days // 30
                return f"{months}个月前"
            else:
                years = diff.days // 365
                return f"{years}年前"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}小时前"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}分钟前"
        else:
            return "刚刚"
            
    except ValueError:
        return "未知时间"

def is_within_time_range(
    timestamp: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> bool:
    """检查时间戳是否在指定范围内"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if dt < start_dt:
                return False
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if dt > end_dt:
                return False
        
        return True
        
    except ValueError:
        return False
