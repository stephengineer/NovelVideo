#!/usr/bin/env python3
"""
测试API调用记录功能
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import db_manager


def test_api_logging():
    """测试API调用记录功能"""
    print("=== 测试API调用记录功能 ===")
    
    # 模拟一个成功的API调用记录
    test_request = {
        "model": "doubao-seed-1.6-flash-250615",
        "messages": [
            {
                "role": "system",
                "content": "你是一位小说分析、解读专家"
            },
            {
                "role": "user",
                "content": "请分析这段小说内容..."
            }
        ]
    }
    
    test_response = {
        "choices": [
            {
                "message": {
                    "content": "{\"summary\": \"这是一个关于...\", \"scenes\": [...]}"
                }
            }
        ],
        "usage": {
            "completion_tokens": 461,
            "prompt_tokens": 661,
            "total_tokens": 1122
        }
    }
    
    # 记录测试API调用
    test_usage_info = {
        'completion_tokens': 461,
        'prompt_tokens': 661,
        'total_tokens': 1122
    }
    
    success = db_manager.log_api_call(
        service='doubao',
        endpoint='chat_completions',
        status='success',
        duration=2.5,
        request_data=test_request,
        response_data=test_response,
        usage_info=test_usage_info
    )
    
    if success:
        print("✓ 成功记录API调用")
    else:
        print("✗ 记录API调用失败")
    
    # 记录一个失败的API调用（包含请求数据）
    test_failed_request = {
        "model": "doubao-seed-1.6-flash-250615",
        "messages": [
            {
                "role": "system",
                "content": "你是一位小说分析、解读专家"
            },
            {
                "role": "user",
                "content": "请分析这段小说内容：这是一个测试请求..."
            }
        ]
    }
    
    success = db_manager.log_api_call(
        service='doubao',
        endpoint='chat_completions',
        status='error',
        duration=1.2,
        request_data=test_failed_request,
        error_message="API密钥无效"
    )
    
    if success:
        print("✓ 成功记录错误API调用")
    else:
        print("✗ 记录错误API调用失败")
    
    # 查询记录
    calls = db_manager.get_api_calls(limit=5)
    print(f"\n查询到 {len(calls)} 条API调用记录:")
    
    for call in calls:
        print(f"  - {call['service']}/{call['endpoint']}: {call['status']} ({call['duration']:.2f}s)")
        if call['request_data']:
            print(f"    有请求数据")
        if call['response_data']:
            print(f"    有响应数据")
        if call['usage_info']:
            try:
                usage_info = json.loads(call['usage_info'])
                print(f"    Tokens: {usage_info.get('prompt_tokens', 0)}/{usage_info.get('completion_tokens', 0)}/{usage_info.get('total_tokens', 0)}")
            except:
                print(f"    有token使用数据")
        if call['error_message']:
            print(f"    错误: {call['error_message']}")


if __name__ == "__main__":
    test_api_logging() 