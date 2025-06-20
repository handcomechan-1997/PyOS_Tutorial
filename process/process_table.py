"""
进程表 - 管理系统中所有进程的集合
"""

import threading
from typing import Dict, List, Optional

from .process import Process

class ProcessTable:
    """进程表"""
    
    def __init__(self):
        """初始化进程表"""
        self.processes: Dict[int, Process] = {}
        self.lock = threading.Lock()
    
    def add_process(self, process: Process):
        """添加进程到进程表"""
        with self.lock:
            self.processes[process.pid] = process
    
    def remove_process(self, pid: int) -> bool:
        """从进程表移除进程"""
        with self.lock:
            if pid in self.processes:
                del self.processes[pid]
                return True
            return False
    
    def get_process(self, pid: int) -> Optional[Process]:
        """根据PID获取进程"""
        with self.lock:
            return self.processes.get(pid)
    
    def get_all_processes(self) -> List[Process]:
        """获取所有进程"""
        with self.lock:
            return list(self.processes.values())
    
    def get_process_count(self) -> int:
        """获取进程数量"""
        with self.lock:
            return len(self.processes)
    
    def get_processes_by_name(self, name: str) -> List[Process]:
        """根据名称获取进程"""
        with self.lock:
            return [p for p in self.processes.values() if p.name == name]
    
    def get_processes_by_state(self, state: str) -> List[Process]:
        """根据状态获取进程"""
        with self.lock:
            return [p for p in self.processes.values() if p.state.value == state]
    
    def clear(self):
        """清空进程表"""
        with self.lock:
            self.processes.clear()
    
    def exists(self, pid: int) -> bool:
        """检查进程是否存在"""
        with self.lock:
            return pid in self.processes 