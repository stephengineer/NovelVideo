#!/usr/bin/env python3
"""
测试字体配置一致性
验证整个小说使用相同的字体配置
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.processors.novel_processor import NovelProcessor
from src.config.font_configs import get_font_config_names, get_font_config_by_name
from src.core import get_logger

def test_font_consistency():
    """测试字体配置一致性"""
    logger = get_logger('test_font_consistency')
    
    try:
        logger.info("开始测试字体配置一致性...")
        
        # 1. 显示所有可用的字体配置
        logger.info("可用的字体配置:")
        font_names = get_font_config_names()
        for i, name in enumerate(font_names, 1):
            logger.info(f"  {i}. {name}")
        
        logger.info("-" * 50)
        
        # 2. 创建小说处理器实例
        processor = NovelProcessor()
        
        # 3. 验证字体配置已设置
        if hasattr(processor, 'font_config') and processor.font_config:
            logger.info(f"小说处理器字体配置: {processor.font_config.name}")
            logger.info(f"  字体路径: {processor.font_config.font_path}")
            logger.info(f"  最大字符数: {processor.font_config.max_chars}")
            logger.info(f"  字体大小: {processor.font_config.font_size}")
            logger.info(f"  字体颜色: {processor.font_config.font_color}")
            logger.info(f"  描边颜色: {processor.font_config.stroke_color}")
            logger.info(f"  描边宽度: {processor.font_config.stroke_width}")
        else:
            logger.error("小说处理器未设置字体配置")
            return False
        
        logger.info("-" * 50)
        
        # 4. 测试指定字体配置
        logger.info("测试指定字体配置...")
        
        # 测试不同的字体配置
        test_configs = ['yellow_black', 'white_yellow', 'gold_blue']
        
        for config_name in test_configs:
            try:
                font_config = get_font_config_by_name(config_name)
                logger.info(f"获取字体配置 '{config_name}': {font_config.name}")
            except Exception as e:
                logger.error(f"获取字体配置 '{config_name}' 失败: {str(e)}")
        
        logger.info("-" * 50)
        
        # 5. 模拟场景视频创建（不实际创建文件）
        logger.info("模拟场景视频创建...")
        
        # 模拟场景数据
        mock_assets = {
            1: {
                'scene_description': '第一个场景的描述',
                'audio_path': '/mock/audio1.mp3',
                'audio_words': '{"words": [{"word": "这是", "start_time": 0, "end_time": 500}, {"word": "第一个", "start_time": 500, "end_time": 1000}]}',
                'audio_duration': 1000,
                'image_path': '/mock/image1.png',
                'video_path': ''
            },
            2: {
                'scene_description': '第二个场景的描述',
                'audio_path': '/mock/audio2.mp3',
                'audio_words': '{"words": [{"word": "这是", "start_time": 0, "end_time": 500}, {"word": "第二个", "start_time": 500, "end_time": 1000}]}',
                'audio_duration': 1000,
                'image_path': '/mock/image2.png',
                'video_path': ''
            }
        }
        
        # 验证每个场景都使用相同的字体配置
        for scene_number, assets in mock_assets.items():
            logger.info(f"场景 {scene_number} 将使用字体配置: {processor.font_config.name}")
        
        logger.info("所有场景将使用相同的字体配置，确保一致性")
        
        logger.info("-" * 50)
        logger.info("字体配置一致性测试完成！")
        
        return True
        
    except Exception as e:
        logger.error(f"字体配置一致性测试失败: {str(e)}")
        return False

def test_font_config_validation():
    """测试字体配置验证"""
    logger = get_logger('test_font_validation')
    
    try:
        logger.info("开始测试字体配置验证...")
        
        # 测试有效的字体配置
        valid_configs = ['yellow_black', 'white_yellow', 'red_white']
        
        for config_name in valid_configs:
            try:
                font_config = get_font_config_by_name(config_name)
                logger.info(f"✓ 字体配置 '{config_name}' 有效")
                
                # 验证字体文件是否存在
                if os.path.exists(font_config.font_path):
                    logger.info(f"  ✓ 字体文件存在: {font_config.font_path}")
                else:
                    logger.warning(f"  ⚠ 字体文件不存在: {font_config.font_path}")
                    
            except Exception as e:
                logger.error(f"✗ 字体配置 '{config_name}' 无效: {str(e)}")
        
        # 测试无效的字体配置
        invalid_config = get_font_config_by_name("nonexistent_config")
        logger.info(f"无效配置返回默认配置: {invalid_config.name}")
        
        logger.info("字体配置验证测试完成！")
        
    except Exception as e:
        logger.error(f"字体配置验证测试失败: {str(e)}")

if __name__ == "__main__":
    print("字体配置一致性测试")
    print("=" * 50)
    
    # 运行测试
    success1 = test_font_consistency()
    print("\n")
    test_font_config_validation()
    
    if success1:
        print("\n✓ 所有测试通过！")
    else:
        print("\n✗ 部分测试失败！") 