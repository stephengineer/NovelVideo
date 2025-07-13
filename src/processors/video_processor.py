"""
视频处理器
负责视频合成和后期处理
"""

import os
import random
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from moviepy import (
    VideoFileClip, AudioFileClip, TextClip,
    CompositeVideoClip, CompositeAudioClip,
    ImageClip, VideoClip, concatenate_videoclips
)
from PIL import Image
from ..core import config, get_logger, db_manager
from ..services.subtitle_service import add_timed_subtitles

from moviepy import ImageSequenceClip
import tempfile

class VideoProcessor:
    """视频处理器类"""
    
    def __init__(self):
        self.video_config = config.get('video', {})
        self.logger = get_logger('video_processor')
    
    def create_scene_video(self, image_path: str, video_path: str, audio_path: str, audio_duration: float, audio_words: str, text_content: str,
                          output_path: str, task_id: str, scene_number: int,
                          font_config=None, sound_effects: Optional[List[Tuple[str, float, float]]] = None) -> bool:
        """
        创建单个场景视频
        
        Args:
            video_path: 背景视频路径
            audio_path: 配音音频路径
            text_content: 字幕文本
            output_path: 输出视频路径
            task_id: 任务ID
            scene_number: 场景编号
            sound_effects: 音效列表
            
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"开始处理场景视频 | 任务: {task_id} | 场景: {scene_number}")
            
            # 加载配音并处理长度
            voiceover_clip = AudioFileClip(audio_path)
            audio_duration_seconds = audio_duration / 1000
            
            # 使用图片运镜生成视频
            if image_path:
                # 图片运镜生成视频
                video_clip = self.create_video_by_camera_movement(image_path, audio_duration_seconds)
            else:
                video_clip = self.modify_video_speed(video_path, audio_duration_seconds)

            audio_clips = [voiceover_clip]  # 基础音频轨道（配音）
                
            # 添加背景音乐
            # if music_path and os.path.exists(music_path):
            #     with AudioFileClip(music_path) as music_clip:
            #         # 调整背景音乐长度
            #         if music_clip.duration < video_duration:
            #             music_clip = music_clip.loop(duration=video_duration)
            #         else:
            #             music_clip = music_clip.subclip(0, video_duration)
            #         # 背景音乐音量设为配音的30%
            #         music_clip = music_clip.volumex(0.3)
            #         audio_clips.append(music_clip)
                
            # 添加音效
            # if sound_effects:
            #     for sfx_path, start_time, duration in sound_effects:
            #         if not os.path.exists(sfx_path):
            #             self.logger.warning(f"音效文件不存在: {sfx_path}")
            #             continue
            #         # 确保音效不超出视频时长
            #         end_time = min(start_time + duration, video_duration)
            #         with AudioFileClip(sfx_path) as sfx_clip:
            #             # 截取音效并调整音量
            #             sfx_clip = sfx_clip.subclip(0, min(duration, sfx_clip.duration))
            #             sfx_clip = sfx_clip.set_start(start_time).volumex(1.2)
            #             audio_clips.append(sfx_clip)
                
            # 混合所有音频轨道
            final_audio = CompositeAudioClip(audio_clips)
            video_clip = video_clip.with_audio(final_audio)
            
            # 创建文字图层，使用指定的字体配置
            text_clips = add_timed_subtitles(audio_words, video_clip.size, font_config)
            
            # 合成视频和文字
            final_video = CompositeVideoClip([video_clip, *text_clips])
            
            # 写入输出文件
            try:
                final_video.write_videofile(output_path, fps=final_video.fps)
            except:
                final_video.write_videofile(output_path, fps=30)
            
            self.logger.info(f"场景视频处理完成 | 任务: {task_id} | 场景: {scene_number} | 文件: {output_path}")
            return True
                    
        except Exception as e:
            self.logger.error(f"场景视频处理失败 | 任务: {task_id} | 场景: {scene_number} | 错误: {str(e)}")
            return False
    
    def create_video_by_camera_movement(self, image_path, duration):
        """创建随机运镜效果的视频"""
        # 加载图片
        img = ImageClip(image_path).get_frame(0)
        img_h, img_w = img.shape[:2]
        
        # 随机选择运镜类型
        movements = ["up", "down", "left", "right", "zoom_in", "zoom_out"]
        movement_type = random.choice(movements)
        
        def make_frame(t):
            # 根据时间进度计算当前状态 (0-1)
            progress = min(t / duration, 0.999)
            
            # 初始化裁剪区域（默认全屏）
            view_w, view_h = int(img_w * 0.9), int(img_h * 0.9)
            x, y = 0, 0
            
            # 根据运镜类型调整裁剪区域和位置
            if movement_type == "up":
                # 镜头向上移动（裁剪区域向下）
                max_shift = img_h * 0.1  # 最大移动距离
                y = max_shift * progress
                
            elif movement_type == "down":
                # 镜头向下移动（裁剪区域向上）
                max_shift = img_h * 0.1
                y = max_shift * (1 - progress)
                
            elif movement_type == "left":
                # 镜头向左移动（裁剪区域向右）
                max_shift = img_w * 0.1
                x = max_shift * progress
                
            elif movement_type == "right":
                # 镜头向右移动（裁剪区域向左）
                max_shift = img_w * 0.1
                x = max_shift * (1 - progress)
                
            elif movement_type == "zoom_in":
                # 镜头放大（裁剪区域缩小并居中）
                start_scale = 1.0  # 初始缩放比例（100%）
                end_scale = 0.8    # 最终缩放比例（50%）
                current_scale = start_scale - (start_scale - end_scale) * progress
                
                view_w = int(img_w * current_scale)
                view_h = int(img_h * current_scale)
                x = (img_w - view_w) / 2  # 居中
                y = (img_h - view_h) / 2
                
            elif movement_type == "zoom_out":
                # 镜头缩小（裁剪区域放大并居中）
                start_scale = 0.8  # 初始缩放比例（50%）
                end_scale = 1.0    # 最终缩放比例（100%）
                current_scale = start_scale + (end_scale - start_scale) * progress
                
                view_w = int(img_w * current_scale)
                view_h = int(img_h * current_scale)
                x = (img_w - view_w) / 2  # 居中
                y = (img_h - view_h) / 2
            
            # 确保裁剪区域不超出原图范围（转换为整数前进行边界检查）
            x = max(0, min(x, img_w - view_w))
            y = max(0, min(y, img_h - view_h))
            
            # 转换为整数
            x, y, view_w, view_h = int(x), int(y), int(view_w), int(view_h)
            
            # 裁剪局部区域
            cropped = img[y:y+view_h, x:x+view_w]
            
            # 将裁剪区域放大/缩小至原图尺寸
            pil_img = Image.fromarray(cropped)
            scaled_img = pil_img.resize((img_w, img_h), Image.LANCZOS)
            
            return np.array(scaled_img)
        
        # 生成基础视频剪辑
        return  VideoClip(make_frame, duration=duration).with_fps(30)


    def modify_video_speed(self, video_path, audio_duration_seconds):
        video_clip = VideoFileClip(video_path)
        video_duration = video_clip.duration
        
        if video_duration == audio_duration_seconds:
            return video_clip
        
        speed_factor = video_duration / audio_duration_seconds
        new_fps = video_clip.fps * speed_factor
        modified_video_clip = video_clip.with_fps(new_fps, change_duration=True)

        # 检查修改后的视频时长是否小于音频时长
        if modified_video_clip.duration < audio_duration_seconds:
            # 计算需要重复的次数
            repeat_times = int(audio_duration_seconds / modified_video_clip.duration) + 1
            repeated_clips = [modified_video_clip] * repeat_times
            extended_clip = concatenate_videoclips(repeated_clips)
            # 截取与音频时长相同的部分
            final_clip = extended_clip.subclip(0, audio_duration_seconds)
        else:
            final_clip = modified_video_clip
        
        return final_clip

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
            
            # 加载所有视频片段
            video_clips = []
            for i, video_path in enumerate(scene_videos):
                if not os.path.exists(video_path):
                    self.logger.warning(f"场景视频文件不存在: {video_path}")
                    continue
                
                clip = VideoFileClip(video_path)
                
                # 添加转场效果
                # if i > 0 and transition_duration > 0:
                #     # 在视频开头添加淡入效果
                #     clip = clip.fadein(transition_duration)
                
                video_clips.append(clip)
            
            if not video_clips:
                raise Exception("没有有效的视频片段")
            
            # 合并视频片段
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # 写入最终视频
            final_video.write_videofile(
                output_path,
                codec="libx264",  # 视频编码（通用）
                audio_codec="aac",  # 音频编码（强制使用AAC，兼容性强）
                bitrate="5000k",
                audio_bitrate="128k"  # 音频比特率（可选，确保音质）
            )
            
            # 清理资源
            for clip in video_clips:
                clip.close()
            final_video.close()
            
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