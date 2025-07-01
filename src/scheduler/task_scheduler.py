"""
任务调度器
负责任务的调度和管理
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..core import config, get_logger, db_manager
from .task_queue import TaskQueue
from .task_worker import TaskWorker


class TaskScheduler:
    """任务调度器类"""
    
    def __init__(self):
        self.scheduler_config = config.get('scheduler', {})
        self.max_concurrent_tasks = self.scheduler_config.get('max_concurrent_tasks', 3)
        self.task_timeout = self.scheduler_config.get('task_timeout', 3600)
        self.retry_attempts = self.scheduler_config.get('retry_attempts', 3)
        self.retry_delay = self.scheduler_config.get('retry_delay', 300)
        
        self.logger = get_logger('task_scheduler')
        self.task_queue = TaskQueue()
        self.workers: List[TaskWorker] = []
        self.running_tasks: Dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent_tasks)
        
        self.logger.info(f"任务调度器初始化完成 | 最大并发数: {self.max_concurrent_tasks}")
    
    def start(self):
        """启动调度器"""
        self.logger.info("启动任务调度器")
        
        # 启动工作线程
        for i in range(self.max_concurrent_tasks):
            worker = TaskWorker(f"worker-{i+1}", self.task_queue, self)
            self.workers.append(worker)
            worker.start()  # 使用start()而不是run()
        
        # 启动监控线程
        self._start_monitor()
    
    def stop(self):
        """停止调度器"""
        self.logger.info("停止任务调度器")
        
        # 停止任务队列
        self.task_queue.stop()
        
        # 停止所有工作线程
        for worker in self.workers:
            worker.stop()
        
        # 等待所有工作线程结束
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=5)  # 最多等待5秒
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        self.logger.info("任务调度器已停止")
    
    def submit_task(self, task_type: str, input_file: str = None, 
                   config_data: Dict = None) -> str:
        """
        提交新任务
        
        Args:
            task_type: 任务类型
            input_file: 输入文件路径
            config_data: 任务配置
            
        Returns:
            任务ID
        """
        import uuid
        task_id = f"{task_type}_{uuid.uuid4().hex[:8]}"
        
        # 创建任务记录
        if db_manager.create_task(task_id, task_type, input_file, config_data):
            # 添加到队列
            self.task_queue.add_task(task_id, task_type, input_file, config_data)
            self.logger.info(f"任务已提交 | ID: {task_id} | 类型: {task_type}")
            return task_id
        else:
            raise Exception(f"创建任务失败: {task_id}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        return db_manager.get_task(task_id)
    
    def get_pending_tasks(self) -> List[Dict]:
        """获取待处理任务列表"""
        return db_manager.get_tasks_by_status('pending')
    
    def get_running_tasks(self) -> List[Dict]:
        """获取运行中任务列表"""
        return db_manager.get_tasks_by_status('running')
    
    def get_completed_tasks(self) -> List[Dict]:
        """获取已完成任务列表"""
        return db_manager.get_tasks_by_status('completed')
    
    def get_failed_tasks(self) -> List[Dict]:
        """获取失败任务列表"""
        return db_manager.get_tasks_by_status('failed')
    
    def retry_task(self, task_id: str) -> bool:
        """重试失败的任务"""
        task = db_manager.get_task(task_id)
        if task and task['status'] == 'failed':
            # 重置任务状态
            db_manager.update_task_status(task_id, 'pending', error_message=None)
            # 重新添加到队列
            self.task_queue.add_task(task_id, task['task_type'], 
                                   task['input_file'], task.get('config'))
            self.logger.info(f"任务重试 | ID: {task_id}")
            return True
        return False
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.running_tasks:
            # 标记任务为取消状态
            db_manager.update_task_status(task_id, 'cancelled')
            self.logger.info(f"任务已取消 | ID: {task_id}")
            return True
        return False
    
    def _start_monitor(self):
        """启动监控线程"""
        def monitor():
            while True:
                try:
                    # 检查超时任务
                    self._check_timeout_tasks()
                    
                    # 检查失败任务
                    self._check_failed_tasks()
                    
                    # 清理完成的任务
                    self._cleanup_completed_tasks()
                    
                    time.sleep(30)  # 每30秒检查一次
                    
                except Exception as e:
                    self.logger.error(f"监控线程错误: {str(e)}")
                    time.sleep(60)  # 出错后等待1分钟再继续
        
        import threading
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def _check_timeout_tasks(self):
        """检查超时任务"""
        running_tasks = self.get_running_tasks()
        current_time = time.time()
        
        for task in running_tasks:
            if 'started_at' in task and task['started_at']:
                start_time = time.mktime(time.strptime(task['started_at'], '%Y-%m-%d %H:%M:%S'))
                if current_time - start_time > self.task_timeout:
                    self.logger.warning(f"任务超时 | ID: {task['id']}")
                    db_manager.update_task_status(task['id'], 'failed', 
                                                error_message='任务执行超时')
    
    def _check_failed_tasks(self):
        """检查失败任务的重试"""
        failed_tasks = self.get_failed_tasks()
        
        for task in failed_tasks:
            # 这里可以实现自动重试逻辑
            # 暂时只是记录日志
            self.logger.info(f"失败任务 | ID: {task['id']} | 错误: {task.get('error_message', '未知错误')}")
    
    def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        # 这里可以实现清理逻辑，比如删除临时文件等
        pass
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        return {
            'total_workers': len(self.workers),
            'active_workers': len([w for w in self.workers if w.is_running()]),
            'queue_size': self.task_queue.size(),
            'running_tasks': len(self.get_running_tasks()),
            'pending_tasks': len(self.get_pending_tasks()),
            'completed_tasks': len(self.get_completed_tasks()),
            'failed_tasks': len(self.get_failed_tasks())
        } 