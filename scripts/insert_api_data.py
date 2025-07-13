#!/usr/bin/env python3
"""
API调用记录数据插入脚本
专门用于向数据库中插入API调用记录，用于测试和演示
"""

import sys
import os
import time
import random
import json
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import db_manager, get_logger

def generate_realistic_api_data():
    """生成真实的API调用数据"""
    logger = get_logger('insert_api_data')
    
    # 真实的API调用场景
    api_scenarios = [
        # 小说分析场景
        {
            "task_id": "novel_analysis_001",
            "service": "doubao",
            "api_type": "analyze_novel",
            "request_data": {
                "model": "doubao-pro",
                "messages": [
                    {"role": "system", "content": "你是一位小说分析、解读专家"},
                    {"role": "user", "content": "分析给定的小说内容，并生成详细的分镜脚本..."}
                ],
                "thinking": {"type": "auto"},
                "max_tokens": 4000,
                "temperature": 0.7
            },
            "response_data": {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "summary": "这是一个关于友情和成长的故事",
                            "style": "温馨感人",
                            "scenes": [
                                {"scene_number": 1, "scene_content": "主角在公园里散步", "scene_description": "宁静的公园场景"}
                            ]
                        })
                    }
                }],
                "usage": {"completion_tokens": 150, "prompt_tokens": 200, "total_tokens": 350}
            },
            "duration": 2.5,
            "status": "success"
        },
        
        # 图像生成场景 - 成功
        {
            "task_id": "image_gen_001",
            "service": "doubao",
            "api_type": "image_generate",
            "request_data": {
                "model": "doubao-image",
                "prompt": "美丽的自然风景，山川河流，8K超高清",
                "response_format": "url",
                "size": "1024x1024",
                "seed": 12345,
                "guidance_scale": 7.5
            },
            "response_data": {
                "data": [{"url": "https://example.com/generated_image_001.jpg"}],
                "usage": {"total_tokens": 100}
            },
            "duration": 8.2,
            "status": "success"
        },
        
        # 图像生成场景 - 敏感内容错误
        {
            "task_id": "image_gen_002",
            "service": "doubao",
            "api_type": "image_generate",
            "request_data": {
                "model": "doubao-image",
                "prompt": "暴力打架场景，血腥场面",
                "response_format": "url",
                "size": "1024x1024",
                "seed": 54321,
                "guidance_scale": 7.5
            },
            "response_data": {
                "error": {
                    "code": "SensitiveContent",
                    "message": "检测到敏感内容，请修改提示词"
                }
            },
            "duration": 1.8,
            "status": "error",
            "error_message": "检测到敏感内容，请修改提示词"
        },
        
        # 图像生成场景 - 重试成功
        {
            "task_id": "image_gen_002",
            "service": "doubao",
            "api_type": "image_generate",
            "request_data": {
                "model": "doubao-image",
                "prompt": "人物对峙场景，艺术风格，适合全年龄段",
                "response_format": "url",
                "size": "1024x1024",
                "seed": 54321,
                "guidance_scale": 7.5
            },
            "response_data": {
                "data": [{"url": "https://example.com/generated_image_002.jpg"}],
                "usage": {"total_tokens": 120}
            },
            "duration": 7.5,
            "status": "success"
        },
        
        # 视频生成场景
        {
            "task_id": "video_gen_001",
            "service": "doubao",
            "api_type": "video_generate",
            "request_data": {
                "model": "doubao-video-pro",
                "content": [{
                    "type": "text",
                    "text": "一个人在公园里散步，温馨场景 --rs 1024 --seed 12345 --rt 16:9"
                }]
            },
            "response_data": {
                "id": "video_task_001",
                "status": "completed",
                "content": {"video_url": "https://example.com/generated_video_001.mp4"},
                "usage": {"completion_tokens": 200, "total_tokens": 250}
            },
            "duration": 45.2,
            "status": "success"
        },
        
        # Prompt改写场景
        {
            "task_id": "prompt_rewrite_001",
            "service": "doubao",
            "api_type": "prompt_rewrite",
            "request_data": {
                "model": "doubao-pro",
                "messages": [
                    {"role": "system", "content": "你是一个专业的图像描述改写助手，擅长将敏感内容改写为适合图像生成的安全版本。"},
                    {"role": "user", "content": "请将以下图像描述改写为适合图像生成的安全版本，避免敏感内容：原始描述：暴力打架场景..."}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            "response_data": {
                "choices": [{"message": {"content": "人物对峙场景，艺术风格，适合全年龄段观看"}}],
                "usage": {"completion_tokens": 30, "prompt_tokens": 80, "total_tokens": 110}
            },
            "duration": 1.2,
            "status": "success"
        },
        
        # TTS场景
        {
            "task_id": "tts_001",
            "service": "tts",
            "api_type": "text_to_speech",
            "request_data": {
                "text": "这是一个测试的语音合成内容",
                "voice": "zh-CN-XiaoxiaoNeural",
                "rate": 1.0,
                "volume": 1.0
            },
            "response_data": {
                "audio_url": "https://example.com/tts_audio_001.wav",
                "audio_duration": 3.5,
                "audio_words": "这是一个测试的语音合成内容"
            },
            "duration": 2.8,
            "status": "success"
        }
    ]
    
    return api_scenarios

def insert_api_records():
    """插入API调用记录"""
    logger = get_logger('insert_api_data')
    
    try:
        scenarios = generate_realistic_api_data()
        
        logger.info("开始插入API调用记录...")
        
        for i, scenario in enumerate(scenarios):
            # 添加一些时间变化
            timestamp = datetime.now() - timedelta(
                hours=random.randint(0, 24),
                minutes=random.randint(0, 59)
            )
            
            # 插入记录
            db_manager.log_api_call(
                task_id=scenario["task_id"],
                service=scenario["service"],
                api_type=scenario["api_type"],
                status=scenario["status"],
                duration=scenario["duration"],
                error_message=scenario.get("error_message"),
                request_data=scenario["request_data"],
                response_data=scenario["response_data"],
                usage_info=scenario["response_data"].get("usage") if scenario["status"] == "success" else None
            )
            
            logger.info(f"插入第{i+1}条记录: {scenario['task_id']} - {scenario['api_type']}")
            
            # 添加延迟
            time.sleep(0.1)
        
        logger.info(f"成功插入{len(scenarios)}条API调用记录")
        
    except Exception as e:
        logger.error(f"插入API记录失败: {str(e)}")

def insert_batch_api_records():
    """插入批量API调用记录（用于性能测试）"""
    logger = get_logger('insert_api_data')
    
    try:
        logger.info("开始插入批量API调用记录...")
        
        # 生成批量数据
        batch_size = 20
        services = ['doubao', 'tts']
        api_types = ['chat_completions', 'image_generate', 'video_generate']
        statuses = ['success', 'error']
        
        for i in range(batch_size):
            task_id = f"batch_test_{i+1:03d}"
            service = random.choice(services)
            api_type = random.choice(api_types)
            status = random.choice(statuses)
            duration = random.uniform(0.5, 15.0)
            
            # 生成简单的请求和响应数据
            request_data = {
                "model": f"{service}-model",
                "prompt": f"测试prompt {i+1}",
                "temperature": 0.7
            }
            
            if status == 'success':
                response_data = {
                    "choices": [{"message": {"content": f"测试响应 {i+1}"}}],
                    "usage": {
                        "completion_tokens": random.randint(20, 100),
                        "prompt_tokens": random.randint(50, 200),
                        "total_tokens": random.randint(70, 300)
                    }
                }
                error_message = None
                usage_info = response_data["usage"]
            else:
                response_data = {
                    "error": {
                        "code": "TestError",
                        "message": f"测试错误 {i+1}"
                    }
                }
                error_message = f"测试错误 {i+1}"
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
            
            if (i + 1) % 5 == 0:
                logger.info(f"已插入 {i+1}/{batch_size} 条记录")
        
        logger.info(f"成功插入{batch_size}条批量API调用记录")
        
    except Exception as e:
        logger.error(f"插入批量API记录失败: {str(e)}")

def main():
    """主函数"""
    logger = get_logger('insert_api_data')
    
    logger.info("开始插入API调用记录数据...")
    
    try:
        # 插入真实场景数据
        insert_api_records()
        
        # 插入批量测试数据
        insert_batch_api_records()
        
        logger.info("所有API调用记录数据插入完成！")
        
    except Exception as e:
        logger.error(f"插入API调用记录数据失败: {str(e)}")

if __name__ == "__main__":
    main() 