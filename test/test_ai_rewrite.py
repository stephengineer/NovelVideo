#!/usr/bin/env python3
"""
测试AI模型改写功能
验证敏感prompt的智能改写
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core import config, get_logger
from src.services.doubao_service import DoubaoService

def test_ai_rewrite():
    """测试AI模型改写功能"""
    logger = get_logger('test_ai_rewrite')
    
    try:
        # 初始化豆包服务
        doubao_service = DoubaoService()
        
        # 测试敏感prompt
        test_prompts = [
            "两个人打架的场景，血腥暴力",
            "战争场面，死亡和破坏",
            "不当的裸露内容，性感诱惑",
            "政治冲突，种族歧视",
            "宗教极端主义，恐怖袭击"
        ]
        
        logger.info("=== 测试AI模型改写功能 ===")
        
        for i, original_prompt in enumerate(test_prompts, 1):
            logger.info(f"\n--- 测试 {i} ---")
            logger.info(f"原始prompt: {original_prompt}")
            
            # 测试三次重试的改写
            for retry_count in range(1, 4):
                logger.info(f"\n重试 {retry_count}:")
                
                # 测试AI模型改写
                rewritten_prompt = doubao_service.rewrite_prompt(original_prompt, retry_count, "test_task_001")
                logger.info(f"改写结果: {rewritten_prompt}")
                
                # 测试AI模型调用函数
                if retry_count == 1:  # 只测试第一次的AI调用
                    instruction = f"""
请将以下图像描述改写为适合图像生成的安全版本，避免敏感内容：
原始描述：{original_prompt}

要求：
1. 保持场景的核心内容和氛围
2. 将可能敏感的内容替换为更温和的表达
3. 添加艺术风格修饰，使其适合全年龄段
4. 保持描述的生动性和画面感

请直接返回改写后的描述，不要包含其他解释。
"""
                    
                    ai_result = doubao_service._call_rewrite_api(instruction, "test_task_001")
                    if ai_result:
                        logger.info(f"AI模型直接调用结果: {ai_result}")
                    else:
                        logger.warning("AI模型调用失败，使用备用方案")
                        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")

def test_fallback_rewrite():
    """测试备用改写方案"""
    logger = get_logger('test_fallback_rewrite')
    
    try:
        doubao_service = DoubaoService()
        
        test_prompts = [
            "暴力冲突场景",
            "不当内容描述",
            "敏感政治话题"
        ]
        
        logger.info("=== 测试备用改写方案 ===")
        
        for original_prompt in test_prompts:
            logger.info(f"\n原始prompt: {original_prompt}")
            
            for retry_count in range(1, 4):
                fallback_result = doubao_service._fallback_rewrite_prompt(original_prompt, retry_count)
                logger.info(f"备用方案重试{retry_count}: {fallback_result}")
                
    except Exception as e:
        logger.error(f"备用方案测试失败: {str(e)}")

def test_rewrite_strategies():
    """测试不同改写策略的效果"""
    logger = get_logger('test_rewrite_strategies')
    
    try:
        doubao_service = DoubaoService()
        
        # 测试不同敏感程度的prompt
        test_cases = [
            {
                "name": "轻度敏感",
                "prompt": "两个人争执的场景"
            },
            {
                "name": "中度敏感", 
                "prompt": "暴力冲突，有人受伤"
            },
            {
                "name": "高度敏感",
                "prompt": "血腥战争，死亡场景"
            }
        ]
        
        logger.info("=== 测试不同改写策略 ===")
        
        for case in test_cases:
            logger.info(f"\n--- {case['name']} ---")
            logger.info(f"原始: {case['prompt']}")
            
            for retry_count in range(1, 4):
                result = doubao_service.rewrite_prompt(case['prompt'], retry_count, "test_task_002")
                logger.info(f"策略{retry_count}: {result}")
                
    except Exception as e:
        logger.error(f"策略测试失败: {str(e)}")

if __name__ == "__main__":
    test_ai_rewrite()
    test_fallback_rewrite()
    test_rewrite_strategies() 