#!/usr/bin/env python3
"""
视频生成服务敏感内容重试功能使用示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.video_gen_service import VideoGenService
from src.core import get_logger

def example_video_gen_with_retry():
    """示例：使用视频生成服务的重试功能"""
    logger = get_logger('video_retry_example')
    
    try:
        # 初始化视频生成服务
        video_service = VideoGenService()
        
        # 示例1：文生视频（可能包含敏感内容）
        logger.info("=== 示例1：文生视频重试 ===")
        
        task_id = "example_video_001"
        scene_number = 1
        seed = 12345
        
        # 可能敏感的prompt
        sensitive_prompt = "一个人在激烈的战斗中，暴力场景"
        
        logger.info(f"原始prompt: {sensitive_prompt}")
        
        try:
            result = video_service.generate_video_from_text(
                prompt=sensitive_prompt,
                task_id=task_id,
                scene_number=scene_number,
                seed=seed
            )
            
            if result:
                logger.info(f"视频生成成功: {result}")
            else:
                logger.warning("视频生成失败")
                
        except Exception as e:
            logger.error(f"视频生成异常: {str(e)}")
        
        logger.info("-" * 50)
        
        # 示例2：图生视频（可能包含敏感内容）
        logger.info("=== 示例2：图生视频重试 ===")
        
        # 假设有一个图像文件
        image_path = "path/to/input_image.jpg"  # 需要替换为实际路径
        
        # 可能敏感的prompt
        image_prompt = "基于图像生成暴力场景"
        
        logger.info(f"图像路径: {image_path}")
        logger.info(f"原始prompt: {image_prompt}")
        
        try:
            # 注意：这里需要实际的图像文件才能测试
            # result = video_service.generate_video_from_image(
            #     prompt=image_prompt,
            #     image_path=image_path,
            #     task_id=task_id,
            #     scene_number=scene_number + 1,
            #     seed=seed
            # )
            
            logger.info("图生视频功能需要实际的图像文件才能测试")
            
        except Exception as e:
            logger.error(f"图生视频异常: {str(e)}")
        
        logger.info("-" * 50)
        
        # 示例3：直接测试prompt改写功能
        logger.info("=== 示例3：直接测试prompt改写 ===")
        
        test_prompts = [
            "暴力打架场景",
            "血腥战斗场面",
            "不当的诱惑内容"
        ]
        
        for i, prompt in enumerate(test_prompts):
            logger.info(f"测试prompt {i+1}: {prompt}")
            
            for retry_count in range(1, 4):
                try:
                    rewritten = video_service.doubao_service.rewrite_prompt(
                        prompt, retry_count, f"example_rewrite_{i+1}"
                    )
                    logger.info(f"  重试{retry_count}次: {rewritten}")
                except Exception as e:
                    logger.error(f"  改写失败: {str(e)}")
            
            logger.info("")
        
    except Exception as e:
        logger.error(f"示例执行失败: {str(e)}")

def example_batch_video_gen():
    """示例：批量视频生成，自动处理敏感内容"""
    logger = get_logger('batch_video_example')
    
    try:
        # 初始化视频生成服务
        video_service = VideoGenService()
        
        # 批量prompt（包含正常和敏感内容）
        prompts = [
            "一个人在公园里散步，温馨场景",
            "暴力打架，激烈冲突",
            "美丽的自然风景，和谐画面",
            "血腥战斗，残酷场面",
            "温馨的家庭聚会，欢乐时光"
        ]
        
        task_id = "batch_video_001"
        seed = 12345
        
        logger.info("=== 批量视频生成示例 ===")
        
        for i, prompt in enumerate(prompts):
            logger.info(f"处理第{i+1}个prompt: {prompt}")
            
            try:
                result = video_service.generate_video_from_text(
                    prompt=prompt,
                    task_id=task_id,
                    scene_number=i+1,
                    seed=seed
                )
                
                if result:
                    logger.info(f"  成功生成视频: {result}")
                else:
                    logger.warning(f"  视频生成失败")
                    
            except Exception as e:
                logger.error(f"  处理异常: {str(e)}")
            
            logger.info("-" * 30)
        
    except Exception as e:
        logger.error(f"批量处理失败: {str(e)}")

if __name__ == "__main__":
    print("视频生成服务敏感内容重试功能使用示例")
    print("=" * 50)
    
    # 运行示例
    example_video_gen_with_retry()
    print("\n")
    example_batch_video_gen()
    
    print("\n示例执行完成！")
    print("\n主要功能说明：")
    print("1. 自动检测敏感内容错误")
    print("2. 使用AI模型智能改写prompt")
    print("3. 最多重试3次，每次使用不同策略")
    print("4. 完整的日志记录和错误处理")
    print("5. 支持文生视频和图生视频两种模式") 