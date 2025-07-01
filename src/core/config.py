"""
配置管理模块
负责加载和管理项目配置
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 加载环境变量
        load_dotenv()
        
        # 读取YAML配置文件
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        # 替换环境变量
        self._replace_env_vars(self.config)
        
        # 创建必要的目录
        self._create_directories()
    
    def _replace_env_vars(self, data: Any):
        """递归替换配置中的环境变量"""
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self._replace_env_vars(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                data[i] = self._replace_env_vars(item)
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            env_var = data[2:-1]
            return os.getenv(env_var, data)
        return data
    
    def _create_directories(self):
        """创建必要的目录"""
        paths = self.config.get('paths', {})
        for path_key, path_value in paths.items():
            if isinstance(path_value, str):
                Path(path_value).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_path(self, path_key: str) -> Path:
        """获取路径配置"""
        path_value = self.get(f"paths.{path_key}")
        return Path(path_value) if path_value else None
    
    def reload(self):
        """重新加载配置"""
        self._load_config()


# 全局配置实例
config = ConfigManager() 