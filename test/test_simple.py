#!/usr/bin/env python3
"""
简单测试调度器启动和停止
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.scheduler import TaskScheduler
from src.core import get_logger


def test_simple():
    """简单测试"""
    logger = get_logger('test_simple')
    
    print("=== 简单测试调度器 ===")
    
    try:
        # 创建调度器
        scheduler = TaskScheduler()
        print("✓ 调度器创建成功")
        
        # 启动调度器
        scheduler.start()
        print("✓ 调度器启动成功")
        
        # 等待一下让worker启动
        time.sleep(2)
        
        # 检查调度器状态
        stats = scheduler.get_scheduler_stats()
        print(f"✓ 调度器状态: {stats}")
        
        # 等待5秒
        print("等待5秒...")
        time.sleep(5)
        
        # 停止调度器
        scheduler.stop()
        print("✓ 调度器停止成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        logger.error(f"测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_simple()
    if success:
        print("\n✓ 测试通过")
    else:
        print("\n✗ 测试失败")
        sys.exit(1) 