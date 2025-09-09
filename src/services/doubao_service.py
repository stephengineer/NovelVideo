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
仔细阅读小说, 按照时间顺序和故事结构进行分类和重新排列。根据情节的发展和角色的心理变化, 理解剧本的核心内涵和叙述逻辑。分镜数量小于20个。
<小说内容>
{novel_text}
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
                    "content": "你是小说拆解专家,擅长将小说进行分析、分解及转化为分镜脚本。"
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
                                "description": "小说风格",
                                "enum": ["武侠古风", "都市言情", "悬疑推理", "民间故事", "其他"]
                            },
                            "scenes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "scene_number": {
                                            "type": "integer",
                                            "description": "分镜编号"
                                        },
                                        "scene_description": {
                                            "type": "string",
                                            "description": "场景描述"
                                        }
                                    },
                                    "required": [
                                        "scene_number",
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
    
    def rewrite_prompt(self, original_prompt: str, retry_count: int, task_id: str = None) -> str:
        """
        使用AI模型改写敏感prompt，尝试避免敏感内容检测
        
        Args:
            original_prompt: 原始prompt
            retry_count: 重试次数（1-3）
            task_id: 任务ID（可选，用于日志记录）
            
        Returns:
            改写后的prompt
        """
        try:
            # 根据重试次数构建不同的改写指令
            if retry_count == 1:
                instruction = f"""
请将以下图像描述改写为适合图像生成的安全版本，避免敏感内容：
原始描述：{original_prompt}

要求：
1. 保持场景的核心内容和氛围
2. 将可能敏感的内容替换为更温和的表达
3. 添加艺术风格修饰，使其适合全年龄段
4. 保持描述的生动性和画面感

请直接返回改写后的描述，不要包含其他解释。
"""
            elif retry_count == 2:
                instruction = f"""
请将以下图像描述进一步改写，使其更加温和和安全：
原始描述：{original_prompt}

要求：
1. 简化描述，移除所有可能敏感的元素
2. 强调温馨、和谐、正能量的氛围
3. 使用更加温和的词汇和表达方式
4. 确保完全适合全年龄段观看

请直接返回改写后的描述，不要包含其他解释。
"""
            else:  # retry_count == 3
                instruction = f"""
请将以下图像描述完全重写为最安全的版本：
原始描述：{original_prompt}

要求：
1. 提取场景的核心元素（人物、环境、动作等）
2. 使用最安全、最温和的描述方式
3. 强调温馨和谐的氛围
4. 确保完全没有任何敏感内容
5. 适合所有年龄段观看

请直接返回改写后的描述，不要包含其他解释。
"""
            
            # 调用AI模型进行改写
            rewritten_prompt = self._call_rewrite_api(instruction, task_id)
            
            if rewritten_prompt:
                self.logger.info(f"AI模型改写成功 | 重试次数: {retry_count} | 原始: {original_prompt} | 改写后: {rewritten_prompt}")
                return rewritten_prompt
            else:
                # 如果AI模型调用失败，使用备用方案
                return self._fallback_rewrite_prompt(original_prompt, retry_count)
                
        except Exception as e:
            self.logger.error(f"AI模型改写失败: {str(e)}")
            # 使用备用方案
            return self._fallback_rewrite_prompt(original_prompt, retry_count)
    
    def _call_rewrite_api(self, instruction: str, task_id: str = None) -> Optional[str]:
        """
        调用AI模型进行prompt改写
        
        Args:
            instruction: 改写指令
            task_id: 任务ID（可选）
            
        Returns:
            改写后的prompt，失败时返回None
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是一个专业的图像描述改写助手，擅长将敏感内容改写为适合图像生成的安全版本。'
                    },
                    {
                        'role': 'user',
                        'content': instruction
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 500
            }
            
            start_time = time.time()
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
                
                # 记录API调用
                if task_id:
                    db_manager.log_api_call(
                        task_id,
                        'doubao',
                        'prompt_rewrite',
                        'success',
                        duration,
                        request_data=payload,
                        response_data=result,
                        usage_info=usage_info
                    )
                
                if 'choices' in result and len(result['choices']) > 0:
                    rewritten_prompt = result['choices'][0]['message']['content'].strip()
                    # 移除可能的引号
                    rewritten_prompt = rewritten_prompt.strip('"').strip("'")
                    return rewritten_prompt
                else:
                    self.logger.error("AI模型响应格式错误")
                    return None
            else:
                error_msg = f"AI模型调用失败: {response.status_code} - {response.text}"
                if task_id:
                    db_manager.log_api_call(
                        task_id,
                        'doubao',
                        'prompt_rewrite',
                        'error',
                        duration,
                        error_msg,
                        payload
                    )
                self.logger.error(error_msg)
                return None
                
        except Exception as e:
            self.logger.error(f"调用AI模型失败: {str(e)}")
            return None
    
    def _fallback_rewrite_prompt(self, original_prompt: str, retry_count: int) -> str:
        """
        备用prompt改写方案（当AI模型调用失败时使用）
        
        Args:
            original_prompt: 原始prompt
            retry_count: 重试次数
            
        Returns:
            改写后的prompt
        """
        # 敏感词汇替换映射
        sensitive_replacements = {
            # 暴力相关
            '打架': '争执',
            '斗殴': '冲突',
            '暴力': '激烈',
            '血腥': '红色',
            '死亡': '失去意识',
            '杀人': '制服',
            '伤害': '制服',
            '攻击': '防御',
            '战斗': '对峙',
            '战争': '冲突',
            
            # 不当内容
            '裸露': '穿着',
            '性感': '优雅',
            '诱惑': '吸引',
            '暧昧': '亲密',
            
            # 其他敏感词
            '政治': '社会',
            '宗教': '信仰',
            '种族': '文化',
            '歧视': '差异'
        }
        
        # 根据重试次数采用不同的改写策略
        if retry_count == 1:
            # 第一次重试：替换敏感词汇
            new_prompt = original_prompt
            for sensitive_word, replacement in sensitive_replacements.items():
                if sensitive_word in new_prompt:
                    new_prompt = new_prompt.replace(sensitive_word, replacement)
                    self.logger.info(f"备用方案替换敏感词: {sensitive_word} -> {replacement}")
            
            # 添加艺术风格修饰
            new_prompt += "，艺术风格，卡通化，适合全年龄段"
            
        elif retry_count == 2:
            # 第二次重试：简化描述，移除可能敏感的部分
            new_prompt = original_prompt
            
            # 移除可能敏感的动词
            sensitive_verbs = ['打', '杀', '伤', '攻击', '战斗', '战争']
            for verb in sensitive_verbs:
                if verb in new_prompt:
                    new_prompt = new_prompt.replace(verb, '面对')
            
            # 添加更多修饰词
            new_prompt += "，温馨场景，和谐氛围，正能量"
            
        else:  # retry_count == 3
            # 第三次重试：完全重写，使用最安全的描述
            # 提取场景的核心元素
            core_elements = []
            
            # 提取人物
            if '人' in original_prompt or '者' in original_prompt or '员' in original_prompt:
                core_elements.append('人物')
            
            # 提取环境
            if '室' in original_prompt or '外' in original_prompt:
                core_elements.append('环境')
            
            # 提取动作
            if '站' in original_prompt or '坐' in original_prompt or '走' in original_prompt:
                core_elements.append('动作')
            
            # 构建最安全的prompt
            if core_elements:
                new_prompt = f"温馨的{''.join(core_elements)}场景，和谐氛围，适合全年龄段观看"
            else:
                new_prompt = "温馨和谐的场景，适合全年龄段观看"
        
        self.logger.info(f"备用方案Prompt改写 | 重试次数: {retry_count} | 原始: {original_prompt} | 改写后: {new_prompt}")
        return new_prompt 