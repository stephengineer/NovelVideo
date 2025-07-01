"""
火山引擎基础服务类
提供火山引擎API的基础功能
"""

import requests
import json
import time
import hashlib
import hmac
from typing import Dict, Any, Optional
from ..core import config, get_logger, db_manager


class VolcengineService:
    """火山引擎基础服务类"""
    
    def __init__(self):
        self.access_key = config.get('volcengine.access_key')
        self.secret_key = config.get('volcengine.secret_key')
        self.region = config.get('volcengine.region')
        self.endpoints = config.get('volcengine.endpoints', {})
        self.logger = get_logger('volcengine_service')
        
        if not self.access_key or not self.secret_key:
            raise ValueError("火山引擎API密钥未配置")
    
    def _generate_signature(self, method: str, url: str, headers: Dict, body: str = "") -> str:
        """生成API签名"""
        # 构建签名字符串
        string_to_sign = f"{method}\n{url}\n"
        
        # 添加头部信息
        for key, value in sorted(headers.items()):
            if key.lower().startswith('x-'):
                string_to_sign += f"{key.lower()}:{value}\n"
        
        string_to_sign += f"\n{body}"
        
        # 使用HMAC-SHA256生成签名
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, 
                     task_id: str = None) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'X-Date': str(int(time.time())),
            'X-Access-Key': self.access_key
        }
        
        body = json.dumps(data) if data else ""
        
        # 生成签名
        signature = self._generate_signature(method, url, headers, body)
        headers['X-Signature'] = signature
        
        start_time = time.time()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                timeout=120
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if task_id:
                    db_manager.log_api_call('volcengine', endpoint, 'success', duration, 
                                          request_data=data, response_data=result)
                return result
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                if task_id:
                    db_manager.log_api_call('volcengine', endpoint, 'error', duration, 
                                          request_data=data, error_message=error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            if task_id:
                db_manager.log_api_call('volcengine', endpoint, 'error', duration, 
                                      request_data=data, error_message=str(e))
            raise
    
    def _poll_task_status(self, task_id: str, poll_url: str, 
                         max_wait_time: int = 300) -> Dict[str, Any]:
        """轮询任务状态"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                result = self._make_request('GET', poll_url, task_id=task_id)
                
                status = result.get('status', 'unknown')
                if status in ['completed', 'success']:
                    return result
                elif status in ['failed', 'error']:
                    raise Exception(f"任务执行失败: {result.get('message', '未知错误')}")
                
                # 等待5秒后重试
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"轮询任务状态失败: {task_id}, 错误: {str(e)}")
                raise
        
        raise Exception(f"任务超时: {task_id}")
    
    def _download_file(self, url: str, local_path: str) -> bool:
        """下载文件"""
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            self.logger.error(f"下载文件失败: {url}, 错误: {str(e)}")
            return False 