"""
图像生成服务
基于火山引擎的图像生成API
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from .volcengine_service import VolcengineService
from ..core import config, get_logger, db_manager


class ImageGenService(VolcengineService):
    """图像生成服务类"""
    
    def __init__(self):
        super().__init__()
        self.image_config = config.get('image_gen', {})
        self.logger = get_logger('image_gen_service')
    
    def generate_image(self, prompt: str, output_path: str, task_id: str,
                      width: int = None, height: int = None, 
                      style: str = None, quality: str = None) -> bool:
        """
        生成图像
        
        Args:
            prompt: 图像描述提示词
            output_path: 输出图像文件路径
            task_id: 任务ID
            width: 图像宽度
            height: 图像高度
            style: 图像风格
            quality: 图像质量
            
        Returns:
            是否成功
        """
        try:
            # 使用配置的默认值
            width = width or self.image_config.get('width', 1920)
            height = height or self.image_config.get('height', 1080)
            style = style or self.image_config.get('style', 'realistic')
            quality = quality or self.image_config.get('quality', 'high')
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 构建请求数据
            request_data = {
                'prompt': prompt,
                'width': width,
                'height': height,
                'style': style,
                'quality': quality,
                'format': 'png'
            }
            
            # 调用图像生成API
            endpoint = f"{self.endpoints.get('image_gen')}/image/v1/generate"
            result = self._make_request('POST', endpoint, request_data, task_id)
            
            # 检查任务状态
            if 'task_id' in result:
                # 异步任务，需要轮询
                poll_url = f"{self.endpoints.get('image_gen')}/image/v1/task/{result['task_id']}"
                final_result = self._poll_task_status(result['task_id'], poll_url)
                
                # 下载图像文件
                image_url = final_result.get('image_url')
                if image_url and self._download_file(image_url, output_path):
                    self.logger.info(f"图像生成成功 | 任务: {task_id} | 文件: {output_path}")
                    return True
                else:
                    raise Exception("下载图像文件失败")
            else:
                # 同步任务，直接返回图像数据
                image_data = result.get('image_data')
                if image_data:
                    import base64
                    with open(output_path, 'wb') as f:
                        f.write(base64.b64decode(image_data))
                    self.logger.info(f"图像生成成功 | 任务: {task_id} | 文件: {output_path}")
                    return True
                else:
                    raise Exception("未获取到图像数据")
                    
        except Exception as e:
            self.logger.error(f"图像生成失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
    def generate_scene_image(self, scene_description: str, task_id: str, 
                           scene_number: int, scene_type: str = None) -> Optional[str]:
        """
        为场景生成图像
        
        Args:
            scene_description: 场景描述
            task_id: 任务ID
            scene_number: 场景编号
            scene_type: 场景类型（室内/室外/特写等）
            
        Returns:
            图像文件路径
        """
        try:
            # 根据场景类型优化提示词
            enhanced_prompt = self._enhance_prompt(scene_description, scene_type)
            
            # 生成输出路径
            output_dir = config.get_path('temp_dir') / task_id / 'images'
            output_path = output_dir / f"scene_{scene_number:02d}.png"
            
            # 生成图像
            if self.generate_image(enhanced_prompt, str(output_path), task_id):
                return str(output_path)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"场景图像生成失败 | 任务: {task_id} | 场景: {scene_number} | 错误: {str(e)}")
            return None
    
    def _enhance_prompt(self, description: str, scene_type: str = None) -> str:
        """增强图像生成提示词"""
        # 基础提示词
        prompt = f"高质量摄影，{description}"
        
        # 根据场景类型添加特定描述
        if scene_type:
            if scene_type == "室内":
                prompt += "，室内场景，温暖光线"
            elif scene_type == "室外":
                prompt += "，室外场景，自然光线"
            elif scene_type == "特写":
                prompt += "，特写镜头，细节丰富"
            elif scene_type == "远景":
                prompt += "，远景镜头，广阔视野"
        
        # 添加通用质量提升词
        prompt += "，8K超高清，电影级画质，专业摄影"
        
        return prompt
    
    def get_available_styles(self) -> Dict[str, Any]:
        """获取可用的图像风格列表"""
        try:
            endpoint = f"{self.endpoints.get('image_gen')}/image/v1/styles"
            result = self._make_request('GET', endpoint)
            return result
        except Exception as e:
            self.logger.error(f"获取图像风格列表失败: {str(e)}")
            return {} 