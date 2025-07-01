#!/usr/bin/env python3
"""
小说视频生成系统使用示例
Example usage of Novel Video Generator System
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core import config, get_logger
from src.scheduler import TaskScheduler


def example_basic_usage():
    """基本使用示例"""
    logger = get_logger('example')
    
    # 创建任务调度器
    scheduler = TaskScheduler()
    
    # 启动调度器
    scheduler.start()
    
    try:
        # 示例小说文件路径
        novel_file = "data/input/example_novel.txt"
        
        # 创建示例小说文件
        create_example_novel(novel_file)
        
        # 提交任务
        task_id = scheduler.submit_task('novel_video', novel_file)
        logger.info(f"任务已提交: {task_id}")
        
        # 等待任务完成（在实际使用中，这应该异步处理）
        import time
        while True:
            task = scheduler.get_task_status(task_id)
            if task['status'] == 'completed':
                logger.info(f"任务完成: {task_id}")
                logger.info(f"输出文件: {task['output_file']}")
                break
            elif task['status'] == 'failed':
                logger.error(f"任务失败: {task_id}")
                logger.error(f"错误信息: {task['error_message']}")
                break
            else:
                progress = task.get('progress', 0) * 100
                logger.info(f"任务进度: {progress:.1f}%")
                time.sleep(10)  # 等待10秒后再次检查
                
    finally:
        # 停止调度器
        scheduler.stop()


def create_example_novel(file_path):
    """创建示例小说文件"""
    content = """
第一章 初遇

春日的午后，阳光透过树叶洒在小径上，形成斑驳的光影。小美漫步在花园里，欣赏着周围盛开的花朵。

突然，一只美丽的蝴蝶飞到了她的面前，翅膀上闪烁着七彩的光芒。小美被这美丽的景象吸引住了，她小心翼翼地伸出手，想要触摸这只蝴蝶。

"你好，美丽的蝴蝶。"小美轻声说道。

蝴蝶似乎听懂了小美的话，在她周围翩翩起舞，仿佛在回应她的问候。小美开心地笑了，她感觉这个下午变得特别美好。

就在这时，远处传来了悠扬的笛声，那声音如同天籁一般，让人心旷神怡。小美循着声音望去，看到一个少年正坐在花园的凉亭里吹奏着笛子。

少年的身影在阳光下显得格外优雅，他的笛声仿佛在诉说着一个美丽的故事。小美被这美妙的音乐深深吸引，她静静地站在那里，聆听着这动人的旋律。

当笛声结束时，少年转过头来，看到了小美。他们的目光在空中相遇，那一刻，仿佛时间都静止了。

"你好。"少年微笑着说道。

"你好。"小美也微笑着回应。

就这样，一个美丽的邂逅开始了。
"""
    
    # 确保目录存在
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    
    print(f"示例小说文件已创建: {file_path}")


def example_batch_processing():
    """批量处理示例"""
    logger = get_logger('example')
    
    # 创建任务调度器
    scheduler = TaskScheduler()
    scheduler.start()
    
    try:
        # 创建多个示例小说文件
        novel_files = []
        for i in range(3):
            file_path = f"data/input/novel_{i+1}.txt"
            create_example_novel(file_path)
            novel_files.append(file_path)
        
        # 批量提交任务
        task_ids = []
        for novel_file in novel_files:
            task_id = scheduler.submit_task('novel_video', novel_file)
            task_ids.append(task_id)
            logger.info(f"任务已提交: {task_id} - {novel_file}")
        
        # 监控所有任务
        import time
        while True:
            completed = 0
            failed = 0
            
            for task_id in task_ids:
                task = scheduler.get_task_status(task_id)
                if task['status'] == 'completed':
                    completed += 1
                elif task['status'] == 'failed':
                    failed += 1
            
            logger.info(f"任务状态 - 完成: {completed}, 失败: {failed}, 总数: {len(task_ids)}")
            
            if completed + failed == len(task_ids):
                break
            
            time.sleep(30)  # 等待30秒后再次检查
                
    finally:
        scheduler.stop()


def example_interactive_mode():
    """交互模式示例"""
    print("=== 小说视频生成系统交互模式示例 ===")
    print("这个示例展示了如何使用交互模式来管理系统")
    
    # 创建任务调度器
    scheduler = TaskScheduler()
    
    # 模拟用户交互
    print("\n1. 查看系统状态")
    stats = scheduler.get_scheduler_stats()
    print(f"   工作线程: {stats['total_workers']}")
    print(f"   队列大小: {stats['queue_size']}")
    
    print("\n2. 提交示例任务")
    novel_file = "data/input/interactive_example.txt"
    create_example_novel(novel_file)
    
    task_id = scheduler.submit_task('novel_video', novel_file)
    print(f"   任务已提交: {task_id}")
    
    print("\n3. 查看任务状态")
    task = scheduler.get_task_status(task_id)
    print(f"   任务状态: {task['status']}")
    print(f"   创建时间: {task['created_at']}")
    
    print("\n4. 列出所有任务")
    pending_tasks = scheduler.get_pending_tasks()
    print(f"   待处理任务: {len(pending_tasks)}")
    
    print("\n交互模式示例完成")


if __name__ == "__main__":
    print("小说视频生成系统使用示例")
    print("请选择要运行的示例:")
    print("1. 基本使用示例")
    print("2. 批量处理示例")
    print("3. 交互模式示例")
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == '1':
        example_basic_usage()
    elif choice == '2':
        example_batch_processing()
    elif choice == '3':
        example_interactive_mode()
    else:
        print("无效选择，运行基本使用示例")
        example_basic_usage() 