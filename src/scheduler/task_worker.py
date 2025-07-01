"""
任务工作线程
负责执行具体的任务
"""

import threading
import time
from typing import Dict, Any, Optional
from ..core import get_logger, db_manager
from ..processors.novel_processor import NovelProcessor


class TaskWorker(threading.Thread):
    """任务工作线程类"""
    
    def __init__(self, worker_id: str, task_queue, scheduler):
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.scheduler = scheduler
        self.logger = get_logger(f'task_worker_{worker_id}')
        self.running = False
        self.current_task = None
        
        # 初始化处理器
        self.novel_processor = NovelProcessor()
    
    def run(self):
        """工作线程主循环"""
        self.running = True
        self.logger.info(f"工作线程启动 | ID: {self.worker_id}")
        
        while self.running:
            try:
                # 从队列获取任务
                task_info = self.task_queue.get_task()
                if task_info is None:
                    time.sleep(1)  # 队列为空时等待
                    continue
                
                # 执行任务
                self._execute_task(task_info)
                
            except Exception as e:
                self.logger.error(f"工作线程错误 | ID: {self.worker_id} | 错误: {str(e)}")
                time.sleep(5)  # 出错后等待5秒再继续
    
    def stop(self):
        """停止工作线程"""
        self.running = False
        self.logger.info(f"工作线程停止 | ID: {self.worker_id}")
    
    def is_running(self) -> bool:
        """检查工作线程是否运行"""
        return self.running and self.is_alive()
    
    def _execute_task(self, task_info: Dict[str, Any]):
        """执行任务"""
        task_id = task_info['task_id']
        task_type = task_info['task_type']
        input_file = task_info.get('input_file')
        config_data = task_info.get('config_data', {})
        
        self.current_task = task_id
        start_time = time.time()
        
        try:
            self.logger.info(f"开始执行任务 | 工作线程: {self.worker_id} | 任务: {task_id} | 类型: {task_type}")
            
            # 更新任务状态为运行中
            db_manager.update_task_status(task_id, 'running', started_at=time.strftime('%Y-%m-%d %H:%M:%S'))
            
            # 根据任务类型执行不同的处理
            if task_type == 'novel_video':
                success = self._process_novel_video(task_id, input_file, config_data)
            else:
                raise Exception(f"不支持的任务类型: {task_type}")
            
            # 更新任务状态
            if success:
                duration = time.time() - start_time
                db_manager.update_task_status(task_id, 'completed', 
                                            completed_at=time.strftime('%Y-%m-%d %H:%M:%S'))
                self.logger.info(f"任务执行完成 | 工作线程: {self.worker_id} | 任务: {task_id} | 耗时: {duration:.2f}s")
            else:
                raise Exception("任务执行失败")
                
        except Exception as e:
            duration = time.time() - start_time
            error_message = str(e)
            db_manager.update_task_status(task_id, 'failed', 
                                        error_message=error_message)
            self.logger.error(f"任务执行失败 | 工作线程: {self.worker_id} | 任务: {task_id} | 错误: {error_message} | 耗时: {duration:.2f}s")
        
        finally:
            self.current_task = None
            # 从队列中移除任务
            self.task_queue.remove_task(task_id)
    
    def _process_novel_video(self, task_id: str, input_file: str, config_data: Dict) -> bool:
        """处理小说视频生成任务"""
        try:
            # 使用小说处理器处理任务
            return self.novel_processor.process_novel(task_id, input_file, config_data)
        except Exception as e:
            self.logger.error(f"小说视频处理失败 | 任务: {task_id} | 错误: {str(e)}")
            return False
    
    def get_worker_status(self) -> Dict[str, Any]:
        """获取工作线程状态"""
        return {
            'worker_id': self.worker_id,
            'running': self.running,
            'alive': self.is_alive(),
            'current_task': self.current_task
        } 