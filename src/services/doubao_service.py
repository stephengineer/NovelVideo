"""
豆包大模型API服务
负责小说分析和分镜脚本生成
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from ..core import config, get_logger, db_manager


class DoubaoService:
    """豆包大模型API服务类"""
    
    def __init__(self):
        self.api_key = config.get('doubao.api_key')
        self.base_url = config.get('doubao.base_url')
        self.model = config.get('doubao.model')
        self.max_tokens = config.get('doubao.max_tokens')
        self.temperature = config.get('doubao.temperature')
        self.logger = get_logger('doubao_service')
        
        if not self.api_key:
            raise ValueError("豆包API密钥未配置")
    
    def analyze_novel(self, novel_text: str, task_id: str) -> Dict[str, Any]:
        """
        分析小说内容，生成分镜脚本
        
        Args:
            novel_text: 小说文本内容
            task_id: 任务ID
            
        Returns:
            包含分镜脚本的字典
        """
        start_time = time.time()
        
        try:
            # 构建分析提示词
            prompt = self._build_analysis_prompt(novel_text)
            
            # 调用豆包API
            response = self._call_api(prompt, task_id)
            
            # 解析响应
            storyboard = self._parse_storyboard_response(response)
            
            duration = time.time() - start_time
            self.logger.info(f"小说分析完成 | 任务: {task_id} | 耗时: {duration:.2f}s")
            
            return storyboard
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"小说分析失败 | 任务: {task_id} | 错误: {str(e)}")
            db_manager.log_api_call('doubao', 'analyze_novel', 'error', duration, 
                                  error_message=str(e))
            raise
    
    def _build_analysis_prompt(self, novel_text: str) -> str:
        """构建分析提示词"""
        return f"""
请分析以下小说内容，并生成详细的分镜脚本。要求：

1. 将小说内容分解为多个场景（分镜）
2. 每个场景包含：
   - 场景描述（用于图像生成）
   - 对话或旁白文本（用于TTS）
   - 建议的持续时间（5-30秒）
   - 场景类型（室内/室外/特写等）

3. 分镜脚本格式要求：
   - 场景数量控制在10个以内
   - 每个场景描述要具体且适合图像生成
   - 对话文本要自然流畅
   - 总时长控制在3-5分钟

小说内容：
{novel_text}

请以JSON格式返回分镜脚本，格式如下：
{{
    "title": "小说标题",
    "summary": "小说概要",
    "scenes": [
        {{
            "scene_number": 1,
            "scene_description": "详细的场景描述，用于图像生成",
            "dialogue": "对话或旁白文本",
            "duration": 15,
            "scene_type": "室内/室外/特写",
            "mood": "场景氛围"
        }}
    ]
}}
"""
    
    def _call_api(self, prompt: str, task_id: str) -> Dict[str, Any]:
        """调用豆包API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                db_manager.log_api_call('doubao', 'chat_completions', 'success', duration)
                return result
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                db_manager.log_api_call('doubao', 'chat_completions', 'error', duration, 
                                      error_message=error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            db_manager.log_api_call('doubao', 'chat_completions', 'error', duration, 
                                  error_message=str(e))
            raise
    
    def _parse_storyboard_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析API响应，提取分镜脚本"""
        try:
            content = response['choices'][0]['message']['content']
            
            # 尝试解析JSON
            try:
                storyboard = json.loads(content)
                return storyboard
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    storyboard = json.loads(json_match.group())
                    return storyboard
                else:
                    raise Exception("无法解析分镜脚本JSON")
                    
        except Exception as e:
            self.logger.error(f"解析分镜脚本失败: {str(e)}")
            raise Exception(f"解析分镜脚本失败: {str(e)}")
    
    def generate_chapter_summary(self, chapter_text: str, task_id: str) -> str:
        """生成章节摘要"""
        start_time = time.time()
        
        try:
            prompt = f"""
请为以下小说章节生成一个简洁的摘要，用于视频标题和描述：

{chapter_text}

要求：
1. 摘要长度控制在50字以内
2. 突出章节的核心情节
3. 适合作为视频标题使用

请直接返回摘要文本，不要包含其他格式。
"""
            
            response = self._call_api(prompt, task_id)
            summary = response['choices'][0]['message']['content'].strip()
            
            duration = time.time() - start_time
            self.logger.info(f"章节摘要生成完成 | 任务: {task_id} | 耗时: {duration:.2f}s")
            
            return summary
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"章节摘要生成失败 | 任务: {task_id} | 错误: {str(e)}")
            db_manager.log_api_call('doubao', 'generate_summary', 'error', duration, 
                                  error_message=str(e))
            raise 