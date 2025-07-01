#!/usr/bin/env python3
"""
分析Token使用情况的示例脚本
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import db_manager


def analyze_token_usage():
    """分析Token使用情况"""
    print("=== Token使用情况分析 ===")
    
    # 获取成功的API调用记录
    calls = db_manager.get_api_calls(status='success', limit=100)
    
    if not calls:
        print("暂无成功的API调用记录")
        return
    
    # 统计token使用情况
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    calls_with_usage = 0
    
    for call in calls:
        if call['usage_info']:
            try:
                usage_info = json.loads(call['usage_info'])
                total_prompt_tokens += usage_info.get('prompt_tokens', 0)
                total_completion_tokens += usage_info.get('completion_tokens', 0)
                total_tokens += usage_info.get('total_tokens', 0)
                calls_with_usage += 1
            except:
                continue
    
    if calls_with_usage == 0:
        print("暂无token使用数据")
        return
    
    print(f"分析记录数: {calls_with_usage}")
    print(f"总提示词tokens: {total_prompt_tokens:,}")
    print(f"总完成tokens: {total_completion_tokens:,}")
    print(f"总tokens: {total_tokens:,}")
    print(f"平均每次调用tokens: {total_tokens/calls_with_usage:.1f}")
    print(f"提示词占比: {total_prompt_tokens/total_tokens*100:.1f}%")
    print(f"完成占比: {total_completion_tokens/total_tokens*100:.1f}%")


def analyze_token_by_service():
    """按服务分析Token使用情况"""
    print("\n=== 按服务分析Token使用情况 ===")
    
    calls = db_manager.get_api_calls(status='success', limit=100)
    
    if not calls:
        print("暂无成功的API调用记录")
        return
    
    # 按服务分组统计
    service_stats = {}
    
    for call in calls:
        service = call['service']
        if service not in service_stats:
            service_stats[service] = {
                'calls': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            }
        
        service_stats[service]['calls'] += 1
        
        if call['usage_info']:
            try:
                usage_info = json.loads(call['usage_info'])
                service_stats[service]['prompt_tokens'] += usage_info.get('prompt_tokens', 0)
                service_stats[service]['completion_tokens'] += usage_info.get('completion_tokens', 0)
                service_stats[service]['total_tokens'] += usage_info.get('total_tokens', 0)
            except:
                continue
    
    # 显示统计结果
    for service, stats in service_stats.items():
        if stats['total_tokens'] > 0:
            print(f"\n服务: {service}")
            print(f"  调用次数: {stats['calls']}")
            print(f"  总tokens: {stats['total_tokens']:,}")
            print(f"  平均每次tokens: {stats['total_tokens']/stats['calls']:.1f}")
            print(f"  提示词tokens: {stats['prompt_tokens']:,} ({stats['prompt_tokens']/stats['total_tokens']*100:.1f}%)")
            print(f"  完成tokens: {stats['completion_tokens']:,} ({stats['completion_tokens']/stats['total_tokens']*100:.1f}%)")


def show_recent_token_usage():
    """显示最近的Token使用情况"""
    print("\n=== 最近的Token使用情况 ===")
    
    calls = db_manager.get_api_calls(status='success', limit=10)
    
    for call in calls:
        print(f"\n时间: {call['created_at']}")
        print(f"服务: {call['service']} | 端点: {call['endpoint']}")
        print(f"耗时: {call['duration']:.2f}s")
        
        if call['usage_info']:
            try:
                usage_info = json.loads(call['usage_info'])
                print(f"Tokens: {usage_info.get('prompt_tokens', 0)}/{usage_info.get('completion_tokens', 0)}/{usage_info.get('total_tokens', 0)} (提示/完成/总计)")
                
                # 计算token效率
                if usage_info.get('total_tokens', 0) > 0:
                    efficiency = usage_info.get('completion_tokens', 0) / usage_info.get('total_tokens', 0) * 100
                    print(f"完成效率: {efficiency:.1f}%")
            except:
                print("(无法解析token使用数据)")
        else:
            print("(无token使用数据)")


def estimate_cost():
    """估算API调用成本"""
    print("\n=== 成本估算 ===")
    
    # 假设的token价格（以豆包为例，实际价格请查看官方文档）
    prompt_token_price = 0.0001  # 每1K tokens的价格
    completion_token_price = 0.0002  # 每1K tokens的价格
    
    calls = db_manager.get_api_calls(status='success', limit=1000)
    
    total_prompt_tokens = 0
    total_completion_tokens = 0
    
    for call in calls:
        if call['usage_info']:
            try:
                usage_info = json.loads(call['usage_info'])
                total_prompt_tokens += usage_info.get('prompt_tokens', 0)
                total_completion_tokens += usage_info.get('completion_tokens', 0)
            except:
                continue
    
    # 计算成本
    prompt_cost = (total_prompt_tokens / 1000) * prompt_token_price
    completion_cost = (total_completion_tokens / 1000) * completion_token_price
    total_cost = prompt_cost + completion_cost
    
    print(f"总提示词tokens: {total_prompt_tokens:,}")
    print(f"总完成tokens: {total_completion_tokens:,}")
    print(f"提示词成本: ${prompt_cost:.4f}")
    print(f"完成成本: ${completion_cost:.4f}")
    print(f"总成本: ${total_cost:.4f}")
    print(f"\n注意: 以上成本估算基于假设价格，实际价格请参考官方文档")


if __name__ == "__main__":
    analyze_token_usage()
    analyze_token_by_service()
    show_recent_token_usage()
    estimate_cost() 