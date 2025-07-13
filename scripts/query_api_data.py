#!/usr/bin/env python3
"""
API调用记录查询脚本
用于查询和显示数据库中的API调用记录
"""

import sys
import os
import json
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import db_manager, get_logger

def query_recent_api_calls(limit=10):
    """查询最近的API调用记录"""
    logger = get_logger('query_api_data')
    
    try:
        logger.info(f"查询最近{limit}条API调用记录...")
        
        # 这里需要根据实际的数据库查询方法来实现
        # 假设有一个query_api_calls方法
        # records = db_manager.query_api_calls(limit=limit)
        
        # 临时显示查询逻辑
        logger.info("数据库查询功能需要根据实际的数据库结构来实现")
        logger.info("可以使用以下SQL查询：")
        logger.info("SELECT * FROM api_calls ORDER BY timestamp DESC LIMIT ?")
        
    except Exception as e:
        logger.error(f"查询API调用记录失败: {str(e)}")

def query_api_calls_by_service(service, limit=10):
    """按服务类型查询API调用记录"""
    logger = get_logger('query_api_data')
    
    try:
        logger.info(f"查询{service}服务的最近{limit}条API调用记录...")
        
        # 临时显示查询逻辑
        logger.info(f"可以使用以下SQL查询：")
        logger.info(f"SELECT * FROM api_calls WHERE service = ? ORDER BY timestamp DESC LIMIT ?")
        
    except Exception as e:
        logger.error(f"查询{service}服务记录失败: {str(e)}")

def query_api_calls_by_status(status, limit=10):
    """按状态查询API调用记录"""
    logger = get_logger('query_api_data')
    
    try:
        logger.info(f"查询状态为{status}的最近{limit}条API调用记录...")
        
        # 临时显示查询逻辑
        logger.info(f"可以使用以下SQL查询：")
        logger.info(f"SELECT * FROM api_calls WHERE status = ? ORDER BY timestamp DESC LIMIT ?")
        
    except Exception as e:
        logger.error(f"查询{status}状态记录失败: {str(e)}")

def get_api_statistics():
    """获取API调用统计信息"""
    logger = get_logger('query_api_data')
    
    try:
        logger.info("获取API调用统计信息...")
        
        # 统计查询示例
        statistics_queries = [
            "SELECT COUNT(*) as total_calls FROM api_calls",
            "SELECT service, COUNT(*) as call_count FROM api_calls GROUP BY service",
            "SELECT status, COUNT(*) as status_count FROM api_calls GROUP BY status",
            "SELECT AVG(duration) as avg_duration FROM api_calls WHERE status = 'success'",
            "SELECT COUNT(*) as error_count FROM api_calls WHERE status = 'error'"
        ]
        
        logger.info("统计查询SQL：")
        for i, query in enumerate(statistics_queries, 1):
            logger.info(f"{i}. {query}")
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")

def query_sensitive_content_records():
    """查询敏感内容处理记录"""
    logger = get_logger('query_api_data')
    
    try:
        logger.info("查询敏感内容处理记录...")
        
        # 查询包含敏感内容处理的记录
        logger.info("可以使用以下SQL查询敏感内容处理记录：")
        logger.info("SELECT * FROM api_calls WHERE api_type = 'prompt_rewrite' ORDER BY timestamp DESC")
        logger.info("SELECT * FROM api_calls WHERE error_message LIKE '%敏感%' ORDER BY timestamp DESC")
        
    except Exception as e:
        logger.error(f"查询敏感内容记录失败: {str(e)}")

def query_token_usage():
    """查询token使用情况"""
    logger = get_logger('query_api_data')
    
    try:
        logger.info("查询token使用情况...")
        
        # token使用统计查询
        token_queries = [
            "SELECT SUM(usage_info->>'total_tokens') as total_tokens FROM api_calls WHERE usage_info IS NOT NULL",
            "SELECT service, SUM(usage_info->>'total_tokens') as service_tokens FROM api_calls WHERE usage_info IS NOT NULL GROUP BY service",
            "SELECT DATE(timestamp) as date, SUM(usage_info->>'total_tokens') as daily_tokens FROM api_calls WHERE usage_info IS NOT NULL GROUP BY DATE(timestamp) ORDER BY date DESC"
        ]
        
        logger.info("Token使用统计查询：")
        for i, query in enumerate(token_queries, 1):
            logger.info(f"{i}. {query}")
        
    except Exception as e:
        logger.error(f"查询token使用情况失败: {str(e)}")

def main():
    """主函数"""
    logger = get_logger('query_api_data')
    
    logger.info("API调用记录查询工具")
    logger.info("=" * 40)
    
    try:
        # 查询最近的API调用记录
        query_recent_api_calls(10)
        logger.info("-" * 40)
        
        # 按服务类型查询
        query_api_calls_by_service('doubao', 5)
        logger.info("-" * 40)
        
        # 按状态查询
        query_api_calls_by_status('success', 5)
        query_api_calls_by_status('error', 5)
        logger.info("-" * 40)
        
        # 获取统计信息
        get_api_statistics()
        logger.info("-" * 40)
        
        # 查询敏感内容处理记录
        query_sensitive_content_records()
        logger.info("-" * 40)
        
        # 查询token使用情况
        query_token_usage()
        
        logger.info("查询完成！")
        
    except Exception as e:
        logger.error(f"查询失败: {str(e)}")

if __name__ == "__main__":
    main() 