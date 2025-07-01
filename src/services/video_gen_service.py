"""
视频生成服务
基于火山引擎的视频生成API
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from .volcengine_service import VolcengineService
from ..core import config, get_logger, db_manager


class VideoGenService(VolcengineService):
    """视频生成服务类"""
    
    def __init__(self):
        super().__init__()
        self.video_config = config.get('video_gen', {})
        self.logger = get_logger('video_gen_service')
    
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
            duration = duration or self.video_config.get('duration', 10)
            transition = transition or self.video_config.get('transition', 'fade')
            effects = effects or self.video_config.get('effects', ['zoom', 'pan'])
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 上传图像文件
            image_url = self._upload_file(image_path)
            if not image_url:
                raise Exception("图像文件上传失败")
            
            # 构建请求数据
            request_data = {
                'image_url': image_url,
                'duration': duration,
                'transition': transition,
                'effects': effects,
                'format': 'mp4',
                'fps': config.get('video.fps', 30),
                'resolution': config.get('video.resolution', [1920, 1080])
            }
            
            # 调用视频生成API
            endpoint = f"{self.endpoints.get('video_gen')}/video/v1/generate"
            result = self._make_request('POST', endpoint, request_data, task_id)
            
            # 检查任务状态
            if 'task_id' in result:
                # 异步任务，需要轮询
                poll_url = f"{self.endpoints.get('video_gen')}/video/v1/task/{result['task_id']}"
                final_result = self._poll_task_status(result['task_id'], poll_url)
                
                # 下载视频文件
                video_url = final_result.get('video_url')
                if video_url and self._download_file(video_url, output_path):
                    self.logger.info(f"视频生成成功 | 任务: {task_id} | 文件: {output_path}")
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
                    return True
                else:
                    raise Exception("未获取到视频数据")
                    
        except Exception as e:
            self.logger.error(f"视频生成失败 | 任务: {task_id} | 错误: {str(e)}")
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