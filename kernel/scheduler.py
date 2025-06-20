"""
进程调度器 - 负责进程的调度和执行
"""

import threading
import time
import queue
from typing import List, Optional
from enum import Enum

from process.process import Process
from utils.logger import Logger

class ProcessState(Enum):
    """进程状态枚举"""
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    TERMINATED = "terminated"

class Scheduler:
    """进程调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.logger = Logger()
        self.running = False
        self.ready_queue = queue.Queue()
        self.waiting_queue = queue.Queue()
        self.current_process: Optional[Process] = None
        self.processes: List[Process] = []
        self.scheduler_thread: Optional[threading.Thread] = None
        self.time_quantum = 1.0  # 时间片（秒）
        self.cpu_usage = 0.0
        self.total_cpu_time = 0.0
        self.idle_time = 0.0
        
    def start(self):
        """启动调度器"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            self.logger.info("进程调度器启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
        self.logger.info("进程调度器停止")
    
    def add_process(self, process: Process):
        """添加进程到调度队列"""
        self.processes.append(process)
        self.ready_queue.put(process)
        self.logger.log_process_event(process.pid, "added to scheduler")
    
    def remove_process(self, pid: int):
        """从调度器中移除进程"""
        for i, process in enumerate(self.processes):
            if process.pid == pid:
                self.processes.pop(i)
                self.logger.log_process_event(pid, "removed from scheduler")
                break
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.running:
            try:
                if not self.ready_queue.empty():
                    # 获取下一个进程
                    process = self.ready_queue.get()
                    self._execute_process(process)
                else:
                    # 没有就绪进程，CPU空闲
                    time.sleep(0.1)
                    self.idle_time += 0.1
                    
            except Exception as e:
                self.logger.error(f"调度器错误: {e}")
    
    def _execute_process(self, process: Process):
        """执行进程"""
        self.current_process = process
        process.state = ProcessState.RUNNING
        self.logger.log_process_event(process.pid, "started execution")
        
        start_time = time.time()
        
        try:
            # 模拟进程执行
            process.execute(self.time_quantum)
            
            # 更新CPU使用率
            execution_time = time.time() - start_time
            self.total_cpu_time += execution_time
            
            # 如果进程还未完成，重新加入就绪队列
            if process.state != ProcessState.TERMINATED:
                process.state = ProcessState.READY
                self.ready_queue.put(process)
                self.logger.log_process_event(process.pid, "returned to ready queue")
            else:
                self.logger.log_process_event(process.pid, "completed")
                
        except Exception as e:
            self.logger.error(f"进程执行错误 PID {process.pid}: {e}")
            process.state = ProcessState.TERMINATED
        
        self.current_process = None
    
    def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        total_time = self.total_cpu_time + self.idle_time
        if total_time > 0:
            return (self.total_cpu_time / total_time) * 100
        return 0.0
    
    def get_process_count(self) -> int:
        """获取进程数量"""
        return len(self.processes)
    
    def get_current_process(self) -> Optional[Process]:
        """获取当前运行的进程"""
        return self.current_process
    
    def get_ready_queue_size(self) -> int:
        """获取就绪队列大小"""
        return self.ready_queue.qsize()
    
    def get_waiting_queue_size(self) -> int:
        """获取等待队列大小"""
        return self.waiting_queue.qsize() 