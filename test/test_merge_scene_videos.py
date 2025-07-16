#!/usr/bin/env python3
"""
测试 merge_scene_videos 方法
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import numpy as np
from moviepy import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips
from PIL import Image

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.processors.video_processor import VideoProcessor
from src.core.config import config
from src.core.logger import get_logger

def create_test_video(output_path: str, duration: float = 3.0, width: int = 720, height: int = 1280):
    """创建测试视频文件"""
    try:
        # 创建一个简单的彩色视频
        def make_frame(t):
            # 根据时间创建不同的颜色
            r = int(255 * (t / duration))
            g = int(255 * (1 - t / duration))
            b = 128
            
            # 创建彩色帧
            frame = np.full((height, width, 3), [r, g, b], dtype=np.uint8)
            
            # 添加一些简单的动画效果
            center_x, center_y = width // 2, height // 2
            radius = int(50 + 30 * np.sin(t * 2))
            
            # 绘制一个圆形
            y, x = np.ogrid[:height, :width]
            mask = (x - center_x)**2 + (y - center_y)**2 <= radius**2
            frame[mask] = [255, 255, 255]
            
            return frame
        
        # 创建视频剪辑
        clip = VideoFileClip(make_frame, duration=duration).with_fps(24)
        
        # 添加简单的音频（静音）
        audio = AudioFileClip(lambda t: np.zeros(2), duration=duration, fps=44100)
        clip = clip.with_audio(audio)
        
        # 写入文件
        clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            bitrate="1000k",
            audio_bitrate="64k",
            verbose=False,
            logger=None
        )
        
        clip.close()
        return True
        
    except Exception as e:
        print(f"创建测试视频失败: {e}")
        return False

def create_test_scene_videos(num_scenes: int = 3, temp_dir: str = None) -> list:
    """创建测试场景视频文件"""
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    
    scene_videos = []
    
    for i in range(num_scenes):
        video_path = os.path.join(temp_dir, f"scene_{i+1:02d}.mp4")
        duration = 3.0 + i * 0.5  # 每个场景时长递增
        
        if create_test_video(video_path, duration):
            scene_videos.append(video_path)
            print(f"创建测试视频: {video_path} (时长: {duration:.1f}s)")
        else:
            print(f"创建测试视频失败: scene_{i+1}")
    
    return scene_videos, temp_dir

def test_merge_scene_videos():
    """测试 merge_scene_videos 方法"""
    logger = get_logger('test_merge_scene_videos')
    
    print("=" * 60)
    print("开始测试 merge_scene_videos 方法")
    print("=" * 60)
    
    # 1. 创建测试视频文件
    print("\n1. 创建测试场景视频...")
    # scene_videos, temp_dir = create_test_scene_videos(num_scenes=3)
    scene_videos = [
        "/Users/zhongqi/Documents/dev/NovelVideo/data/temp/novel_video_d41a99a0/final_scenes/scene_01_final.mp4",
        "/Users/zhongqi/Documents/dev/NovelVideo/data/temp/novel_video_d41a99a0/final_scenes/scene_02_final.mp4",
    ]
    
    if not scene_videos:
        print("❌ 无法创建测试视频文件")
        return False
    
    print(f"✅ 成功创建 {len(scene_videos)} 个测试视频")
    
    # 2. 准备输出路径
    output_dir = Path(config.get_path('output_dir'))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "test_merged_video.mp4"
    
    # 3. 准备背景音乐
    bgm_dir = Path("assets/bgm")
    music_files = list(bgm_dir.glob("*.mp3"))
    
    if music_files:
        music_path = str(music_files[0])
        print(f"使用背景音乐: {music_path}")
    else:
        music_path = None
        print("⚠️  未找到背景音乐文件")
    
    # 4. 初始化 VideoProcessor
    print("\n2. 初始化 VideoProcessor...")
    video_processor = VideoProcessor()
    
    # 5. 测试合并功能
    print("\n3. 测试视频合并...")
    print(f"输入视频: {scene_videos}")
    print(f"输出路径: {output_path}")
    print(f"背景音乐: {music_path}")
    
    try:
        success = video_processor.merge_scene_videos(
            scene_videos=scene_videos,
            output_path=str(output_path),
            task_id="test_merge_001",
            transition_duration=1.0,
            music_path=music_path
        )
        
        if success:
            print("✅ 视频合并成功!")
            
            # 验证输出文件
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"输出文件大小: {file_size / 1024 / 1024:.2f} MB")
                
                # 检查视频信息
                try:
                    with VideoFileClip(str(output_path)) as clip:
                        print(f"合并后视频时长: {clip.duration:.2f} 秒")
                        print(f"视频分辨率: {clip.size[0]}x{clip.size[1]}")
                        print(f"视频帧率: {clip.fps} fps")
                except Exception as e:
                    print(f"⚠️  无法读取输出视频信息: {e}")
                
                return True
            else:
                print("❌ 输出文件不存在")
                return False
        else:
            print("❌ 视频合并失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    
    finally:
        # 6. 清理临时文件
        print("\n4. 清理临时文件...")
        try:
            shutil.rmtree(temp_dir)
            print("✅ 临时文件清理完成")
        except Exception as e:
            print(f"⚠️  清理临时文件失败: {e}")

def test_merge_with_different_transitions():
    """测试不同的转场时长"""
    print("\n" + "=" * 60)
    print("测试不同转场时长的合并效果")
    print("=" * 60)
    
    # 创建测试视频
    scene_videos, temp_dir = create_test_scene_videos(num_scenes=2)
    
    if not scene_videos:
        return False
    
    output_dir = Path(config.get_path('output_dir'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    video_processor = VideoProcessor()
    
    # 测试不同的转场时长
    transition_durations = [0.0, 0.5, 1.0, 2.0]
    
    for duration in transition_durations:
        output_path = output_dir / f"test_transition_{duration}s.mp4"
        
        print(f"\n测试转场时长: {duration}秒")
        
        success = video_processor.merge_scene_videos(
            scene_videos=scene_videos,
            output_path=str(output_path),
            task_id=f"test_transition_{duration}",
            transition_duration=duration,
            music_path=None  # 不使用背景音乐以便观察转场效果
        )
        
        if success:
            print(f"✅ 转场时长 {duration}s 测试成功")
        else:
            print(f"❌ 转场时长 {duration}s 测试失败")
    
    # 清理
    shutil.rmtree(temp_dir)

def test_merge_with_invalid_files():
    """测试处理无效文件的情况"""
    print("\n" + "=" * 60)
    print("测试处理无效文件的情况")
    print("=" * 60)
    
    # 创建一些有效视频和一个无效文件
    scene_videos, temp_dir = create_test_scene_videos(num_scenes=2)
    
    # 添加一个不存在的文件
    scene_videos.append("/path/to/nonexistent/video.mp4")
    
    output_dir = Path(config.get_path('output_dir'))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "test_invalid_files.mp4"
    
    video_processor = VideoProcessor()
    
    print("测试包含无效文件的合并...")
    success = video_processor.merge_scene_videos(
        scene_videos=scene_videos,
        output_path=str(output_path),
        task_id="test_invalid_files",
        transition_duration=1.0
    )
    
    if success:
        print("✅ 成功处理包含无效文件的合并")
    else:
        print("❌ 处理无效文件时失败")
    
    # 清理
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("开始测试 merge_scene_videos 功能")
    print("=" * 60)
    
    # 基础功能测试
    success1 = test_merge_scene_videos()
    
    # 转场效果测试
    # success2 = test_merge_with_different_transitions()
    
    # 错误处理测试
    # success3 = test_merge_with_invalid_files()
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"基础功能测试: {'✅ 通过' if success1 else '❌ 失败'}")
    # print(f"转场效果测试: {'✅ 通过' if success2 else '❌ 失败'}")
    # print(f"错误处理测试: {'✅ 通过' if success3 else '❌ 失败'}")
    print("=" * 60)
    
    if all([success1]):
        print("🎉 所有测试通过!")
    else:
        print("⚠️  部分测试失败，请检查日志") 