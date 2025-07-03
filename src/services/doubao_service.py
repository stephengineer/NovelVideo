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
        self.base_url = config.get('doubao.base_url')
        self.api_key = config.get('doubao.api_key')
        self.model = config.get('doubao.model')
        self.thinking = config.get('doubao.thinking')
        self.max_tokens = config.get('doubao.max_tokens')
        self.frequency_penalty = config.get('doubao.frequency_penalty')
        self.temperature = config.get('doubao.temperature')
        self.top_p = config.get('doubao.top_p')
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
            # 记录分析失败的API调用
            db_manager.log_api_call(
                task_id,
                'doubao', 
                'analyze_novel', 
                'error',
                duration,
                str(e)
            )
            raise
    
    def _build_analysis_prompt(self, novel_text: str) -> str:
        """构建分析提示词"""
        return f"""
分析给定的小说内容，并生成详细的分镜脚本。请仔细阅读小说内容，按照要求进行处理。以下是具体要求：
1. 将小说内容分解为多个场景(分镜), 场景数量小于20个
2. 每个场景包含：画面内容、旁白内容
<小说内容>
{novel_text}
</小说内容>
"""
    
    def _call_api(self, prompt: str, task_id: str) -> Dict[str, Any]:
        """调用豆包API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # 构建请求数据
        payload = {
            'model': self.model,
            'messages': [
                {
                    "role": "system",
                    "content": "你是一位小说分析、解读专家"
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            "thinking": {
                "type": self.thinking
            },
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "novel_analyze",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "小说概要"
                            },
                            "style": {
                                "type": "string",
                                "description": "小说风格"
                            },
                            "scenes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "scene_number": {
                                            "type": "integer",
                                            "description": "场景编号"
                                        },
                                        "scene_content": {
                                            "type": "string",
                                            "description": "画面内容"
                                        },
                                        "scene_description": {
                                            "type": "string",
                                            "description": "场景描述, 小于100字"
                                        }
                                    },
                                    "required": [
                                        "scene_number",
                                        "scene_content",
                                        "scene_description"
                                    ],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": [
                            "summary",
                            "style",
                            "scenes"
                        ],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v3/chat/completions",
                headers=headers,
                data=json.dumps(payload)
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # 提取token使用情况
                usage_info = {}
                if 'usage' in result:
                    usage_info = {
                        'completion_tokens': result['usage'].get('completion_tokens', 0),
                        'prompt_tokens': result['usage'].get('prompt_tokens', 0),
                        'total_tokens': result['usage'].get('total_tokens', 0)
                    }
                
                # 记录成功的API调用，包含请求、响应数据和token使用情况
                db_manager.log_api_call(
                    task_id,
                    'doubao', 
                    'chat_completions', 
                    'success', 
                    duration,
                    request_data=payload,
                    response_data=result,
                    usage_info=usage_info
                )
                return result
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                # 记录失败的API调用，包含请求数据
                db_manager.log_api_call(
                    task_id,
                    'doubao', 
                    'chat_completions', 
                    'error', 
                    duration,
                    error_msg,
                    payload
                )
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            # 记录网络异常的API调用，包含请求数据
            db_manager.log_api_call(
                task_id,
                'doubao', 
                'chat_completions', 
                'error', 
                duration,
                str(e),
                payload
            )
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
            # 记录摘要生成失败的API调用
            db_manager.log_api_call(
                task_id,
                'doubao', 
                'generate_summary', 
                'error', 
                duration,
                str(e)
            )
            raise 