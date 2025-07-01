"""
文本转语音服务
基于火山引擎豆包语音API
"""

import os
import requests
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from ..core import config, get_logger, db_manager


class TTSService:
    """豆包语音TTS服务类"""
    
    def __init__(self):
        self.api_key = config.get('doubao_tts.api_key')
        self.base_url = config.get('doubao_tts.base_url')
        self.app_id = config.get('doubao_tts.app_id')
        self.logger = get_logger('tts_service')
        
        if not self.api_key:
            raise ValueError("豆包语音API密钥未配置")
    
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
            voice = voice or config.get('tts.voice', 'BV001_streaming')
            speed = speed or config.get('tts.speed', 1.0)
            volume = volume or config.get('tts.volume', 1.0)
            pitch = pitch or config.get('tts.pitch', 1.0)
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 构建请求数据
            request_data = {
                'app_id': self.app_id,
                'text': text,
                'voice_type': voice,
                'speed': speed,
                'volume': volume,
                'pitch': pitch,
                'format': 'mp3',
                'sample_rate': config.get('audio.sample_rate', 44100)
            }
            
            # 调用豆包TTS API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/tts/v1/synthesize",
                headers=headers,
                json=request_data,
                timeout=60
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查任务状态
                if 'task_id' in result:
                    # 异步任务，需要轮询
                    poll_url = f"{self.base_url}/tts/v1/task/{result['task_id']}"
                    final_result = self._poll_task_status(result['task_id'], poll_url)
                    
                    # 下载音频文件
                    audio_url = final_result.get('audio_url')
                    if audio_url and self._download_file(audio_url, output_path):
                        self.logger.info(f"TTS生成成功 | 任务: {task_id} | 文件: {output_path}")
                        db_manager.log_api_call('doubao_tts', 'synthesize', 'success', duration)
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
                        db_manager.log_api_call('doubao_tts', 'synthesize', 'success', duration)
                        return True
                    else:
                        raise Exception("未获取到音频数据")
            else:
                error_msg = f"TTS API调用失败: {response.status_code} - {response.text}"
                db_manager.log_api_call('doubao_tts', 'synthesize', 'error', duration, 
                                      error_message=error_msg)
                raise Exception(error_msg)
                    
        except Exception as e:
            self.logger.error(f"TTS生成失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
    def _poll_task_status(self, task_id: str, poll_url: str) -> Dict[str, Any]:
        """轮询任务状态"""
        max_attempts = 30  # 最多轮询30次
        poll_interval = 2  # 每2秒轮询一次
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(poll_url, headers=headers, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    if status == 'completed':
                        return result
                    elif status == 'failed':
                        raise Exception(f"TTS任务失败: {result.get('error_message', '未知错误')}")
                    elif status in ['pending', 'processing']:
                        time.sleep(poll_interval)
                        continue
                    else:
                        raise Exception(f"未知的任务状态: {status}")
                else:
                    raise Exception(f"轮询任务状态失败: {response.status_code}")
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                time.sleep(poll_interval)
        
        raise Exception("任务超时")
    
    def _download_file(self, url: str, local_path: str) -> bool:
        """下载文件"""
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(f"下载文件失败: {str(e)}")
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