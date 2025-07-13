import json
import string
import random
from pathlib import Path
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from config.font_configs import get_random_font_config, get_font_config_by_name


# --------------------------
# 通用工具函数
# --------------------------
def _parse_words(frontend_str):
    """解析文字和时间数据"""
    frontend_data = json.loads(frontend_str)
    return frontend_data["words"]

def _filter_punctuation(text):
    """过滤所有标点符号（中英文）"""
    punctuations = set(string.punctuation + "。！？，；、")
    return "".join([char for char in text if char not in punctuations])


# --------------------------
# 字幕拆分逻辑（依赖当前字体的max_chars）
# --------------------------
def _split_into_lines(words, current_font_config):
    """按当前字体的max_chars拆分文字为多行"""
    lines = []
    current_line_words = []  # 当前行包含的字

    for word_info in words:
        word = word_info["word"]
        current_line_words.append(word_info)

        # 遇到标点符号强制切分
        split_symbols = {"。", "！", "？", "，", "；", "、", ",", ";", "!", "?"}
        has_punct = any(char in split_symbols for char in word)
        if has_punct:
            line_text = "".join([w["word"] for w in current_line_words])
            line_text_clean = _filter_punctuation(line_text)
            if line_text_clean:
                lines.append({
                    "text": line_text_clean,
                    "start": current_line_words[0]["start_time"],
                    "end": current_line_words[-1]["end_time"]
                })
            current_line_words = []
            continue

        # 未到标点但字符数超过当前字体的max_chars
        current_text_clean = _filter_punctuation(
            "".join([w["word"] for w in current_line_words])
        )
        if len(current_text_clean) >= current_font_config.max_chars:
            lines.append({
                "text": current_text_clean,
                "start": current_line_words[0]["start_time"],
                "end": current_line_words[-1]["end_time"]
            })
            current_line_words = []

    # 处理最后一行剩余内容
    if current_line_words:
        line_text_clean = _filter_punctuation(
            "".join([w["word"] for w in current_line_words])
        )
        if line_text_clean:
            lines.append({
                "text": line_text_clean,
                "start": current_line_words[0]["start_time"],
                "end": current_line_words[-1]["end_time"]
            })

    return lines


# --------------------------
# 生成字幕视频（应用当前字体的样式配置）
# --------------------------
def add_timed_subtitles(frontend_str, video_size, font_config=None):
    """
    生成字幕视频
    
    Args:
        frontend_str: 前端格式的文字时间数据
        video_size: 视频尺寸 (width, height)
        font_config: 字体配置，如果为None则随机选择
        
    Returns:
        字幕片段列表
    """
    # 解析文字时间数据
    words = _parse_words(frontend_str)

    # 如果没有指定字体配置，则随机选择一个
    if font_config is None:
        font_config = get_random_font_config()

    # 按选中字体的max_chars拆分字幕
    lines = _split_into_lines(words, font_config)

    """使用选中字体的配置生成字幕（颜色、描边等）"""
    subtitle_clips = []
    video_w, video_h = video_size

    for i, line_info in enumerate(lines):
        text = line_info["text"]
        start_time = line_info["start"] / 1000  # 毫秒转秒
        end_time = line_info["end"] / 1000
        duration = end_time - start_time
        
        # 创建字幕片段（应用字体样式配置）
        txt_clip = TextClip(
            text=text,
            font=font_config.font_path,       # 字体路径
            font_size=font_config.font_size,   # 字号
            color=font_config.font_color,     # 字体颜色
            stroke_color=font_config.stroke_color,  # 描边颜色
            stroke_width=font_config.stroke_width,  # 描边宽度
            size=(int(video_w * 0.95), None),  # 宽度限制为视频的90%
            margin=(0, video_h * 0.25),
            method="caption"                  # 自动居中
        ).with_position(("center", "bottom"))     # 水平居中，垂直定位
        
        # 设置字幕显示时间
        txt_clip = txt_clip.with_start(start_time).with_duration(duration)
        subtitle_clips.append(txt_clip)
    return subtitle_clips