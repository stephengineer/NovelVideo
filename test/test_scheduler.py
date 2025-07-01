#!/usr/bin/env python3
"""
测试调度器功能
"""

import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.scheduler import TaskScheduler
from src.core import config, get_logger


def test_scheduler():
    """测试调度器功能"""
    logger = get_logger('test_scheduler')
    
    print("=== 测试调度器功能 ===")
    
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
        
        # 提交一个测试任务
        test_file = "data/input/test.txt"
        
        # 创建测试文件
        Path(test_file).parent.mkdir(parents=True, exist_ok=True)
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("这是一个测试小说文件。\n主角在森林中漫步，阳光透过树叶洒在地上。")
        
        print(f"✓ 创建测试文件: {test_file}")
        
        # 提交任务
        task_id = scheduler.submit_task('novel_video', test_file)
        print(f"✓ 任务提交成功: {task_id}")
        
        # 监控任务状态
        print("\n=== 监控任务状态 ===")
        for i in range(10):  # 监控10次
            task = scheduler.get_task_status(task_id)
            if task:
                print(f"任务状态: {task['status']} | 进度: {task.get('progress', 0):.1%}")
                
                if task['status'] in ['completed', 'failed']:
                    if task['status'] == 'failed':
                        print(f"任务失败: {task.get('error_message', '未知错误')}")
                    break
            else:
                print("无法获取任务状态")
                break
            
            time.sleep(5)  # 每5秒检查一次
        
        # 显示最终状态
        print("\n=== 最终状态 ===")
        final_stats = scheduler.get_scheduler_stats()
        print(f"调度器统计: {final_stats}")
        
        # 停止调度器
        scheduler.stop()
        print("✓ 调度器停止成功")
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        logger.error(f"测试失败: {str(e)}")
        return False
    
    return True


if __name__ == "__main__":
    success = test_scheduler()
    if success:
        print("\n✓ 所有测试通过")
    else:
        print("\n✗ 测试失败")
        sys.exit(1) 