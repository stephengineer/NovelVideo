"""
处理器模块
包含各种数据处理和视频合成功能
"""

from .video_processor import VideoProcessor
from .storyboard_processor import StoryboardProcessor
from .novel_processor import NovelProcessor

__all__ = [
    'VideoProcessor',
    'StoryboardProcessor', 
    'NovelProcessor'
] 