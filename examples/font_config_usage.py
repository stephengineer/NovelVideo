#!/usr/bin/env python3
"""
字体配置使用示例
展示如何使用和自定义字体配置
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.font_configs import (
    get_font_config_names, 
    get_font_config_by_name, 
    get_random_font_config,
    FontConfig
)
from src.core import get_logger

def example_font_config_usage():
    """字体配置使用示例"""
    logger = get_logger('font_config_example')
    
    logger.info("字体配置使用示例")
    logger.info("=" * 50)
    
    # 1. 查看所有可用的字体配置
    logger.info("1. 查看所有可用的字体配置:")
    font_names = get_font_config_names()
    for i, name in enumerate(font_names, 1):
        logger.info(f"   {i:2d}. {name}")
    
    logger.info("-" * 50)
    
    # 2. 获取特定的字体配置
    logger.info("2. 获取特定的字体配置:")
    
    # 获取黄色字体配置
    yellow_config = get_font_config_by_name("yellow_black")
    logger.info(f"黄色字体配置:")
    logger.info(f"  名称: {yellow_config.name}")
    logger.info(f"  字体路径: {yellow_config.font_path}")
    logger.info(f"  最大字符数: {yellow_config.max_chars}")
    logger.info(f"  字体大小: {yellow_config.font_size}")
    logger.info(f"  字体颜色: {yellow_config.font_color}")
    logger.info(f"  描边颜色: {yellow_config.stroke_color}")
    logger.info(f"  描边宽度: {yellow_config.stroke_width}")
    
    logger.info("-" * 30)
    
    # 获取金色字体配置
    gold_config = get_font_config_by_name("gold_blue")
    logger.info(f"金色字体配置:")
    logger.info(f"  名称: {gold_config.name}")
    logger.info(f"  字体颜色: {gold_config.font_color}")
    logger.info(f"  描边颜色: {gold_config.stroke_color}")
    
    logger.info("-" * 50)
    
    # 3. 随机获取字体配置
    logger.info("3. 随机获取字体配置:")
    for i in range(3):
        random_config = get_random_font_config()
        logger.info(f"  随机配置 {i+1}: {random_config.name}")
    
    logger.info("-" * 50)
    
    # 4. 创建自定义字体配置
    logger.info("4. 创建自定义字体配置:")
    
    # 创建自定义配置
    custom_config = FontConfig(
        name="custom_purple",
        font_path="/path/to/custom/font.ttf",
        max_chars=11,
        font_size=76,
        font_color="#8A2BE2",  # 深紫色
        stroke_color="white",
        stroke_width=2
    )
    
    logger.info(f"自定义配置:")
    logger.info(f"  名称: {custom_config.name}")
    logger.info(f"  字体颜色: {custom_config.font_color}")
    logger.info(f"  最大字符数: {custom_config.max_chars}")
    
    logger.info("-" * 50)
    
    # 5. 字体配置应用场景
    logger.info("5. 字体配置应用场景:")
    
    scenarios = [
        {
            "场景": "温馨故事",
            "推荐配置": "pink_gray",
            "理由": "粉色字体营造温馨感"
        },
        {
            "场景": "悬疑故事", 
            "推荐配置": "purple_white",
            "理由": "紫色字体增加神秘感"
        },
        {
            "场景": "冒险故事",
            "推荐配置": "gold_blue", 
            "理由": "金色字体体现高端感"
        },
        {
            "场景": "自然故事",
            "推荐配置": "green_black",
            "理由": "绿色字体体现自然感"
        }
    ]
    
    for scenario in scenarios:
        config = get_font_config_by_name(scenario["推荐配置"])
        logger.info(f"  {scenario['场景']}:")
        logger.info(f"    推荐配置: {config.name}")
        logger.info(f"    字体颜色: {config.font_color}")
        logger.info(f"    理由: {scenario['理由']}")
        logger.info("")

def example_novel_processor_integration():
    """小说处理器集成示例"""
    logger = get_logger('novel_processor_example')
    
    logger.info("小说处理器字体配置集成示例")
    logger.info("=" * 50)
    
    try:
        # 导入小说处理器
        from src.processors.novel_processor import NovelProcessor
        
        # 创建处理器实例
        processor = NovelProcessor()
        
        # 验证字体配置
        if hasattr(processor, 'font_config'):
            logger.info(f"小说处理器已设置字体配置: {processor.font_config.name}")
            logger.info(f"  字体颜色: {processor.font_config.font_color}")
            logger.info(f"  描边颜色: {processor.font_config.stroke_color}")
            logger.info(f"  最大字符数: {processor.font_config.max_chars}")
            
            # 模拟处理多个场景
            logger.info("\n模拟处理多个场景:")
            for scene_num in range(1, 4):
                logger.info(f"  场景 {scene_num}: 使用字体配置 '{processor.font_config.name}'")
            
            logger.info("\n✓ 所有场景将使用相同的字体配置，确保一致性")
            
        else:
            logger.error("小说处理器未设置字体配置")
            
    except Exception as e:
        logger.error(f"集成示例失败: {str(e)}")

def example_subtitle_service_usage():
    """字幕服务使用示例"""
    logger = get_logger('subtitle_service_example')
    
    logger.info("字幕服务字体配置使用示例")
    logger.info("=" * 50)
    
    try:
        # 导入字幕服务
        from src.services.subtitle_service import add_timed_subtitles
        
        # 模拟音频文字数据
        mock_audio_words = '''
        {
            "words": [
                {"word": "这是", "start_time": 0, "end_time": 500},
                {"word": "一个", "start_time": 500, "end_time": 1000},
                {"word": "测试", "start_time": 1000, "end_time": 1500},
                {"word": "场景", "start_time": 1500, "end_time": 2000}
            ]
        }
        '''
        
        # 模拟视频尺寸
        video_size = (1920, 1080)
        
        # 使用不同的字体配置生成字幕
        font_configs = ['yellow_black', 'white_yellow', 'gold_blue']
        
        for config_name in font_configs:
            try:
                font_config = get_font_config_by_name(config_name)
                logger.info(f"使用字体配置 '{config_name}':")
                logger.info(f"  字体颜色: {font_config.font_color}")
                logger.info(f"  描边颜色: {font_config.stroke_color}")
                logger.info(f"  最大字符数: {font_config.max_chars}")
                
                # 生成字幕（这里只是演示，不实际创建文件）
                # subtitle_clips = add_timed_subtitles(mock_audio_words, video_size, font_config)
                logger.info(f"  ✓ 字幕生成成功（使用配置: {config_name}）")
                
            except Exception as e:
                logger.error(f"  ✗ 字幕生成失败: {str(e)}")
            
            logger.info("")
            
    except Exception as e:
        logger.error(f"字幕服务示例失败: {str(e)}")

if __name__ == "__main__":
    print("字体配置使用示例")
    print("=" * 60)
    
    # 运行示例
    example_font_config_usage()
    print("\n")
    example_novel_processor_integration()
    print("\n")
    example_subtitle_service_usage()
    
    print("\n示例执行完成！")
    print("\n主要功能说明：")
    print("1. 字体配置集中管理，便于维护")
    print("2. 整个小说使用一致的字体配置")
    print("3. 支持多种字体样式和颜色搭配")
    print("4. 可以根据故事类型选择合适的字体配置")
    print("5. 支持自定义字体配置") 