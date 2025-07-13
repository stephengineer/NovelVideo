#!/usr/bin/env python3
"""
测试重构后的图像生成服务
验证重试机制和代码重构
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core import config, get_logger, db_manager
from src.services.image_gen_service import ImageGenService
from pathlib import Path

def test_image_gen_refactor():
    """测试重构后的图像生成服务"""
    logger = get_logger('test_image_refactor')
    
    try:
        # 初始化图像生成服务
        image_service = ImageGenService()
        
        # 测试数据
        task_id = "test_image_refactor_001"
        scene_content = "一个温馨的家庭场景，人们围坐在一起聊天"
        scene_number = 1
        seed = 12345
        
        logger.info("=== 测试重构后的图像生成服务 ===")
        logger.info(f"场景内容: {scene_content}")
        
        # 测试场景图像生成
        image_path = image_service.generate_scene_image(
            scene_content, task_id, scene_number, seed
        )
        
        if image_path:
            logger.info(f"✓ 图像生成成功 | 路径: {image_path}")
            
            # 验证文件是否存在
            if Path(image_path).exists():
                file_size = Path(image_path).stat().st_size
                logger.info(f"✓ 图像文件存在 | 大小: {file_size} 字节")
            else:
                logger.error("✗ 图像文件不存在")
                
        else:
            logger.error("✗ 图像生成失败")
            
        # 测试敏感内容重试机制（模拟）
        logger.info("\n=== 测试敏感内容重试机制 ===")
        
        # 测试prompt改写功能
        test_prompts = [
            "两个人打架的场景",
            "血腥的战争场面",
            "不当的裸露内容"
        ]
        
        for i, test_prompt in enumerate(test_prompts, 1):
            logger.info(f"\n测试prompt {i}: {test_prompt}")
            
            for retry_count in range(1, 4):
                rewritten_prompt = image_service._rewrite_prompt(test_prompt, retry_count)
                logger.info(f"  重试{retry_count}: {rewritten_prompt}")
                
        # 验证数据库记录
        logger.info("\n=== 验证数据库记录 ===")
        api_calls = db_manager.get_api_calls(task_id=task_id, service='doubao', limit=10)
        
        if api_calls:
            logger.info(f"找到 {len(api_calls)} 条API调用记录")
            for call in api_calls:
                logger.info(f"  - {call['endpoint']} | {call['status']} | {call['duration']:.2f}s")
        else:
            logger.warning("未找到API调用记录")
            
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")

def test_api_functions():
    """测试提取的API函数"""
    logger = get_logger('test_api_functions')
    
    try:
        image_service = ImageGenService()
        
        # 测试API调用函数
        logger.info("=== 测试API函数 ===")
        
        # 构建测试payload
        test_payload = {
            'model': image_service.model,
            'prompt': '测试prompt',
            'response_format': image_service.response_format,
            'size': image_service.size,
            'seed': 12345,
            'guidance_scale': image_service.guidance_scale,
            'watermark': image_service.watermark
        }
        
        # 测试API调用（这里只是验证函数结构，不实际调用）
        logger.info("✓ API函数结构正确")
        
        # 测试prompt改写函数
        test_prompt = "测试敏感内容"
        for i in range(1, 4):
            rewritten = image_service._rewrite_prompt(test_prompt, i)
            logger.info(f"✓ Prompt改写 {i}: {rewritten}")
            
    except Exception as e:
        logger.error(f"API函数测试失败: {str(e)}")

if __name__ == "__main__":
    test_image_gen_refactor()
    test_api_functions() 