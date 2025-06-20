"""
进程管理器 - 负责进程的创建、销毁和管理
"""

import threading
from typing import Dict, List, Optional, Callable
from collections import defaultdict

from .process import Process
from .process_table import ProcessTable
from kernel.scheduler import Scheduler
from kernel.memory_manager import MemoryManager
from utils.logger import Logger

class ProcessManager:
    """进程管理器"""
    
    def __init__(self):
        """初始化进程管理器"""
        self.logger = Logger()
        self.process_table = ProcessTable()
        self.scheduler: Optional[Scheduler] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.lock = threading.Lock()
        
        # 进程统计
        self.stats = {
            'total_created': 0,
            'total_terminated': 0,
            'current_active': 0
        }
    
    def initialize(self, scheduler: Scheduler, memory_manager: MemoryManager):
        """初始化进程管理器"""
        self.scheduler = scheduler
        self.memory_manager = memory_manager
        self.logger.info("进程管理器初始化完成")
    
    def create_process(self, name: str, priority: int = 0, target: Optional[Callable] = None) -> Process:
        """创建新进程"""
        with self.lock:
            # 创建进程
            process = Process(name, priority, target)
            
            # 添加到进程表
            self.process_table.add_process(process)
            
            # 分配内存
            if self.memory_manager:
                memory_size = 1024  # 默认1KB内存
                allocated = self.memory_manager.allocate_memory(process.pid, memory_size)
                if allocated:
                    process.memory_usage = memory_size
                    process.pcb.memory_info['memory_usage'] = memory_size
            
            # 添加到调度器
            if self.scheduler:
                self.scheduler.add_process(process)
            
            # 更新统计
            self.stats['total_created'] += 1
            self.stats['current_active'] += 1
            
            self.logger.log_process_event(process.pid, f"created by process manager - {name}")
            return process
    
    def terminate_process(self, pid: int) -> bool:
        """终止进程"""
        with self.lock:
            process = self.process_table.get_process(pid)
            if not process:
                self.logger.warning(f"进程不存在: {pid}")
                return False
            
            # 终止进程
            process.terminate()
            
            # 从调度器移除
            if self.scheduler:
                self.scheduler.remove_process(pid)
            
            # 释放内存
            if self.memory_manager:
                self.memory_manager.free_memory(pid)
            
            # 从进程表移除
            self.process_table.remove_process(pid)
            
            # 更新统计
            self.stats['total_terminated'] += 1
            self.stats['current_active'] -= 1
            
            self.logger.log_process_event(pid, "terminated by process manager")
            return True
    
    def get_process(self, pid: int) -> Optional[Process]:
        """获取进程"""
        return self.process_table.get_process(pid)
    
    def get_all_processes(self) -> List[Process]:
        """获取所有进程"""
        return self.process_table.get_all_processes()
    
    def get_process_count(self) -> int:
        """获取进程数量"""
        return self.process_table.get_process_count()
    
    def get_process_stats(self) -> Dict[str, int]:
        """获取进程统计信息"""
        return self.stats.copy()
    
    def get_process_by_name(self, name: str) -> List[Process]:
        """根据名称获取进程"""
        return self.process_table.get_processes_by_name(name)
    
    def kill_all_processes(self):
        """终止所有进程"""
        with self.lock:
            processes = self.get_all_processes()
            for process in processes:
                self.terminate_process(process.pid)
            self.logger.info("所有进程已终止")
    
    def cleanup(self):
        """清理进程管理器"""
        with self.lock:
            self.kill_all_processes()
            self.process_table.clear()
            self.logger.info("进程管理器清理完成")
    
    def get_process_tree(self) -> Dict[int, List[int]]:
        """获取进程树"""
        tree = defaultdict(list)
        processes = self.get_all_processes()
        
        for process in processes:
            if process.pcb.parent_pid is not None:
                tree[process.pcb.parent_pid].append(process.pid)
        
        return dict(tree)
    
    def print_process_info(self):
        """打印进程信息"""
        processes = self.get_all_processes()
        print(f"\n进程信息 (共 {len(processes)} 个进程):")
        print("-" * 80)
        print(f"{'PID':<6} {'名称':<15} {'状态':<12} {'优先级':<8} {'CPU时间':<10} {'内存':<8}")
        print("-" * 80)
        
        for process in processes:
            info = process.get_info()
            print(f"{info['pid']:<6} {info['name']:<15} {info['state']:<12} "
                  f"{info['priority']:<8} {info['cpu_time']:<10.2f} {info['memory_usage']:<8}")
        
        print("-" * 80)
        print(f"统计: 已创建 {self.stats['total_created']} 个, "
              f"已终止 {self.stats['total_terminated']} 个, "
              f"当前活跃 {self.stats['current_active']} 个") 