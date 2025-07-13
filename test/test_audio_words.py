#!/usr/bin/env python3
"""
测试audio_words功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core import config, get_logger, db_manager
from src.services.tts_service import TTSService
from pathlib import Path

def test_audio_words():
    """测试audio_words功能"""
    logger = get_logger('test_audio_words')
    
    try:
        # 初始化TTS服务
        tts_service = TTSService()
        
        # 测试数据
        task_id = "test_audio_words_001"
        scene_description = "这是一个测试场景描述"
        scene_number = 1
        
        # 生成输出路径
        output_dir = config.get_path('temp_dir') / task_id / 'audio'
        output_path = output_dir / f"scene_{scene_number:02d}.mp3"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"开始测试audio_words功能 | 任务: {task_id}")
        
        # 测试generate_speech方法
        success, audio_words, audio_duration = tts_service.generate_speech(
            scene_description, str(output_path), task_id
        )
        
        if success:
            logger.info(f"TTS生成成功 | audio_words: {audio_words}")
            logger.info(f"audio_duration: {audio_duration}")
            logger.info(f"音频文件路径: {output_path}")
            
            # 测试generate_scene_audio方法
            audio_path, scene_audio_words, scene_audio_duration = tts_service.generate_scene_audio(
                scene_description, task_id, scene_number
            )
            
            if audio_path:
                logger.info(f"场景音频生成成功 | audio_path: {audio_path}")
                logger.info(f"场景audio_words: {scene_audio_words}")
                logger.info(f"场景audio_duration: {scene_audio_duration}")
                
                # 验证数据库存储
                storyboard_id = f"{task_id}_scene_{scene_number}"
                storyboards = db_manager.get_storyboards(task_id)
                
                if storyboards:
                    for storyboard in storyboards:
                        if storyboard['id'] == storyboard_id:
                            logger.info(f"数据库中的audio_words: {storyboard.get('audio_words')}")
                            logger.info(f"数据库中的audio_duration: {storyboard.get('audio_duration')}")
                            break
                else:
                    logger.warning("未找到数据库记录")
            else:
                logger.error("场景音频生成失败")
        else:
            logger.error("TTS生成失败")
            
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")

if __name__ == "__main__":
    test_audio_words() 