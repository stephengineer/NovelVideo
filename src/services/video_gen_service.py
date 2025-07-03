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
        self.base_url = config.get('doubao.base_url')
        self.api_key = config.get('doubao.api_key')
        self.model = config.get('video_gen.model')
        self.callback_url = config.get('video_gen.callback_url')
        self.resolution = config.get('video_gen.resolution')
        self.ratio = config.get('video_gen.ratio')
        self.duration = config.get('video_gen.duration')
        self.watermark = config.get('video_gen.watermark')
        self.seed = config.get('video_gen.seed')
        self.logger = get_logger('video_gen_service')
        
        if not self.api_key:
            raise ValueError("豆包API密钥未配置")
    
    def generate_video_from_image(self, prompt: str, image_path: str, output_path: str, task_id: str, seed: int) -> bool:
        """
        从图像生成视频
        
        Args:
            image_path: 输入图像路径
            output_path: 输出视频路径
            task_id: 任务ID
            seed: 随机种子
        Returns:
            是否成功
        """
        try:
            # 验证seed取值范围取值范围为 [0, 2147483647]
            if seed >= 0 and seed <= 2147483647:
                self.seed = seed
            
            # 在文本提示词后追加--[parameters]，控制视频输出的规格，包括宽高比、帧率、分辨率等。
            prompt = prompt + f" --rs {self.resolution} --seed {self.seed}"
            if self.duration == 10:
                prompt = prompt + " --dur 10"
            if self.watermark:
                prompt = prompt + " --wm true"

            infos = list()

            # 读取图像文件并转换为base64
            if image_path == "":
                prompt = prompt + f" --rt {self.ratio}"
            else:
                image_data = "data:image/jpeg;base64,"
                with open(image_path, 'rb') as f:
                    import base64
                    image_data += base64.b64encode(f.read()).decode('utf-8')
            
                infos.append({
                    "type": "image",
                    "image": image_data
                })

            infos.append({
                "type": "text",
                "text": prompt
            })

            # 构建请求数据
            payload = {
                'model': self.model,
                'content': infos
            }
            
            # 调用豆包图生视频API
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
            
            if response.status_code == 200:
                result = response.json()

                # 异步任务，需要轮询
                video_task_id = result.get('id')
                poll_url = f"{self.base_url}/api/v3/contents/generations/tasks/{video_task_id}"
                final_result = self._poll_task_status(video_task_id, poll_url)
                
                # 下载视频文件
                video_url = final_result.get('content').get('video_url')
                if video_url and self._download_file(video_url, output_path):
                    # 提取token使用情况
                    usage_info = {}
                    if 'usage' in final_result:
                        usage_info = {
                            'completion_tokens': final_result['usage'].get('completion_tokens', 0),
                            'total_tokens': final_result['usage'].get('total_tokens', 0)
                        }
                    self.logger.info(f"视频生成成功 | 任务: {task_id} | 文件: {output_path}")
                    db_manager.log_api_call(task_id, 'doubao', 'video_generate', 'success', duration, 
                                            request_data=payload, response_data=final_result, usage_info=usage_info)
                    return True
                else:
                    raise Exception("下载视频文件失败")

            else:
                error_msg = f"图生视频API调用失败: {response.status_code} - {response.text}"
                db_manager.log_api_call(task_id, 'doubao', 'video_generate', 'error', duration, 
                                      error_message=error_msg)
                raise Exception(error_msg)
                    
        except Exception as e:
            self.logger.error(f"视频生成失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
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
    
    def generate_scene_video(self, prompt: str, image_path: str, task_id: str, scene_number: int, seed: int) -> Optional[str]:
        """
        为场景生成视频
        
        Args:
            image_path: 场景图像路径
            task_id: 任务ID
            scene_number: 场景编号
            seed: 随机种子
        Returns:
            视频文件路径
        """
        try:
            # 生成输出路径
            output_dir = config.get_path('temp_dir') / task_id / 'videos'
            output_path = output_dir / f"scene_{scene_number:02d}.mp4"

            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 生成视频
            if self.generate_video_from_image(str(prompt), str(image_path), str(output_path), task_id, seed):
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