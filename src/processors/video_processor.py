"""
视频处理器
负责视频合成和后期处理
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from moviepy import (
    VideoFileClip, AudioFileClip, TextClip,
    CompositeVideoClip, CompositeAudioClip,
)
from ..core import config, get_logger, db_manager


class VideoProcessor:
    """视频处理器类"""
    
    def __init__(self):
        self.video_config = config.get('video', {})
        self.logger = get_logger('video_processor')
    
    def create_scene_video(self, video_path: str, audio_path: str, text_content: str,
                          output_path: str, task_id: str, scene_number: int,
                          text_position: Tuple[str, str] = ('center', 'bottom'),
                          text_duration: Optional[float] = None,
                          music_path: Optional[str] = None,
                          sound_effects: Optional[List[Tuple[str, float, float]]] = None) -> bool:
        """
        创建单个场景视频
        
        Args:
            video_path: 背景视频路径
            audio_path: 配音音频路径
            text_content: 字幕文本
            output_path: 输出视频路径
            task_id: 任务ID
            scene_number: 场景编号
            text_position: 文字位置
            text_duration: 文字显示时长
            music_path: 背景音乐路径
            sound_effects: 音效列表
            
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"开始处理场景视频 | 任务: {task_id} | 场景: {scene_number}")
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 使用资源管理上下文
            with VideoFileClip(video_path) as video_clip:
                video_duration = video_clip.duration
                
                # 加载配音并处理长度
                with AudioFileClip(audio_path) as voiceover_clip:
                    # 确保配音长度不超过视频
                    if voiceover_clip.duration > video_duration:
                        voiceover_clip = voiceover_clip.subclip(0, video_duration)
                    audio_clips = [voiceover_clip]  # 基础音频轨道（配音）
                    
                    # 添加背景音乐
                    if music_path and os.path.exists(music_path):
                        with AudioFileClip(music_path) as music_clip:
                            # 调整背景音乐长度
                            if music_clip.duration < video_duration:
                                music_clip = music_clip.loop(duration=video_duration)
                            else:
                                music_clip = music_clip.subclip(0, video_duration)
                            # 背景音乐音量设为配音的30%
                            music_clip = music_clip.volumex(0.3)
                            audio_clips.append(music_clip)
                    
                    # 添加音效
                    if sound_effects:
                        for sfx_path, start_time, duration in sound_effects:
                            if not os.path.exists(sfx_path):
                                self.logger.warning(f"音效文件不存在: {sfx_path}")
                                continue
                            # 确保音效不超出视频时长
                            end_time = min(start_time + duration, video_duration)
                            with AudioFileClip(sfx_path) as sfx_clip:
                                # 截取音效并调整音量
                                sfx_clip = sfx_clip.subclip(0, min(duration, sfx_clip.duration))
                                sfx_clip = sfx_clip.set_start(start_time).volumex(1.2)
                                audio_clips.append(sfx_clip)
                    
                    # 混合所有音频轨道
                    final_audio = CompositeAudioClip(audio_clips)
                    video_clip = video_clip.with_audio(final_audio)
                    
                    # 创建文字图层
                    font_path = config.get_path('fonts_dir') / "NotoSansSC-Regular.ttf"
                    if not font_path.exists():
                        font_path = "NotoSansSC-Regular.ttf"  # 回退到当前目录
                    
                    text_clip = TextClip(
                        font=str(font_path),
                        text=text_content,
                        font_size=130,
                        method='caption',  # 自动换行
                        size=(int(video_clip.w * 0.85), None),  # 文字宽度限制为视频的85%
                        duration=video_duration,
                        text_align='center',
                        transparent=True
                    )
                    text_clip = text_clip.with_start(1).with_duration(video_duration)
                    text_clip = text_clip.with_position(text_position)
                    
                    # 合成视频和文字
                    final_video = CompositeVideoClip([video_clip, text_clip])
                    
                    # 写入输出文件
                    final_video.write_videofile(
                        output_path,
                        codec=self.video_config.get('codec', 'libx264'),
                        audio_codec=self.video_config.get('audio_codec', 'aac'),
                        bitrate=self.video_config.get('bitrate', '5000k'),
                        audio_bitrate=self.video_config.get('audio_bitrate', '192k'),
                        fps=video_clip.fps,
                        threads=os.cpu_count(),
                        preset=self.video_config.get('preset', 'medium')
                    )
                    
                    self.logger.info(f"场景视频处理完成 | 任务: {task_id} | 场景: {scene_number} | 文件: {output_path}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"场景视频处理失败 | 任务: {task_id} | 场景: {scene_number} | 错误: {str(e)}")
            return False
    
    def merge_scene_videos(self, scene_videos: List[str], output_path: str, 
                          task_id: str, transition_duration: float = None) -> bool:
        """
        合并多个场景视频
        
        Args:
            scene_videos: 场景视频路径列表
            output_path: 输出视频路径
            task_id: 任务ID
            transition_duration: 转场时长
            
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"开始合并场景视频 | 任务: {task_id} | 场景数: {len(scene_videos)}")
            
            # 使用配置的转场时长
            transition_duration = transition_duration or config.get('storyboard.transition_duration', 1.0)
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 加载所有视频片段
            video_clips = []
            for i, video_path in enumerate(scene_videos):
                if not os.path.exists(video_path):
                    self.logger.warning(f"场景视频文件不存在: {video_path}")
                    continue
                
                clip = VideoFileClip(video_path)
                
                # 添加转场效果
                if i > 0 and transition_duration > 0:
                    # 在视频开头添加淡入效果
                    clip = clip.fadein(transition_duration)
                
                video_clips.append(clip)
            
            if not video_clips:
                raise Exception("没有有效的视频片段")
            
            # 合并视频片段
            final_video = CompositeVideoClip(video_clips)
            
            # 写入最终视频
            final_video.write_videofile(
                output_path,
                codec=self.video_config.get('codec', 'libx264'),
                audio_codec=self.video_config.get('audio_codec', 'aac'),
                bitrate=self.video_config.get('bitrate', '5000k'),
                audio_bitrate=self.video_config.get('audio_bitrate', '192k'),
                fps=video_clips[0].fps,
                threads=os.cpu_count(),
                preset=self.video_config.get('preset', 'medium')
            )
            
            # 清理资源
            for clip in video_clips:
                clip.close()
            
            self.logger.info(f"场景视频合并完成 | 任务: {task_id} | 文件: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"场景视频合并失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
    def add_intro_outro(self, main_video_path: str, intro_video_path: str, 
                       outro_video_path: str, output_path: str, task_id: str) -> bool:
        """
        添加片头和片尾
        
        Args:
            main_video_path: 主视频路径
            intro_video_path: 片头视频路径
            outro_video_path: 片尾视频路径
            output_path: 输出视频路径
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"开始添加片头片尾 | 任务: {task_id}")
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 加载视频片段
            video_clips = []
            
            # 添加片头
            if intro_video_path and os.path.exists(intro_video_path):
                intro_clip = VideoFileClip(intro_video_path)
                video_clips.append(intro_clip)
            
            # 添加主视频
            main_clip = VideoFileClip(main_video_path)
            video_clips.append(main_clip)
            
            # 添加片尾
            if outro_video_path and os.path.exists(outro_video_path):
                outro_clip = VideoFileClip(outro_video_path)
                video_clips.append(outro_clip)
            
            # 合并视频
            final_video = CompositeVideoClip(video_clips)
            
            # 写入最终视频
            final_video.write_videofile(
                output_path,
                codec=self.video_config.get('codec', 'libx264'),
                audio_codec=self.video_config.get('audio_codec', 'aac'),
                bitrate=self.video_config.get('bitrate', '5000k'),
                audio_bitrate=self.video_config.get('audio_bitrate', '192k'),
                fps=main_clip.fps,
                threads=os.cpu_count(),
                preset=self.video_config.get('preset', 'medium')
            )
            
            # 清理资源
            for clip in video_clips:
                clip.close()
            
            self.logger.info(f"片头片尾添加完成 | 任务: {task_id} | 文件: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"片头片尾添加失败 | 任务: {task_id} | 错误: {str(e)}")
            return False 