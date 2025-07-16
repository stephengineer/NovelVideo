"""
视频生成服务
负责调用火山引擎视频生成API
"""

import os
import json
import time
import random
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from ..core import config, get_logger, db_manager



class VideoGenService:
    """豆包图生视频服务类"""
    
    def __init__(self):
        self.base_url = config.get('doubao.base_url')
        self.api_key = config.get('doubao.api_key')
        self.model_pro = config.get('video_gen.model_pro')
        self.model_t2v = config.get('video_gen.model_t2v')
        self.model_i2v = config.get('video_gen.model_i2v')
        self.callback_url = config.get('video_gen.callback_url')
        self.resolution = config.get('video_gen.resolution')
        self.ratio = config.get('video_gen.ratio')
        self.duration = config.get('video_gen.duration')
        self.watermark = config.get('video_gen.watermark')
        self.seed = config.get('video_gen.seed')
        self.logger = get_logger('video_gen_service')
        
        # 初始化豆包服务用于prompt改写
        from .doubao_service import DoubaoService
        self.doubao_service = DoubaoService()
        
        if not self.api_key:
            raise ValueError("豆包API密钥未配置")
    
    def _poll_task_status(self, video_task_id: str, poll_url: str) -> Dict[str, Any]:
        """轮询任务状态"""
        max_attempts = 20  # 最多轮询次数
        poll_interval = 5   # 轮询一次间隔描述
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(poll_url, headers=headers, data="")
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    if status == 'succeeded':
                        return result
                    elif status == 'failed':
                        raise Exception(f"视频生成任务失败: {result.get('error').get('code')} {result.get('error').get('message')}")
                    elif status == 'cancelled':
                        raise Exception(f"视频生成任务取消")
                    elif status in ['running']:
                        time.sleep(poll_interval)
                        continue
                    elif status == 'queued':
                        time.sleep(poll_interval * 2)
                        continue
                    else:
                        raise Exception(f"未知的任务状态: {status}")
                else:
                    raise Exception(f"调用查询视频生成接口失败: {response.status_code}")
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
    
    def _call_video_gen_api(self, task_id: str, model: str, content: List[Dict], output_path: str, original_prompt: str = None) -> bool:
        """
        通用方法：调用视频生成API
        
        Args:
            task_id: 任务ID
            content: 请求内容列表
            output_path: 输出文件路径
            original_prompt: 原始prompt（用于重试时改写）
        Returns:
            是否成功
        """
        try:
            # 构建请求数据
            payload = {
                'model': model,
                'content': content
            }
            
            # 调用豆包视频生成API
            response, duration = self._make_video_api_call(payload)

            if response.status_code == 200:
                result = response.json()

                # 同步任务，需要轮询
                video_task_id = result.get('id')
                poll_url = f"{self.base_url}/api/v3/contents/generations/tasks/{video_task_id}"
                final_result = self._poll_task_status(video_task_id, poll_url)
                
                # 下载视频文件
                video_url = final_result.get('content').get('video_url')
                total_duration = time.time() - (time.time() - duration)
                if video_url and self._download_file(video_url, output_path):
                    # 提取token使用情况
                    usage_info = {}
                    if 'usage' in final_result:
                        usage_info = {
                            'completion_tokens': final_result['usage'].get('completion_tokens', 0),
                            'total_tokens': final_result['usage'].get('total_tokens', 0)
                        }
                    self.logger.info(f"视频生成成功 | 任务: {task_id} | 文件: {output_path}")
                    db_manager.log_api_call(task_id, 'doubao', 'video_generate', 'success', total_duration, 
                                            request_data=payload, response_data=final_result, usage_info=usage_info)
                    return True
                else:
                    raise Exception("下载视频文件失败")

            else:
                # 检查是否是敏感内容错误
                if "Sensitive" in response.get('error', {}).get('code', ''):
                    # 重试3次重新改写prompt，并重新生成视频
                    if original_prompt:
                        self.logger.warning(f"检测到敏感内容，开始重试 | 任务: {task_id} | 原始prompt: {original_prompt}")
                        
                        for retry_count in range(3):
                            try:
                                # 改写prompt
                                new_prompt = self.doubao_service.rewrite_prompt(original_prompt, retry_count + 1, task_id)
                                self.logger.info(f"重试第{retry_count + 1}次 | 改写后prompt: {new_prompt}")
                                
                                # 更新content中的prompt
                                updated_content = self._update_content_prompt(content, new_prompt)
                                
                                # 重新调用API
                                retry_response, _ = self._make_video_api_call({
                                    'model': model,
                                    'content': updated_content
                                })
                                
                                if retry_response.status_code == 200:
                                    retry_result = retry_response.json()
                                    
                                    # 异步任务，需要轮询
                                    retry_video_task_id = retry_result.get('id')
                                    retry_poll_url = f"{self.base_url}/api/v3/contents/generations/tasks/{retry_video_task_id}"
                                    retry_final_result = self._poll_task_status(retry_video_task_id, retry_poll_url)
                                    
                                    # 下载视频文件
                                    retry_video_url = retry_final_result.get('content').get('video_url')
                                    if retry_video_url and self._download_file(retry_video_url, output_path):
                                        # 提取token使用情况
                                        usage_info = {}
                                        if 'usage' in retry_final_result:
                                            usage_info = {
                                                'completion_tokens': retry_final_result['usage'].get('completion_tokens', 0),
                                                'total_tokens': retry_final_result['usage'].get('total_tokens', 0)
                                            }
                                        self.logger.info(f"视频生成重试成功 | 任务: {task_id} | 重试次数: {retry_count + 1} | 文件: {output_path}")
                                        db_manager.log_api_call(task_id, 'doubao', 'video_generate', 'success', total_duration, 
                                                                request_data={'model': model, 'content': updated_content}, 
                                                                response_data=retry_final_result, usage_info=usage_info)
                                        return True
                                    else:
                                        raise Exception("下载重试视频文件失败")
                                elif "Sensitive" not in retry_response.text:
                                    # 其他错误，记录并继续重试
                                    self.logger.warning(f"重试第{retry_count + 1}次遇到其他错误: {retry_response.text}")
                                    continue
                                else:
                                    # 仍然是敏感内容错误，继续重试
                                    self.logger.warning(f"重试第{retry_count + 1}次仍然检测到敏感内容")
                                    continue
                                    
                            except Exception as retry_e:
                                self.logger.warning(f"重试第{retry_count + 1}次异常: {str(retry_e)}")
                                continue
                        
                        # 所有重试都失败了
                        error_msg = f"视频生成失败: 敏感内容重试3次后仍然失败"
                        db_manager.log_api_call(task_id, 'doubao', 'video_generate', 'error', duration, error_msg, payload, result)
                        raise Exception(error_msg)
                    else:
                        # 没有原始prompt，无法重试
                        error_msg = f"视频生成失败: 检测到敏感内容但无法重试"
                        db_manager.log_api_call(task_id, 'doubao', 'video_generate', 'error', duration, error_msg, payload, response)
                        raise Exception(error_msg)
                else:
                    # 其他错误
                    error_msg = f"视频生成API调用失败: {response.status_code} - {response.text}"
                    db_manager.log_api_call(task_id, 'doubao', 'video_generate', 'error', duration, 
                                          request_data=payload, error_message=error_msg)
                    raise Exception(error_msg)
                    
        except Exception as e:
            self.logger.error(f"视频生成失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
    def _make_video_api_call(self, payload: Dict[str, Any]) -> tuple[requests.Response, float]:
        """
        调用视频生成API
        
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
            f"{self.base_url}/api/v3/contents/generations/tasks",
            headers=headers,
            data=json.dumps(payload)
        )
        duration = time.time() - start_time
        
        return response, duration
    
    def _update_content_prompt(self, content: List[Dict], new_prompt: str) -> List[Dict]:
        """
        更新content中的prompt
        
        Args:
            content: 原始content列表
            new_prompt: 新的prompt
            
        Returns:
            更新后的content列表
        """
        updated_content = []
        for item in content:
            if item.get('type') == 'text':
                # 更新文本prompt，保持原有的参数
                text = item.get('text', '')
                # 提取原有的参数部分（--rs, --seed, --rt, --dur, --wm等）
                import re
                params_match = re.search(r'(\s+--[^\s]+(?:\s+[^\s]+)*)$', text)
                if params_match:
                    params = params_match.group(1)
                    updated_content.append({
                        'type': 'text',
                        'text': new_prompt + params
                    })
                else:
                    updated_content.append({
                        'type': 'text',
                        'text': new_prompt
                    })
            else:
                # 保持其他类型的内容不变
                updated_content.append(item)
        
        return updated_content
    
    def generate_video_from_text(self, prompt: str, task_id: str, scene_number: int, seed: int) -> bool:
        """文生视频"""
        try:
            # 生成输出路径
            output_dir = config.get_path('temp_dir') / task_id / 'videos'
            output_path = output_dir / f"scene_{scene_number:02d}.mp4"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            self.seed = seed
            
            # 保存原始prompt用于重试
            original_prompt = prompt
            
            # 在文本提示词后追加--[parameters]，控制视频输出的规格，包括宽高比、帧率、分辨率等。
            prompt = prompt + f" --rs {self.resolution} --seed {self.seed} --rt {self.ratio}"
            if self.duration == 10:
                prompt = prompt + " --dur 10"
            if self.watermark:
                prompt = prompt + " --wm true"

            # 构建内容
            content = [{
                "type": "text",
                "text": prompt
            }]
            
            # 调用通用API方法，传递原始prompt用于重试
            if self._call_video_gen_api(task_id, self.model_pro, content, output_path, original_prompt):
                return str(output_path)
            else:
                return None
            
        except Exception as e:
            self.logger.error(f"文生视频失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
    def generate_video_from_image(self, prompt: str, image_path: str, task_id: str, scene_number: int, seed: int, novel_style: str = None) -> bool:
        """
        从图像生成视频
        
        Args:
            prompt: 文本提示词
            image_path: 输入图像路径
            output_path: 输出视频路径
            task_id: 任务ID
            seed: 随机种子
        Returns:
            是否成功
        """
        try:
            # 生成输出路径
            output_dir = config.get_path('temp_dir') / task_id / 'videos'
            output_path = output_dir / f"scene_{scene_number:02d}.mp4"
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            self.seed = seed
            
            # 保存原始prompt用于重试
            if novel_style:
                original_prompt = prompt + ", 画面风格: " + novel_style
            else:
                original_prompt = prompt
            
            # 在文本提示词后追加--[parameters]，控制视频输出的规格，包括宽高比、帧率、分辨率等。
            prompt = prompt + f" --rs {self.resolution} --seed {self.seed}"
            if self.duration == 10:
                prompt = prompt + " --dur 10"
            if self.watermark:
                prompt = prompt + " --wm true"

            # 读取图像文件并转换为base64
            image_data = "data:image/jpeg;base64,"
            with open(image_path, 'rb') as f:
                import base64
                image_data += base64.b64encode(f.read()).decode('utf-8')
        
            content = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data
                    }
                }
            ]

            # 调用通用API方法，传递原始prompt用于重试
            if self._call_video_gen_api(task_id, self.model_i2v, content, output_path, original_prompt):
                return str(output_path)
            else:
                return None
                    
        except Exception as e:
            self.logger.error(f"图生视频失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
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