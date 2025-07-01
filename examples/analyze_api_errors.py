#!/usr/bin/env python3
"""
分析API错误记录的示例脚本
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import db_manager


def analyze_recent_errors():
    """分析最近的API错误"""
    print("=== API错误分析 ===")
    
    # 获取最近24小时的错误记录
    calls = db_manager.get_api_calls(status='error', limit=50)
    
    if not calls:
        print("暂无API错误记录")
        return
    
    # 按服务分组统计
    service_stats = {}
    for call in calls:
        service = call['service']
        if service not in service_stats:
            service_stats[service] = {
                'count': 0,
                'total_duration': 0,
                'errors': []
            }
        
        service_stats[service]['count'] += 1
        service_stats[service]['total_duration'] += call['duration']
        service_stats[service]['errors'].append(call)
    
    # 显示统计信息
    for service, stats in service_stats.items():
        print(f"\n服务: {service}")
        print(f"  错误次数: {stats['count']}")
        print(f"  总耗时: {stats['total_duration']:.2f}s")
        print(f"  平均耗时: {stats['total_duration']/stats['count']:.2f}s")
        
        # 分析错误类型
        error_types = {}
        for error_call in stats['errors']:
            error_msg = error_call['error_message'] or "未知错误"
            error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        print("  错误类型分布:")
        for error_type, count in error_types.items():
            print(f"    - {error_type}: {count}次")


def analyze_specific_error():
    """分析特定错误的详细信息"""
    print("\n=== 详细错误分析 ===")
    
    # 获取最近的错误记录
    calls = db_manager.get_api_calls(status='error', limit=10)
    
    for call in calls:
        print(f"\n错误ID: {call['id']}")
        print(f"服务: {call['service']} | 端点: {call['endpoint']}")
        print(f"时间: {call['created_at']}")
        print(f"耗时: {call['duration']:.2f}s")
        print(f"错误: {call['error_message']}")
        
        if call['request_data']:
            print("请求数据:")
            try:
                request_data = json.loads(call['request_data'])
                
                # 显示模型信息
                if 'model' in request_data:
                    print(f"  模型: {request_data['model']}")
                
                # 显示消息内容
                if 'messages' in request_data:
                    print("  消息:")
                    for i, msg in enumerate(request_data['messages']):
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        if len(content) > 200:
                            content = content[:200] + "..."
                        print(f"    {i+1}. [{role}] {content}")
                
                # 显示其他参数
                other_params = {k: v for k, v in request_data.items() 
                              if k not in ['model', 'messages']}
                if other_params:
                    print("  其他参数:")
                    for k, v in other_params.items():
                        print(f"    {k}: {v}")
                        
            except json.JSONDecodeError:
                print("  (无法解析请求数据)")
        
        print("-" * 60)


def suggest_fixes():
    """根据错误记录提供修复建议"""
    print("\n=== 修复建议 ===")
    
    calls = db_manager.get_api_calls(status='error', limit=20)
    
    if not calls:
        print("暂无错误记录，无需修复建议")
        return
    
    # 分析常见错误
    common_errors = {}
    for call in calls:
        error_msg = call['error_message'] or "未知错误"
        if error_msg not in common_errors:
            common_errors[error_msg] = 0
        common_errors[error_msg] += 1
    
    print("常见错误及修复建议:")
    for error_msg, count in sorted(common_errors.items(), key=lambda x: x[1], reverse=True):
        print(f"\n错误: {error_msg} (出现{count}次)")
        
        if "API密钥" in error_msg or "401" in error_msg:
            print("  建议: 检查API密钥配置，确保密钥有效且权限正确")
        elif "网络" in error_msg or "连接" in error_msg:
            print("  建议: 检查网络连接，确认API服务地址可访问")
        elif "超时" in error_msg:
            print("  建议: 增加请求超时时间，或检查网络稳定性")
        elif "限流" in error_msg or "429" in error_msg:
            print("  建议: 降低请求频率，实现请求重试机制")
        elif "参数" in error_msg or "400" in error_msg:
            print("  建议: 检查请求参数格式，确保符合API要求")
        else:
            print("  建议: 查看API文档，确认请求格式正确")


if __name__ == "__main__":
    analyze_recent_errors()
    analyze_specific_error()
    suggest_fixes() 