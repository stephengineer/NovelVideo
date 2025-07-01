"""
视频生成服务
基于火山引擎豆包图生视频API
"""

import os
import requests
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from ..core import config, get_logger, db_manager


class VideoGenService:
    """豆包图生视频服务类"""
    
    def __init__(self):
        self.api_key = config.get('doubao.api_key')
        self.base_url = config.get('doubao.base_url')
        self.logger = get_logger('video_gen_service')
        
        if not self.api_key:
            raise ValueError("豆包API密钥未配置")
    
    def generate_video_from_image(self, image_path: str, output_path: str, task_id: str,
                                 duration: int = None, transition: str = None,
                                 effects: List[str] = None) -> bool:
        """
        从图像生成视频
        
        Args:
            image_path: 输入图像路径
            output_path: 输出视频路径
            task_id: 任务ID
            duration: 视频时长（秒）
            transition: 转场效果
            effects: 特效列表
            
        Returns:
            是否成功
        """
        try:
            # 使用配置的默认值
            duration = duration or config.get('video_gen.duration', 10)
            transition = transition or config.get('video_gen.transition', 'fade')
            effects = effects or config.get('video_gen.effects', ['zoom', 'pan'])
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 读取图像文件并转换为base64
            with open(image_path, 'rb') as f:
                import base64
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 构建请求数据
            request_data = {
                'model': 'doubao-seedance-1.0-pro',
                'image': image_data,
                'duration': duration,
                'transition': transition,
                'effects': effects,
                'format': 'mp4',
                'fps': config.get('video.fps', 30),
                'resolution': config.get('video.resolution', [1920, 1080])
            }
            
            # 调用豆包图生视频API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/v1/videos/generations",
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
                    poll_url = f"{self.base_url}/v1/videos/tasks/{result['task_id']}"
                    final_result = self._poll_task_status(result['task_id'], poll_url)
                    
                    # 下载视频文件
                    video_url = final_result.get('video_url')
                    if video_url and self._download_file(video_url, output_path):
                        self.logger.info(f"视频生成成功 | 任务: {task_id} | 文件: {output_path}")
                        db_manager.log_api_call('doubao', 'video_generate', 'success', duration)
                        return True
                    else:
                        raise Exception("下载视频文件失败")
                else:
                    # 同步任务，直接返回视频数据
                    video_data = result.get('video_data')
                    if video_data:
                        import base64
                        with open(output_path, 'wb') as f:
                            f.write(base64.b64decode(video_data))
                        self.logger.info(f"视频生成成功 | 任务: {task_id} | 文件: {output_path}")
                        db_manager.log_api_call('doubao', 'video_generate', 'success', duration)
                        return True
                    else:
                        raise Exception("未获取到视频数据")
            else:
                error_msg = f"图生视频API调用失败: {response.status_code} - {response.text}"
                db_manager.log_api_call('doubao', 'video_generate', 'error', duration, 
                                      error_message=error_msg)
                raise Exception(error_msg)
                    
        except Exception as e:
            self.logger.error(f"视频生成失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
    def _poll_task_status(self, task_id: str, poll_url: str) -> Dict[str, Any]:
        """轮询任务状态"""
        max_attempts = 120  # 最多轮询120次
        poll_interval = 5   # 每5秒轮询一次
        
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
                        raise Exception(f"视频生成任务失败: {result.get('error_message', '未知错误')}")
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
            response = requests.get(url, timeout=120)  # 视频文件下载需要更长时间
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(f"下载文件失败: {str(e)}")
            return False
    
    def generate_scene_video(self, image_path: str, task_id: str, scene_number: int,
                           duration: int = None) -> Optional[str]:
        """
        为场景生成视频
        
        Args:
            image_path: 场景图像路径
            task_id: 任务ID
            scene_number: 场景编号
            duration: 视频时长
            
        Returns:
            视频文件路径
        """
        try:
            # 生成输出路径
            output_dir = config.get_path('temp_dir') / task_id / 'videos'
            output_path = output_dir / f"scene_{scene_number:02d}.mp4"
            
            # 生成视频
            if self.generate_video_from_image(str(image_path), str(output_path), task_id, duration):
                return str(output_path)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"场景视频生成失败 | 任务: {task_id} | 场景: {scene_number} | 错误: {str(e)}")
            return None
    
    def _upload_file(self, file_path: str) -> Optional[str]:
        """上传文件到火山引擎"""
        try:
            # 这里需要根据火山引擎的实际API实现文件上传
            # 暂时返回一个占位符URL
            self.logger.warning("文件上传功能需要根据火山引擎API文档实现")
            return f"https://example.com/uploaded/{Path(file_path).name}"
        except Exception as e:
            self.logger.error(f"文件上传失败: {file_path}, 错误: {str(e)}")
            return None
    
    def get_available_transitions(self) -> Dict[str, Any]:
        """获取可用的转场效果列表"""
        try:
            endpoint = f"{self.endpoints.get('video_gen')}/video/v1/transitions"
            result = self._make_request('GET', endpoint)
            return result
        except Exception as e:
            self.logger.error(f"获取转场效果列表失败: {str(e)}")
            return {}
    
    def get_available_effects(self) -> Dict[str, Any]:
        """获取可用的特效列表"""
        try:
            endpoint = f"{self.endpoints.get('video_gen')}/video/v1/effects"
            result = self._make_request('GET', endpoint)
            return result
        except Exception as e:
            self.logger.error(f"获取特效列表失败: {str(e)}")
            return {} 