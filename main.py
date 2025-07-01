#!/usr/bin/env python3
"""
小说视频生成系统主程序
Novel Video Generator System Main Program
"""

import sys
import os
import argparse
from pathlib import Path
from src.core import config, get_logger
from src.scheduler import TaskScheduler


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='小说视频生成系统')
    parser.add_argument('--input', '-i', help='输入小说文件路径')
    parser.add_argument('--output', '-o', help='输出目录路径')
    parser.add_argument('--config', '-c', default='config/config.yaml', help='配置文件路径')
    parser.add_argument('--daemon', '-d', action='store_true', help='以守护进程模式运行')
    parser.add_argument('--status', '-s', action='store_true', help='查看系统状态')
    parser.add_argument('--list-tasks', '-l', action='store_true', help='列出所有任务')
    parser.add_argument('--task-id', help='指定任务ID')
    parser.add_argument('--retry', action='store_true', help='重试失败的任务')
    parser.add_argument('--cancel', action='store_true', help='取消任务')
    
    args = parser.parse_args()
    
    # 初始化日志
    logger = get_logger('main')
    logger.info("小说视频生成系统启动")
    
    try:
        # 创建任务调度器
        scheduler = TaskScheduler()
        
        if args.daemon:
            # 守护进程模式
            run_daemon_mode(scheduler)
        elif args.status:
            # 查看系统状态
            show_system_status(scheduler)
        elif args.list_tasks:
            # 列出任务
            list_tasks(scheduler)
        elif args.task_id:
            if args.retry:
                # 重试任务
                retry_task(scheduler, args.task_id)
            elif args.cancel:
                # 取消任务
                cancel_task(scheduler, args.task_id)
            else:
                # 查看任务状态
                show_task_status(scheduler, args.task_id)
        elif args.input:
            # 提交新任务
            submit_task(scheduler, args.input, args.output)
        else:
            # 交互模式
            run_interactive_mode(scheduler)
            
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭系统...")
        scheduler.stop()
        logger.info("系统已关闭")
    except Exception as e:
        logger.error(f"系统运行错误: {str(e)}")
        sys.exit(1)


def run_daemon_mode(scheduler):
    """守护进程模式"""
    logger = get_logger('main')
    logger.info("启动守护进程模式")
    
    # 启动调度器
    scheduler.start()
    
    try:
        # 保持运行
        while True:
            import time
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止守护进程...")
        scheduler.stop()


def submit_task(scheduler, input_file, output_dir=None):
    """提交新任务"""
    logger = get_logger('main')
    
    # 检查输入文件
    if not os.path.exists(input_file):
        logger.error(f"输入文件不存在: {input_file}")
        return
    
    # 设置输出目录
    if output_dir:
        config.set('paths.output_dir', output_dir)
    
    try:
        # 提交任务
        task_id = scheduler.submit_task('novel_video', input_file)
        logger.info(f"任务已提交 | ID: {task_id}")
        logger.info(f"输入文件: {input_file}")
        logger.info(f"输出目录: {config.get('paths.output_dir')}")
        
        # 显示任务状态
        show_task_status(scheduler, task_id)
        
    except Exception as e:
        logger.error(f"提交任务失败: {str(e)}")


def show_system_status(scheduler):
    """显示系统状态"""
    logger = get_logger('main')
    
    stats = scheduler.get_scheduler_stats()
    
    print("\n=== 系统状态 ===")
    print(f"工作线程总数: {stats['total_workers']}")
    print(f"活跃工作线程: {stats['active_workers']}")
    print(f"队列大小: {stats['queue_size']}")
    print(f"运行中任务: {stats['running_tasks']}")
    print(f"待处理任务: {stats['pending_tasks']}")
    print(f"已完成任务: {stats['completed_tasks']}")
    print(f"失败任务: {stats['failed_tasks']}")
    print("===============\n")


def list_tasks(scheduler):
    """列出所有任务"""
    logger = get_logger('main')
    
    print("\n=== 任务列表 ===")
    
    # 待处理任务
    pending_tasks = scheduler.get_pending_tasks()
    if pending_tasks:
        print(f"\n待处理任务 ({len(pending_tasks)}):")
        for task in pending_tasks:
            print(f"  {task['id']} - {task['task_type']} - {task['created_at']}")
    
    # 运行中任务
    running_tasks = scheduler.get_running_tasks()
    if running_tasks:
        print(f"\n运行中任务 ({len(running_tasks)}):")
        for task in running_tasks:
            progress = task.get('progress', 0) * 100
            print(f"  {task['id']} - {task['task_type']} - 进度: {progress:.1f}%")
    
    # 已完成任务
    completed_tasks = scheduler.get_completed_tasks()
    if completed_tasks:
        print(f"\n已完成任务 ({len(completed_tasks)}):")
        for task in completed_tasks[:5]:  # 只显示最近5个
            print(f"  {task['id']} - {task['task_type']} - {task['completed_at']}")
    
    # 失败任务
    failed_tasks = scheduler.get_failed_tasks()
    if failed_tasks:
        print(f"\n失败任务 ({len(failed_tasks)}):")
        for task in failed_tasks:
            error = task.get('error_message', '未知错误')
            print(f"  {task['id']} - {task['task_type']} - 错误: {error}")
    
    print("===============\n")


def show_task_status(scheduler, task_id):
    """显示任务状态"""
    logger = get_logger('main')
    
    task = scheduler.get_task_status(task_id)
    if not task:
        logger.error(f"任务不存在: {task_id}")
        return
    
    print(f"\n=== 任务状态: {task_id} ===")
    print(f"类型: {task['task_type']}")
    print(f"状态: {task['status']}")
    print(f"创建时间: {task['created_at']}")
    
    if task['started_at']:
        print(f"开始时间: {task['started_at']}")
    
    if task['completed_at']:
        print(f"完成时间: {task['completed_at']}")
    
    if task['progress'] is not None:
        progress = task['progress'] * 100
        print(f"进度: {progress:.1f}%")
    
    if task['output_file']:
        print(f"输出文件: {task['output_file']}")
    
    if task['error_message']:
        print(f"错误信息: {task['error_message']}")
    
    print("==================\n")


def retry_task(scheduler, task_id):
    """重试任务"""
    logger = get_logger('main')
    
    if scheduler.retry_task(task_id):
        logger.info(f"任务重试成功: {task_id}")
        show_task_status(scheduler, task_id)
    else:
        logger.error(f"任务重试失败: {task_id}")


def cancel_task(scheduler, task_id):
    """取消任务"""
    logger = get_logger('main')
    
    if scheduler.cancel_task(task_id):
        logger.info(f"任务取消成功: {task_id}")
        show_task_status(scheduler, task_id)
    else:
        logger.error(f"任务取消失败: {task_id}")


def run_interactive_mode(scheduler):
    """交互模式"""
    logger = get_logger('main')
    logger.info("启动交互模式")
    
    print("\n=== 小说视频生成系统 ===")
    print("1. 提交新任务")
    print("2. 查看系统状态")
    print("3. 列出所有任务")
    print("4. 查看任务状态")
    print("5. 重试失败任务")
    print("6. 取消任务")
    print("0. 退出")
    print("======================\n")
    
    while True:
        try:
            choice = input("请选择操作 (0-6): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                input_file = input("请输入小说文件路径: ").strip()
                if input_file:
                    submit_task(scheduler, input_file)
            elif choice == '2':
                show_system_status(scheduler)
            elif choice == '3':
                list_tasks(scheduler)
            elif choice == '4':
                task_id = input("请输入任务ID: ").strip()
                if task_id:
                    show_task_status(scheduler, task_id)
            elif choice == '5':
                task_id = input("请输入任务ID: ").strip()
                if task_id:
                    retry_task(scheduler, task_id)
            elif choice == '6':
                task_id = input("请输入任务ID: ").strip()
                if task_id:
                    cancel_task(scheduler, task_id)
            else:
                print("无效选择，请重新输入")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"交互模式错误: {str(e)}")
    
    logger.info("交互模式结束")


if __name__ == "__main__":
    main() 