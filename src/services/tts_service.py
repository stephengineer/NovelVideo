"""
文本转语音服务
基于火山引擎的TTS API
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from .volcengine_service import VolcengineService
from ..core import config, get_logger, db_manager


class TTSService(VolcengineService):
    """文本转语音服务类"""
    
    def __init__(self):
        super().__init__()
        self.tts_config = config.get('tts', {})
        self.logger = get_logger('tts_service')
    
    def generate_speech(self, text: str, output_path: str, task_id: str,
                       voice: str = None, speed: float = None, 
                       volume: float = None, pitch: float = None) -> bool:
        """
        生成语音文件
        
        Args:
            text: 要转换的文本
            output_path: 输出音频文件路径
            task_id: 任务ID
            voice: 语音类型
            speed: 语速
            volume: 音量
            pitch: 音调
            
        Returns:
            是否成功
        """
        try:
            # 使用配置的默认值
            voice = voice or self.tts_config.get('voice', 'zh_female_1')
            speed = speed or self.tts_config.get('speed', 1.0)
            volume = volume or self.tts_config.get('volume', 1.0)
            pitch = pitch or self.tts_config.get('pitch', 1.0)
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 构建请求数据
            request_data = {
                'text': text,
                'voice': voice,
                'speed': speed,
                'volume': volume,
                'pitch': pitch,
                'format': 'mp3',
                'sample_rate': config.get('audio.sample_rate', 44100)
            }
            
            # 调用TTS API
            endpoint = f"{self.endpoints.get('tts')}/tts/v1/synthesize"
            result = self._make_request('POST', endpoint, request_data, task_id)
            
            # 检查任务状态
            if 'task_id' in result:
                # 异步任务，需要轮询
                poll_url = f"{self.endpoints.get('tts')}/tts/v1/task/{result['task_id']}"
                final_result = self._poll_task_status(result['task_id'], poll_url)
                
                # 下载音频文件
                audio_url = final_result.get('audio_url')
                if audio_url and self._download_file(audio_url, output_path):
                    self.logger.info(f"TTS生成成功 | 任务: {task_id} | 文件: {output_path}")
                    return True
                else:
                    raise Exception("下载音频文件失败")
            else:
                # 同步任务，直接返回音频数据
                audio_data = result.get('audio_data')
                if audio_data:
                    import base64
                    with open(output_path, 'wb') as f:
                        f.write(base64.b64decode(audio_data))
                    self.logger.info(f"TTS生成成功 | 任务: {task_id} | 文件: {output_path}")
                    return True
                else:
                    raise Exception("未获取到音频数据")
                    
        except Exception as e:
            self.logger.error(f"TTS生成失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
    def generate_scene_audio(self, scene_description: str, dialogue: str, 
                           task_id: str, scene_number: int) -> Optional[str]:
        """
        为场景生成音频文件
        
        Args:
            scene_description: 场景描述
            dialogue: 对话文本
            task_id: 任务ID
            scene_number: 场景编号
            
        Returns:
            音频文件路径
        """
        try:
            # 构建音频文本（场景描述 + 对话）
            audio_text = f"{scene_description}。{dialogue}"
            
            # 生成输出路径
            output_dir = config.get_path('temp_dir') / task_id / 'audio'
            output_path = output_dir / f"scene_{scene_number:02d}.mp3"
            
            # 生成语音
            if self.generate_speech(audio_text, str(output_path), task_id):
                return str(output_path)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"场景音频生成失败 | 任务: {task_id} | 场景: {scene_number} | 错误: {str(e)}")
            return None
    
    def get_available_voices(self) -> Dict[str, Any]:
        """获取可用的语音列表"""
        try:
            endpoint = f"{self.endpoints.get('tts')}/tts/v1/voices"
            result = self._make_request('GET', endpoint)
            return result
        except Exception as e:
            self.logger.error(f"获取语音列表失败: {str(e)}")
            return {} 