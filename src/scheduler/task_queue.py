"""
任务队列
负责任务的排队和管理
"""

import queue
import threading
from typing import Dict, Any, Optional
from ..core import get_logger


class TaskQueue:
    """任务队列类"""
    
    def __init__(self):
        self.queue = queue.Queue()
        self.task_info: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.logger = get_logger('task_queue')
    
    def add_task(self, task_id: str, task_type: str, input_file: str = None, 
                config_data: Dict = None):
        """添加任务到队列"""
        task_info = {
            'task_id': task_id,
            'task_type': task_type,
            'input_file': input_file,
            'config_data': config_data,
            'priority': 1  # 默认优先级
        }
        
        with self.lock:
            self.task_info[task_id] = task_info
            self.queue.put(task_info)
        
        self.logger.info(f"任务已添加到队列 | ID: {task_id} | 类型: {task_type}")
    
    def get_task(self) -> Optional[Dict[str, Any]]:
        """从队列获取任务"""
        try:
            task_info = self.queue.get(timeout=1)  # 1秒超时
            return task_info
        except queue.Empty:
            return None
    
    def remove_task(self, task_id: str) -> bool:
        """从队列移除任务"""
        with self.lock:
            if task_id in self.task_info:
                del self.task_info[task_id]
                return True
        return False
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        with self.lock:
            return self.task_info.get(task_id)
    
    def size(self) -> int:
        """获取队列大小"""
        return self.queue.qsize()
    
    def is_empty(self) -> bool:
        """检查队列是否为空"""
        return self.queue.empty()
    
    def clear(self):
        """清空队列"""
        with self.lock:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break
            self.task_info.clear()
        
        self.logger.info("任务队列已清空")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        with self.lock:
            return {
                'queue_size': self.size(),
                'task_count': len(self.task_info),
                'is_empty': self.is_empty()
            } 