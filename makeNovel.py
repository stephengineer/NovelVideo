from moviepy import (
    VideoFileClip, AudioFileClip, TextClip,
    CompositeVideoClip, CompositeAudioClip,
)
import os
import tempfile
from typing import Optional, List, Tuple


def create_enhanced_video(
    video_path: str,
    text_content: str,
    voiceover_path: str,
    music_path: Optional[str] = None,
    sound_effects: Optional[List[Tuple[str, float, float]]] = None,  # (路径, 开始时间, 持续时间)
    output_path: str = "final_video.mp4",
    text_position: Tuple[str, str] = ('center', 'bottom'),
    text_duration: Optional[float] = None
) -> None:
    """
    增强版视频合成函数，支持视频、文案、配音、背景音乐和音效的融合
    
    参数说明:
        video_path: 原始视频路径
        text_content: 要显示的文案内容
        voiceover_path: 配音音频路径
        music_path: 背景音乐路径（可选）
        sound_effects: 音效列表（可选），每个元素为(音效路径, 开始时间, 持续时间)
        output_path: 输出视频路径
        text_position: 文字位置，如('center', 'bottom')或(50, 100)
        text_duration: 文字显示时长，None表示与视频同长
    """
    # 资源管理上下文（自动释放资源）
    with VideoFileClip(video_path) as video_clip:
        video_duration = video_clip.duration
        
        # 加载配音并处理长度
        with AudioFileClip(voiceover_path) as voiceover_clip:
            # 确保配音长度不超过视频
            if voiceover_clip.duration > video_duration:
                voiceover_clip = voiceover_clip.subclipped(0, video_duration)
            audio_clips = [voiceover_clip]  # 基础音频轨道（配音）
            
            # 添加背景音乐（降低音量避免覆盖配音）
            # if music_path and os.path.exists(music_path):
            #     with AudioFileClip(music_path) as music_clip:
            #         # 调整背景音乐长度
            #         if music_clip.duration < video_duration:
            #             music_clip = music_clip.loop(duration=video_duration)
            #         else:
            #             music_clip = music_clip.subclip(0, video_duration)
            #         # 背景音乐音量设为配音的30%（可调整）
            #         music_clip = music_clip.volumex(0.3)
            #         audio_clips.append(music_clip)
            
            # 添加音效（精确控制时间和音量）
            if sound_effects:
                for sfx_path, start_time, duration in sound_effects:
                    if not os.path.exists(sfx_path):
                        print(f"警告：音效文件不存在 - {sfx_path}")
                        continue
                    # 确保音效不超出视频时长
                    end_time = min(start_time + duration, video_duration)
                    with AudioFileClip(sfx_path) as sfx_clip:
                        # 截取音效并调整音量
                        sfx_clip = sfx_clip.subclip(0, min(duration, sfx_clip.duration))
                        sfx_clip = sfx_clip.set_start(start_time).volumex(1.2)  # 音效稍大声
                        audio_clips.append(sfx_clip)
            
            # 混合所有音频轨道
            final_audio = CompositeAudioClip(audio_clips)
            video_clip = video_clip.with_audio(final_audio)
            
            # 创建文字图层
            text_clip = TextClip(
                font="NotoSansSC-Regular.ttf",
                text=text_content,
                font_size=130,
                method='caption',  # 自动换行
                size=(int(video_clip.w * 0.85), None),  # 文字宽度限制为视频的85%
                duration=video_duration,
                text_align='center',
                transparent=True
            )
            text_clip = text_clip.with_start(1).with_duration(video_duration)
            text_clip = text_clip.with_position(("center", "bottom"))  # 设置位置
 
            # text_clip = text_clip.set_duration(
            #     text_duration if text_duration is not None else video_duration
            # )
            
            # 合成视频和文字
            final_video = CompositeVideoClip(
                [video_clip, text_clip]
            )
            
            # 写入输出文件（使用高效编码）
            final_video.write_videofile(
                output_path,
                codec="libx264",          # H.264编码（广泛兼容）
                audio_codec="aac",        # AAC音频编码
                bitrate="5000k",          # 视频比特率（质量控制）
                audio_bitrate="192k",     # 音频比特率
                fps=video_clip.fps,       # 保持原视频帧率
                threads=os.cpu_count(),   # 多线程加速
                preset="medium"           # 平衡速度和压缩率
            )
            
            print(f"视频合成完成：{os.path.abspath(output_path)}")


if __name__ == "__main__":

    # 示例用法

    # 音效配置：(路径, 开始时间, 持续时间)
    sound_effects = [
        ("notification.wav", 2.5, 1.0),   # 2.5秒处添加提示音，持续1秒
        ("applause.wav", 8.0, 2.5),      # 8秒处添加掌声，持续2.5秒
    ]
    
    create_enhanced_video(
        video_path="input_video.mp4",
        text_content="户外花园，繁花盛开，蝴蝶飞舞，小美站在花丛小径。",
        voiceover_path="narration.mp3",
        music_path=None,
        sound_effects=None,
        output_path="enhanced_output.mp4",
        text_position=('center', 'bottom'),
        text_duration=None  # 文字全程显示
    )

    