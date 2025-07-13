#!/usr/bin/env python3
"""
测试视频生成服务的敏感内容重试功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.video_gen_service import VideoGenService
from src.core import config, get_logger

def test_video_gen_retry():
    """测试视频生成重试功能"""
    logger = get_logger('test_video_retry')
    
    try:
        # 初始化视频生成服务
        video_service = VideoGenService()
        
        # 测试任务ID
        task_id = "test_video_retry_001"
        
        # 测试敏感prompt（可能触发敏感内容检测）
        sensitive_prompts = [
            "一个人在打架，暴力场景",
            "血腥的战斗场面",
            "不当的诱惑内容",
            "政治敏感话题讨论"
        ]
        
        for i, prompt in enumerate(sensitive_prompts):
            logger.info(f"测试第{i+1}个敏感prompt: {prompt}")
            
            try:
                # 测试文生视频
                result = video_service.generate_video_from_text(
                    prompt=prompt,
                    task_id=task_id,
                    scene_number=i+1,
                    seed=12345
                )
                
                if result:
                    logger.info(f"视频生成成功: {result}")
                else:
                    logger.warning(f"视频生成失败")
                    
            except Exception as e:
                logger.error(f"测试异常: {str(e)}")
            
            logger.info("-" * 50)
        
        # 测试正常prompt
        normal_prompts = [
            "一个人在公园里散步",
            "温馨的家庭场景",
            "美丽的自然风景"
        ]
        
        for i, prompt in enumerate(normal_prompts):
            logger.info(f"测试第{i+1}个正常prompt: {prompt}")
            
            try:
                # 测试文生视频
                result = video_service.generate_video_from_text(
                    prompt=prompt,
                    task_id=task_id,
                    scene_number=i+10,
                    seed=12345
                )
                
                if result:
                    logger.info(f"视频生成成功: {result}")
                else:
                    logger.warning(f"视频生成失败")
                    
            except Exception as e:
                logger.error(f"测试异常: {str(e)}")
            
            logger.info("-" * 50)
            
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")

def test_prompt_rewrite():
    """测试prompt改写功能"""
    logger = get_logger('test_prompt_rewrite')
    
    try:
        # 初始化视频生成服务
        video_service = VideoGenService()
        
        # 测试敏感prompt改写
        sensitive_prompts = [
            "暴力打架场景",
            "血腥战斗",
            "不当内容"
        ]
        
        for i, prompt in enumerate(sensitive_prompts):
            logger.info(f"测试prompt改写 {i+1}: {prompt}")
            
            for retry_count in range(1, 4):
                try:
                    rewritten = video_service.doubao_service.rewrite_prompt(
                        prompt, retry_count, f"test_rewrite_{i+1}"
                    )
                    logger.info(f"重试{retry_count}次改写结果: {rewritten}")
                except Exception as e:
                    logger.error(f"改写失败: {str(e)}")
            
            logger.info("-" * 30)
            
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")

if __name__ == "__main__":
    print("开始测试视频生成重试功能...")
    test_prompt_rewrite()
    print("\n开始测试视频生成重试功能...")
    test_video_gen_retry()
    print("测试完成！") 