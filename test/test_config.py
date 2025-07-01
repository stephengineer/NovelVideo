#!/usr/bin/env python3
"""
测试统一配置
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core import config


def test_config():
    """测试配置"""
    print("=== 测试统一配置 ===")
    
    try:
        # 测试豆包配置
        doubao_config = {
            'api_key': config.get('doubao.api_key'),
            'base_url': config.get('doubao.base_url'),
            'model': config.get('doubao.model'),
            'app_id': config.get('doubao.app_id')
        }
        
        print("豆包配置:")
        for key, value in doubao_config.items():
            if key == 'api_key' and value:
                print(f"  {key}: {'*' * 10} (已配置)")
            else:
                print(f"  {key}: {value}")
        
        # 测试TTS配置
        tts_config = {
            'voice': config.get('tts.voice'),
            'speed': config.get('tts.speed'),
            'volume': config.get('tts.volume'),
            'pitch': config.get('tts.pitch')
        }
        
        print("\nTTS配置:")
        for key, value in tts_config.items():
            print(f"  {key}: {value}")
        
        # 测试图像生成配置
        image_config = {
            'width': config.get('image_gen.width'),
            'height': config.get('image_gen.height'),
            'style': config.get('image_gen.style'),
            'quality': config.get('image_gen.quality')
        }
        
        print("\n图像生成配置:")
        for key, value in image_config.items():
            print(f"  {key}: {value}")
        
        # 测试视频生成配置
        video_config = {
            'duration': config.get('video_gen.duration'),
            'transition': config.get('video_gen.transition'),
            'effects': config.get('video_gen.effects')
        }
        
        print("\n视频生成配置:")
        for key, value in video_config.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_config()
    if success:
        print("\n✓ 配置测试通过")
    else:
        print("\n✗ 配置测试失败")
        sys.exit(1) 