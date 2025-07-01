#!/usr/bin/env python3
"""
查看API调用记录的示例脚本
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import db_manager


def view_api_calls():
    """查看API调用记录"""
    print("=== API调用记录查询 ===")
    
    # 获取最近的API调用记录
    calls = db_manager.get_api_calls(limit=10)
    
    if not calls:
        print("暂无API调用记录")
        return
    
    print(f"找到 {len(calls)} 条记录:")
    print("-" * 80)
    
    for call in calls:
        print(f"ID: {call['id']}")
        print(f"服务: {call['service']}")
        print(f"端点: {call['endpoint']}")
        print(f"状态: {call['status']}")
        print(f"耗时: {call['duration']:.2f}s")
        print(f"时间: {call['created_at']}")
        
        if call['request_data']:
            print("请求数据:")
            try:
                request_data = json.loads(call['request_data'])
                # 隐藏敏感信息
                if 'messages' in request_data:
                    for msg in request_data['messages']:
                        if msg.get('role') == 'user':
                            content = msg.get('content', '')
                            if len(content) > 100:
                                content = content[:100] + "..."
                            msg['content'] = content
                print(json.dumps(request_data, indent=2, ensure_ascii=False))
            except:
                print("(无法解析JSON)")
        
        if call['response_data']:
            print("响应数据:")
            try:
                response_data = json.loads(call['response_data'])
                # 只显示关键信息
                if 'choices' in response_data and response_data['choices']:
                    choice = response_data['choices'][0]
                    if 'message' in choice:
                        content = choice['message'].get('content', '')
                        if len(content) > 200:
                            content = content[:200] + "..."
                        print(f"响应内容: {content}")
                else:
                    print(json.dumps(response_data, indent=2, ensure_ascii=False))
            except:
                print("(无法解析JSON)")
        
        if call['usage_info']:
            print("Token使用情况:")
            try:
                usage_info = json.loads(call['usage_info'])
                print(f"  提示词tokens: {usage_info.get('prompt_tokens', 0)}")
                print(f"  完成tokens: {usage_info.get('completion_tokens', 0)}")
                print(f"  总tokens: {usage_info.get('total_tokens', 0)}")
            except:
                print("(无法解析usage信息)")
        
        if call['error_message']:
            print(f"错误信息: {call['error_message']}")
        
        print("-" * 80)


def view_successful_calls():
    """查看成功的API调用"""
    print("=== 成功的API调用记录 ===")
    
    calls = db_manager.get_api_calls(status='success', limit=5)
    
    if not calls:
        print("暂无成功的API调用记录")
        return
    
    for call in calls:
        print(f"服务: {call['service']} | 端点: {call['endpoint']} | 耗时: {call['duration']:.2f}s")
        
        if call['request_data']:
            try:
                request_data = json.loads(call['request_data'])
                if 'messages' in request_data:
                    user_msg = next((msg for msg in request_data['messages'] if msg.get('role') == 'user'), None)
                    if user_msg:
                        content = user_msg.get('content', '')
                        if len(content) > 100:
                            content = content[:100] + "..."
                        print(f"  请求: {content}")
            except:
                pass
        
        if call['response_data']:
            try:
                response_data = json.loads(call['response_data'])
                if 'choices' in response_data and response_data['choices']:
                    content = response_data['choices'][0]['message'].get('content', '')
                    if len(content) > 100:
                        content = content[:100] + "..."
                    print(f"  响应: {content}")
            except:
                pass
        
        if call['usage_info']:
            try:
                usage_info = json.loads(call['usage_info'])
                print(f"  Tokens: {usage_info.get('prompt_tokens', 0)}/{usage_info.get('completion_tokens', 0)}/{usage_info.get('total_tokens', 0)} (提示/完成/总计)")
            except:
                pass
        print()


def view_error_calls():
    """查看失败的API调用"""
    print("=== 失败的API调用记录 ===")
    
    calls = db_manager.get_api_calls(status='error', limit=5)
    
    if not calls:
        print("暂无失败的API调用记录")
        return
    
    for call in calls:
        print(f"服务: {call['service']} | 端点: {call['endpoint']} | 耗时: {call['duration']:.2f}s")
        
        if call['request_data']:
            try:
                request_data = json.loads(call['request_data'])
                if 'messages' in request_data:
                    user_msg = next((msg for msg in request_data['messages'] if msg.get('role') == 'user'), None)
                    if user_msg:
                        content = user_msg.get('content', '')
                        if len(content) > 100:
                            content = content[:100] + "..."
                        print(f"  请求: {content}")
            except:
                pass
        
        if call['error_message']:
            print(f"  错误: {call['error_message']}")
        print()


if __name__ == "__main__":
    view_api_calls()
    print("\n")
    view_successful_calls()
    print("\n")
    view_error_calls() 