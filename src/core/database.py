"""
数据库管理模块
负责任务状态、文件信息等的持久化存储
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from .config import config
from .logger import get_logger


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.db_path = config.get('database.path', 'data/database/novel_video.db')
        self.logger = get_logger('database')
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        # 确保数据库目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 创建表
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_file TEXT,
                    output_file TEXT,
                    config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    progress REAL DEFAULT 0.0
                )
            ''')
            
            # 分镜脚本表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS storyboards (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    scene_number INTEGER NOT NULL,
                    scene_description TEXT,
                    tts_audio_path TEXT,
                    audio_words TEXT,
                    audio_duration REAL,
                    image_path TEXT,
                    video_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            ''')
            
            # 文件信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    checksum TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            ''')
            
            # API调用记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    service TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration REAL,
                    error_message TEXT,
                    request_data TEXT,
                    response_data TEXT,
                    usage_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def create_task(self, task_id: str, task_type: str, input_file: str = None, 
                   config_data: Dict = None) -> bool:
        """创建新任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tasks (id, task_type, status, input_file, config)
                    VALUES (?, ?, ?, ?, ?)
                ''', (task_id, task_type, 'pending', input_file, 
                     json.dumps(config_data) if config_data else None))
                conn.commit()
                self.logger.info(f"创建任务: {task_id}")
                return True
        except Exception as e:
            self.logger.error(f"创建任务失败: {task_id}, 错误: {str(e)}")
            return False
    
    def update_task_status(self, task_id: str, status: str, **kwargs) -> bool:
        """更新任务状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建更新字段
                update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
                params = [status]
                
                if 'started_at' in kwargs:
                    update_fields.append('started_at = ?')
                    params.append(kwargs['started_at'])
                
                if 'completed_at' in kwargs:
                    update_fields.append('completed_at = ?')
                    params.append(kwargs['completed_at'])
                
                if 'error_message' in kwargs:
                    update_fields.append('error_message = ?')
                    params.append(kwargs['error_message'])
                
                if 'progress' in kwargs:
                    update_fields.append('progress = ?')
                    params.append(kwargs['progress'])
                
                if 'output_file' in kwargs:
                    update_fields.append('output_file = ?')
                    params.append(kwargs['output_file'])
                
                params.append(task_id)
                
                cursor.execute(f'''
                    UPDATE tasks SET {', '.join(update_fields)}
                    WHERE id = ?
                ''', params)
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"更新任务状态失败: {task_id}, 错误: {str(e)}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"获取任务失败: {task_id}, 错误: {str(e)}")
            return None
    
    def get_tasks_by_status(self, status: str) -> List[Dict]:
        """根据状态获取任务列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC', (status,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"获取任务列表失败: {status}, 错误: {str(e)}")
            return []
    
    def add_storyboard(self, task_id: str, scene_number: int, scene_description: str) -> str:
        """添加分镜脚本"""
        try:
            storyboard_id = f"{task_id}_scene_{scene_number}"
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO storyboards (id, task_id, scene_number, scene_description)
                    VALUES (?, ?, ?, ?)
                ''', (storyboard_id, task_id, scene_number, scene_description))
                conn.commit()
                return storyboard_id
        except Exception as e:
            self.logger.error(f"添加分镜脚本失败: {task_id}, 错误: {str(e)}")
            return None
    
    def update_storyboard_assets(self, storyboard_id: str, **kwargs) -> bool:
        """更新分镜脚本的素材路径"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                update_fields = []
                params = []
                
                for key, value in kwargs.items():
                    if key in ['tts_audio_path', 'audio_words', 'audio_duration', 'image_path', 'video_path']:
                        update_fields.append(f'{key} = ?')
                        params.append(value)
                
                if not update_fields:
                    return False
                
                params.append(storyboard_id)
                cursor.execute(f'''
                    UPDATE storyboards SET {', '.join(update_fields)}
                    WHERE id = ?
                ''', params)
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"更新分镜脚本失败: {storyboard_id}, 错误: {str(e)}")
            return False
    
    def get_storyboards(self, task_id: str) -> List[Dict]:
        """获取任务的分镜脚本列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM storyboards WHERE task_id = ? 
                    ORDER BY scene_number
                ''', (task_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"获取分镜脚本失败: {task_id}, 错误: {str(e)}")
            return []
    
    def get_audio_words(self, task_id: str, scene_number: int) -> str:
        """获取音频字数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT audio_words FROM storyboards WHERE task_id = ? AND scene_number = ?', (task_id, scene_number))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            self.logger.error(f"获取音频字数失败: {task_id}, 错误: {str(e)}")
            return None
    
    def get_audio_duration(self, task_id: str, scene_number: int) -> float:
        """获取音频时长"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT audio_duration FROM storyboards WHERE task_id = ? AND scene_number = ?', (task_id, scene_number))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            self.logger.error(f"获取音频时长失败: {task_id}, 错误: {str(e)}")
            return None

    def add_file_record(self, task_id: str, file_type: str, file_path: str,
                       file_size: int = None, checksum: str = None) -> bool:
        """添加文件记录"""
        try:
            file_id = f"{task_id}_{file_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO files (id, task_id, file_type, file_path, file_size, checksum)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (file_id, task_id, file_type, file_path, file_size, checksum))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"添加文件记录失败: {task_id}, 错误: {str(e)}")
            return False
    
    def log_api_call(self, task_id: str, service: str, endpoint: str, status: str, 
                    duration: float, error_message: str = None, request_data: str = None, 
                    response_data: str = None,
                    usage_info: Dict = None) -> bool:
        """记录API调用"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO api_calls (task_id, service, endpoint, status, duration, 
                                         error_message, request_data, response_data, usage_info)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (task_id, service, endpoint, status, duration,
                     error_message,
                     json.dumps(request_data) if request_data else None,
                     json.dumps(response_data) if response_data else None,
                     json.dumps(usage_info) if usage_info else None))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"记录API调用失败: {service}, 错误: {str(e)}")
            return False


    def get_api_calls(self, task_id: str = None, service: str = None, status: str = None, limit: int = 100) -> List[Dict]:
        """获取API调用记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = 'SELECT * FROM api_calls WHERE 1=1'
                params = []
                
                if service:
                    query += ' AND service = ?'
                    params.append(service)
                
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"获取API调用记录失败: {str(e)}")
            return []
    
    def get_api_call_by_id(self, call_id: int) -> Optional[Dict]:
        """根据ID获取API调用记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM api_calls WHERE id = ?', (call_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"获取API调用记录失败: {call_id}, 错误: {str(e)}")
            return None


# 全局数据库管理器实例
db_manager = DatabaseManager() 