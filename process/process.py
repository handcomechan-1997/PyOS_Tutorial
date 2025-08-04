"""
进程类 - 表示操作系统中的一个进程
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from enum import Enum

from .pcb import PCB
from utils.logger import Logger

class ProcessState(Enum):
    """进程状态枚举"""
    NEW = "new"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    TERMINATED = "terminated"

class Process:
    """进程类"""

    # 通过类变量维护下一个可用的 PID，确保每个进程拥有唯一标识
    _next_pid = 1
    
    def __init__(self, name: str, priority: int = 0, target: Optional[Callable] = None):
        """初始化进程"""
        self.pid = Process._next_pid
        Process._next_pid += 1
        
        self.name = name
        self.priority = priority
        self.target = target
        self.state = ProcessState.NEW
        
        # 进程控制块
        self.pcb = PCB(self.pid, self.name, self.priority)
        
        # 进程资源
        self.memory_usage = 0
        self.cpu_time = 0.0
        self.start_time = None
        self.end_time = None
        
        # 进程数据
        self.data: Dict[str, Any] = {}
        self.return_value = None
        
        # 同步
        self.lock = threading.Lock()
        
        self.logger = Logger()
        self.logger.log_process_event(self.pid, f"created - {name}")
    
    def execute(self, time_quantum: float):
        """执行进程

        根据进程的类型模拟执行：如果提供了 ``target`` 函数则直接调用；
        否则通过 ``sleep`` 模拟 CPU 计算。``time_quantum`` 表示允许运行的时间片长度。
        """
        with self.lock:
            if self.state != ProcessState.RUNNING:
                return

            if self.start_time is None:
                self.start_time = time.time()  # 记录第一次执行的时间

            # 模拟进程执行
            if self.target:
                try:
                    # 执行目标函数
                    self.return_value = self.target()
                    self.state = ProcessState.TERMINATED
                    self.end_time = time.time()
                    self.logger.log_process_event(self.pid, "completed successfully")
                except Exception as e:
                    self.logger.error(f"进程执行错误 PID {self.pid}: {e}")
                    self.state = ProcessState.TERMINATED
                    self.end_time = time.time()
            else:
                # 模拟 CPU 密集型任务
                time.sleep(min(time_quantum, 0.1))
                self.cpu_time += time_quantum

                # 简单地假设运行 5 秒后进程完成
                if self.cpu_time >= 5.0:  # 5秒后完成
                    self.state = ProcessState.TERMINATED
                    self.end_time = time.time()
                    self.logger.log_process_event(self.pid, "completed")
    
    def suspend(self):
        """挂起进程"""
        with self.lock:
            if self.state == ProcessState.RUNNING:
                self.state = ProcessState.WAITING
                self.logger.log_process_event(self.pid, "suspended")
    
    def resume(self):
        """恢复进程"""
        with self.lock:
            if self.state == ProcessState.WAITING:
                self.state = ProcessState.READY
                self.logger.log_process_event(self.pid, "resumed")
    
    def terminate(self):
        """终止进程"""
        with self.lock:
            self.state = ProcessState.TERMINATED
            self.end_time = time.time()
            self.logger.log_process_event(self.pid, "terminated")
    
    def get_runtime(self) -> float:
        """获取进程运行时间"""
        if self.start_time is None:
            return 0.0
        end_time = self.end_time or time.time()
        return end_time - self.start_time
    
    def get_info(self) -> Dict[str, Any]:
        """获取进程信息"""
        return {
            'pid': self.pid,
            'name': self.name,
            'state': self.state.value,
            'priority': self.priority,
            'cpu_time': self.cpu_time,
            'memory_usage': self.memory_usage,
            'runtime': self.get_runtime(),
            'return_value': self.return_value
        }
    
    def __str__(self) -> str:
        return f"Process(pid={self.pid}, name='{self.name}', state={self.state.value})"
    
    def __repr__(self) -> str:
        return self.__str__() 