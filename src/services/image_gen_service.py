"""
图像生成服务
基于火山引擎豆包文生图API
"""

import os
import requests
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from ..core import config, get_logger, db_manager


class ImageGenService:
    """豆包文生图服务类"""
    
    def __init__(self):
        self.base_url = config.get('doubao.base_url')
        self.api_key = config.get('doubao.api_key')
        self.model = config.get('image_gen.model')
        self.response_format = config.get('image_gen.response_format')
        self.size = config.get('image_gen.size')
        self.seed = config.get('image_gen.seed')
        self.guidance_scale = config.get('image_gen.guidance_scale')
        self.watermark = config.get('image_gen.watermark')
        self.logger = get_logger('image_gen_service')
        
        if not self.api_key:
            raise ValueError("豆包API密钥未配置")
    
    def generate_image(self, prompt: str, output_path: str, task_id: str, seed: int) -> bool:
        """
        生成图像
        
        Args:
            prompt: 图像描述提示词
            output_path: 输出图像文件路径
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        try:
            # 验证seed取值范围取值范围为 [0, 2147483647]
            if seed >= 0 and seed <= 2147483647:
                self.seed = seed
            
            # 构建请求数据
            payload = {
                'model': self.model,
                'prompt': prompt,
                'response_format': self.response_format,
                'size': self.size,
                'seed': self.seed,
                'guidance_scale': self.guidance_scale,
                'watermark': self.watermark
            }
            
            # 调用豆包文生图API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v3/images/generations",
                headers=headers,
                data=json.dumps(payload),
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查任务状态
                if 'error' not in result:
                    if self.response_format == 'url':
                        # 下载图像文件
                        image_url = result.get('data')[0].get('url')
                        if image_url and self._download_file(image_url, output_path):
                            self.logger.info(f"图像生成下载成功 | 任务: {task_id} | 文件: {output_path}")
                            db_manager.log_api_call(task_id, 'doubao', 'image_generate', 'success', duration, request_data=payload, response_data=result)
                            return True
                        else:
                            raise Exception("下载图像文件失败")
                    elif self.response_format == 'b64_json':
                        # 解析base64编码的图像数据
                        image_data = result.get('data')[0].get('b64_json')
                        if image_data:
                            import base64
                            with open(output_path, 'wb') as f:
                                f.write(base64.b64decode(image_data))
                            self.logger.info(f"图像生成解析成功 | 任务: {task_id} | 文件: {output_path}")
                            db_manager.log_api_call(task_id, 'doubao', 'image_generate', 'success', duration, request_data=payload, response_data=result)
                            return True
                        else:
                            raise Exception("解析图像数据失败")
                else:
                    error_msg = f"图像生成失败: {result.get('error').get('code')} - {result.get('error').get('message')}"
                    db_manager.log_api_call(task_id, 'doubao', 'image_generate', 'error', duration, error_msg, payload, result)
                    raise Exception(error_msg)
            else:
                error_msg = f"文生图API调用失败: {response.status_code} - {response.text}"
                db_manager.log_api_call(task_id, 'doubao', 'image_generate', 'error', duration, error_msg, payload, response)
                raise Exception(error_msg)
                    
        except Exception as e:
            self.logger.error(f"图像生成失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
    def _poll_task_status(self, task_id: str, poll_url: str) -> Dict[str, Any]:
        """轮询任务状态"""
        max_attempts = 60  # 最多轮询60次
        poll_interval = 3  # 每3秒轮询一次
        
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
                        raise Exception(f"图像生成任务失败: {result.get('error_message', '未知错误')}")
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
    
    def generate_scene_image(self, scene_content: str, task_id: str, 
                           scene_number: int, seed: int, scene_type: str = None) -> Optional[str]:
        """
        为场景生成图像
        
        Args:
            scene_content: 场景内容
            task_id: 任务ID
            scene_number: 场景编号
            scene_type: 场景类型（室内/室外/特写等）
            
        Returns:
            图像文件路径
        """
        try:
            # 根据场景类型优化提示词
            enhanced_prompt = self._enhance_prompt(scene_content, scene_type)
            
            # 生成输出路径
            output_dir = config.get_path('temp_dir') / task_id / 'images'
            output_path = output_dir / f"scene_{scene_number:02d}.png"

            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 生成图像
            if self.generate_image(enhanced_prompt, str(output_path), task_id, seed):
                return str(output_path)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"场景图像生成失败 | 任务: {task_id} | 场景: {scene_number} | 错误: {str(e)}")
            return None
    
    def _enhance_prompt(self, scene_content: str, scene_type: str = None) -> str:
        """增强图像生成提示词"""
        # 基础提示词
        prompt = f"{scene_content}"
        
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
        # prompt += "，8K超高清，电影级画质，专业摄影"
        
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