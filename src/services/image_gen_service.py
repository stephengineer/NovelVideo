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
        
        # 初始化豆包服务用于prompt改写
        from .doubao_service import DoubaoService
        self.doubao_service = DoubaoService()
        
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
            response, duration = self._call_image_gen_api(payload)
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查任务状态
                if 'error' not in result:
                    return self._process_successful_response(result, output_path, task_id, duration, payload)
                else:
                    if "Sensitive" in response.get('error', {}).get('code', ''):
                        # 重试3次重新改写prompt，并重新生成图像
                        self.logger.warning(f"检测到敏感内容，开始重试 | 任务: {task_id} | 原始prompt: {prompt}")
                        
                        for retry_count in range(3):
                            try:
                                # 改写prompt
                                new_prompt = self.doubao_service.rewrite_prompt(prompt, retry_count + 1, task_id)
                                self.logger.info(f"重试第{retry_count + 1}次 | 改写后prompt: {new_prompt}")
                                
                                # 更新payload中的prompt
                                payload['prompt'] = new_prompt
                                
                                # 重新调用API
                                retry_response, _ = self._call_image_gen_api(payload)
                                
                                if retry_response.status_code == 200:
                                    retry_result = retry_response.json()
                                    
                                    if 'error' not in retry_result:
                                        # 重试成功，处理结果
                                        success = self._process_successful_response(retry_result, output_path, task_id, duration, payload, retry_count + 1)
                                        if success:
                                            return True
                                    elif "Sensitive" not in retry_result.get('error', {}).get('code', ''):
                                        # 其他错误，记录并继续重试
                                        self.logger.warning(f"重试第{retry_count + 1}次遇到其他错误: {retry_result.get('error')}")
                                        continue
                                    else:
                                        # 仍然是敏感内容错误，继续重试
                                        self.logger.warning(f"重试第{retry_count + 1}次仍然检测到敏感内容")
                                        continue
                                else:
                                    self._handle_api_error(retry_response, task_id, duration, payload, retry_count + 1)
                                    continue
                                    
                            except Exception as retry_e:
                                self.logger.warning(f"重试第{retry_count + 1}次异常: {str(retry_e)}")
                                continue
                        
                        # 所有重试都失败了
                        error_msg = f"图像生成失败: 敏感内容重试3次后仍然失败"
                        db_manager.log_api_call(task_id, 'doubao', 'image_generate', 'error', duration, error_msg, payload, result)
                        raise Exception(error_msg)
                    else:
                        error_msg = f"图像生成失败: {result.get('error').get('code')} - {result.get('error').get('message')}"
                        db_manager.log_api_call(task_id, 'doubao', 'image_generate', 'error', duration, error_msg, payload, result)
                        raise Exception(error_msg)
            else:
                self._handle_api_error(response, task_id, duration, payload)
                    
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
    
    def generate_scene_image(self, image_prompt: str, task_id: str, 
                           scene_number: int, seed: int) -> Optional[str]:
        """
        为场景生成图像
        
        Args:
            scene_description: 场景描述
            task_id: 任务ID
            scene_number: 场景编号
            seed: 随机种子
            
        Returns:
            图像文件路径
        """
        try:
            # 根据场景类型优化提示词
            enhanced_prompt = self._enhance_prompt(image_prompt)
            
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
    
    def _enhance_prompt(self, scene_description: str) -> str:
        """增强图像生成提示词"""
        # 基础提示词
        prompt = f"{scene_description}"
        
        # 添加通用质量提升词
        # prompt += "，8K超高清，电影级画质，专业摄影"
        
        return prompt
    
    def _call_image_gen_api(self, payload: Dict[str, Any]) -> tuple[requests.Response, float]:
        """
        调用图像生成API
        
        Args:
            payload: 请求数据
            
        Returns:
            (响应对象, 耗时)
        """
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
        
        return response, duration
    
    def _handle_api_error(self, response: requests.Response, task_id: str, duration: float, 
                         payload: Dict[str, Any], retry_count: int = None) -> None:
        """
        处理API调用错误
        
        Args:
            response: 响应对象
            task_id: 任务ID
            duration: 请求耗时
            payload: 请求数据
            retry_count: 重试次数（可选）
        """
        retry_info = f" | 重试次数: {retry_count}" if retry_count else ""
        error_msg = f"文生图API调用失败: {response.status_code} - {response.text}{retry_info}"
        self.logger.warning(error_msg)
        db_manager.log_api_call(task_id, 'doubao', 'image_generate', 'error', duration, error_msg, payload, response)
    
    def _process_successful_response(self, result: Dict[str, Any], output_path: str, task_id: str, 
                                   duration: float, payload: Dict[str, Any], retry_count: int = None) -> bool:
        """
        处理成功的API响应
        
        Args:
            result: API响应结果
            output_path: 输出文件路径
            task_id: 任务ID
            duration: 请求耗时
            payload: 请求数据
            retry_count: 重试次数（可选）
            
        Returns:
            是否成功
        """
        try:
            if self.response_format == 'url':
                # 下载图像文件
                image_url = result.get('data')[0].get('url')
                if image_url and self._download_file(image_url, output_path):
                    retry_info = f" | 重试次数: {retry_count}" if retry_count else ""
                    self.logger.info(f"图像生成下载成功 | 任务: {task_id} | 文件: {output_path}{retry_info}")
                    # 提取token使用情况
                    usage_info = {}
                    if 'usage' in result:
                        usage_info = {
                            'completion_tokens': result['usage'].get('output_tokens', 0),
                            'total_tokens': result['usage'].get('total_tokens', 0)
                        }
                    db_manager.log_api_call(task_id, 'doubao', 'image_generate', 'success', duration, request_data=payload, response_data=result, usage_info=usage_info)
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
                    retry_info = f" | 重试次数: {retry_count}" if retry_count else ""
                    self.logger.info(f"图像生成解析成功 | 任务: {task_id} | 文件: {output_path}{retry_info}")
                    # 提取token使用情况
                    usage_info = {}
                    if 'usage' in result:
                        usage_info = {
                            'completion_tokens': result['usage'].get('output_tokens', 0),
                            'total_tokens': result['usage'].get('total_tokens', 0)
                        }
                    db_manager.log_api_call(task_id, 'doubao', 'image_generate', 'success', duration, request_data=payload, response_data=result, usage_info=usage_info)
                    return True
                else:
                    raise Exception("解析图像数据失败")
            else:
                raise Exception(f"不支持的响应格式: {self.response_format}")
        except Exception as e:
            self.logger.error(f"处理API响应失败: {str(e)}")
            return False
    
    
    def get_available_styles(self) -> Dict[str, Any]:
        """获取可用的图像风格列表"""
        try:
            endpoint = f"{self.endpoints.get('image_gen')}/image/v1/styles"
            result = self._make_request('GET', endpoint)
            return result
        except Exception as e:
            self.logger.error(f"获取图像风格列表失败: {str(e)}")
            return {} 