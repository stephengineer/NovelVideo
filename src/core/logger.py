"""
日志管理模块
负责统一的日志记录和管理
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional
from .config import config


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        self.logger = logger
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志配置"""
        # 移除默认的日志处理器
        self.logger.remove()
        
        # 获取日志配置
        log_config = config.get('logging', {})
        log_level = log_config.get('level', 'INFO')
        log_format = log_config.get('format', 
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}")
        
        # 控制台输出
        self.logger.add(
            sys.stdout,
            format=log_format,
            level=log_level,
            colorize=True
        )
        
        # 文件输出
        logs_dir = config.get_path('logs_dir')
        if logs_dir:
            log_file = logs_dir / "novel_video_{time:YYYY-MM-DD}.log"
            
            # 主要日志文件
            self.logger.add(
                log_file,
                format=log_format,
                level=log_level,
                rotation=log_config.get('rotation', '100 MB'),
                retention=log_config.get('retention', '30 days'),
                compression=log_config.get('compression', 'zip'),
                encoding='utf-8'
            )
            
            # 错误日志文件
            error_log_file = logs_dir / "error_{time:YYYY-MM-DD}.log"
            self.logger.add(
                error_log_file,
                format=log_format,
                level="ERROR",
                rotation=log_config.get('rotation', '100 MB'),
                retention=log_config.get('retention', '30 days'),
                compression=log_config.get('compression', 'zip'),
                encoding='utf-8'
            )
    
    def get_logger(self, name: str = None):
        """获取日志记录器"""
        if name:
            return self.logger.bind(name=name)
        return self.logger
    
    def log_task_start(self, task_id: str, task_type: str, **kwargs):
        """记录任务开始"""
        self.logger.info(f"任务开始 | ID: {task_id} | 类型: {task_type}", extra=kwargs)
    
    def log_task_complete(self, task_id: str, task_type: str, duration: float, **kwargs):
        """记录任务完成"""
        self.logger.info(f"任务完成 | ID: {task_id} | 类型: {task_type} | 耗时: {duration:.2f}s", extra=kwargs)
    
    def log_task_error(self, task_id: str, task_type: str, error: Exception, **kwargs):
        """记录任务错误"""
        self.logger.error(f"任务错误 | ID: {task_id} | 类型: {task_type} | 错误: {str(error)}", extra=kwargs)
    
    def log_api_call(self, service: str, endpoint: str, status: str, duration: float, **kwargs):
        """记录API调用"""
        self.logger.info(f"API调用 | 服务: {service} | 端点: {endpoint} | 状态: {status} | 耗时: {duration:.2f}s", extra=kwargs)
    
    def log_file_operation(self, operation: str, file_path: str, status: str, **kwargs):
        """记录文件操作"""
        self.logger.info(f"文件操作 | 操作: {operation} | 文件: {file_path} | 状态: {status}", extra=kwargs)


# 全局日志管理器实例
log_manager = LoggerManager()


def get_logger(name: str = None):
    """获取日志记录器的便捷函数"""
    return log_manager.get_logger(name) 