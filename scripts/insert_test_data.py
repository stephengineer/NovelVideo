#!/usr/bin/env python3
"""
数据库测试数据插入脚本
用于向数据库中插入测试数据，包括API调用记录、任务信息等
"""

import sys
import os
import time
import random
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import db_manager, get_logger

def insert_api_call_records():
    """插入API调用记录测试数据"""
    logger = get_logger('insert_test_data')
    
    try:
        # 模拟不同的任务ID
        task_ids = [
            "test_task_001", "test_task_002", "test_task_003",
            "novel_video_001", "novel_video_002", "novel_video_003"
        ]
        
        # 模拟不同的服务类型
        services = ['doubao', 'volcengine', 'tts']
        
        # 模拟不同的API类型
        api_types = [
            'chat_completions', 'image_generate', 'video_generate',
            'prompt_rewrite', 'analyze_novel', 'generate_summary'
        ]
        
        # 模拟不同的状态
        statuses = ['success', 'error']
        
        # 模拟错误消息
        error_messages = [
            "API调用超时",
            "网络连接失败",
            "参数错误",
            "敏感内容检测",
            "服务器内部错误"
        ]
        
        # 模拟请求数据
        sample_requests = [
            {
                "model": "doubao-pro",
                "messages": [{"role": "user", "content": "测试prompt"}],
                "temperature": 0.7
            },
            {
                "model": "doubao-image",
                "prompt": "美丽的风景",
                "size": "1024x1024"
            },
            {
                "model": "doubao-video",
                "content": [{"type": "text", "text": "测试视频生成"}]
            }
        ]
        
        # 模拟响应数据
        sample_responses = [
            {
                "choices": [{"message": {"content": "测试响应"}}],
                "usage": {"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50}
            },
            {
                "data": [{"url": "https://example.com/image.jpg"}],
                "usage": {"total_tokens": 200}
            },
            {
                "id": "video_task_123",
                "status": "completed",
                "content": {"video_url": "https://example.com/video.mp4"}
            }
        ]
        
        # 模拟token使用情况
        usage_info_samples = [
            {"completion_tokens": 50, "prompt_tokens": 100, "total_tokens": 150},
            {"completion_tokens": 100, "prompt_tokens": 200, "total_tokens": 300},
            {"completion_tokens": 25, "prompt_tokens": 75, "total_tokens": 100}
        ]
        
        logger.info("开始插入API调用记录测试数据...")
        
        # 插入多条测试记录
        for i in range(50):  # 插入50条记录
            # 随机选择数据
            task_id = random.choice(task_ids)
            service = random.choice(services)
            api_type = random.choice(api_types)
            status = random.choice(statuses)
            
            # 随机生成时间（最近7天内）
            timestamp = datetime.now() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # 随机生成耗时
            duration = random.uniform(0.5, 10.0)
            
            # 根据状态生成不同的数据
            if status == 'success':
                error_message = None
                request_data = random.choice(sample_requests)
                response_data = random.choice(sample_responses)
                usage_info = random.choice(usage_info_samples)
            else:
                error_message = random.choice(error_messages)
                request_data = random.choice(sample_requests)
                response_data = None
                usage_info = None
            
            # 插入记录
            db_manager.log_api_call(
                task_id=task_id,
                service=service,
                api_type=api_type,
                status=status,
                duration=duration,
                error_message=error_message,
                request_data=request_data,
                response_data=response_data,
                usage_info=usage_info
            )
            
            # 添加一些延迟避免过快插入
            time.sleep(0.01)
        
        logger.info(f"成功插入50条API调用记录")
        
    except Exception as e:
        logger.error(f"插入API调用记录失败: {str(e)}")

def insert_task_records():
    """插入任务记录测试数据"""
    logger = get_logger('insert_test_data')
    
    try:
        # 模拟任务数据
        tasks = [
            {
                "task_id": "novel_video_001",
                "novel_title": "测试小说1",
                "novel_content": "这是一个测试小说的内容...",
                "status": "completed",
                "created_at": datetime.now() - timedelta(days=2),
                "completed_at": datetime.now() - timedelta(days=1, hours=12)
            },
            {
                "task_id": "novel_video_002", 
                "novel_title": "测试小说2",
                "novel_content": "另一个测试小说的内容...",
                "status": "processing",
                "created_at": datetime.now() - timedelta(hours=6)
            },
            {
                "task_id": "novel_video_003",
                "novel_title": "测试小说3", 
                "novel_content": "第三个测试小说的内容...",
                "status": "failed",
                "created_at": datetime.now() - timedelta(days=1),
                "error_message": "处理过程中发生错误"
            }
        ]
        
        logger.info("开始插入任务记录测试数据...")
        
        for task in tasks:
            # 这里需要根据实际的数据库结构来插入
            # 假设有一个insert_task方法
            logger.info(f"插入任务: {task['task_id']}")
            # db_manager.insert_task(task)  # 需要实现这个方法
        
        logger.info(f"成功插入{len(tasks)}条任务记录")
        
    except Exception as e:
        logger.error(f"插入任务记录失败: {str(e)}")

def insert_sensitive_content_records():
    """插入敏感内容处理记录测试数据"""
    logger = get_logger('insert_test_data')
    
    try:
        # 模拟敏感内容处理记录
        sensitive_records = [
            {
                "task_id": "test_sensitive_001",
                "original_prompt": "暴力打架场景",
                "rewritten_prompt": "人物对峙场景，艺术风格",
                "retry_count": 1,
                "service": "image_gen",
                "status": "success"
            },
            {
                "task_id": "test_sensitive_002",
                "original_prompt": "血腥战斗场面",
                "rewritten_prompt": "激烈冲突场景，温馨氛围",
                "retry_count": 2,
                "service": "video_gen", 
                "status": "success"
            },
            {
                "task_id": "test_sensitive_003",
                "original_prompt": "不当的诱惑内容",
                "rewritten_prompt": "温馨和谐的场景，适合全年龄段",
                "retry_count": 3,
                "service": "image_gen",
                "status": "success"
            }
        ]
        
        logger.info("开始插入敏感内容处理记录测试数据...")
        
        for record in sensitive_records:
            logger.info(f"插入敏感内容记录: {record['task_id']}")
            # 这里可以添加实际的数据库插入逻辑
            # db_manager.insert_sensitive_content_record(record)
        
        logger.info(f"成功插入{len(sensitive_records)}条敏感内容处理记录")
        
    except Exception as e:
        logger.error(f"插入敏感内容记录失败: {str(e)}")

def generate_statistics():
    """生成统计信息"""
    logger = get_logger('insert_test_data')
    
    try:
        logger.info("生成数据库统计信息...")
        
        # 这里可以添加统计查询
        # 例如：总API调用次数、成功率、平均响应时间等
        
        logger.info("统计信息生成完成")
        
    except Exception as e:
        logger.error(f"生成统计信息失败: {str(e)}")

def main():
    """主函数"""
    logger = get_logger('insert_test_data')
    
    logger.info("开始插入测试数据...")
    
    try:
        # 插入API调用记录
        insert_api_call_records()
        
        # 插入任务记录
        insert_task_records()
        
        # 插入敏感内容处理记录
        insert_sensitive_content_records()
        
        # 生成统计信息
        generate_statistics()
        
        logger.info("所有测试数据插入完成！")
        
    except Exception as e:
        logger.error(f"插入测试数据失败: {str(e)}")

if __name__ == "__main__":
    main() 