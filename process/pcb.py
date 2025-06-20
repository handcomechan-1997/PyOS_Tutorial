"""
进程控制块 (PCB) - 存储进程的所有控制信息
"""

import time
from typing import Dict, Any, Optional

class PCB:
    """进程控制块"""
    
    def __init__(self, pid: int, name: str, priority: int = 0):
        """初始化PCB"""
        # 进程标识信息
        self.pid = pid
        self.name = name
        self.priority = priority
        
        # 进程状态信息
        self.state = "new"
        self.cpu_state = {}  # CPU寄存器状态
        
        # 进程调度信息
        self.priority = priority
        self.scheduling_info = {
            'arrival_time': time.time(),
            'burst_time': 0,
            'waiting_time': 0,
            'turnaround_time': 0
        }
        
        # 内存管理信息
        self.memory_info = {
            'base_address': 0,
            'limit': 0,
            'page_table': {},
            'memory_usage': 0
        }
        
        # 文件管理信息
        self.file_info = {
            'open_files': [],
            'working_directory': '/'
        }
        
        # 其他信息
        self.parent_pid = None
        self.child_pids = []
        self.creation_time = time.time()
        self.last_access_time = time.time()
    
    def update_state(self, new_state: str):
        """更新进程状态"""
        self.state = new_state
        self.last_access_time = time.time()
    
    def update_cpu_state(self, registers: Dict[str, Any]):
        """更新CPU状态"""
        self.cpu_state.update(registers)
    
    def add_child(self, child_pid: int):
        """添加子进程"""
        self.child_pids.append(child_pid)
    
    def remove_child(self, child_pid: int):
        """移除子进程"""
        if child_pid in self.child_pids:
            self.child_pids.remove(child_pid)
    
    def get_info(self) -> Dict[str, Any]:
        """获取PCB信息"""
        return {
            'pid': self.pid,
            'name': self.name,
            'state': self.state,
            'priority': self.priority,
            'parent_pid': self.parent_pid,
            'child_pids': self.child_pids.copy(),
            'creation_time': self.creation_time,
            'last_access_time': self.last_access_time,
            'scheduling_info': self.scheduling_info.copy(),
            'memory_info': self.memory_info.copy(),
            'file_info': self.file_info.copy()
        }
    
    def __str__(self) -> str:
        return f"PCB(pid={self.pid}, name='{self.name}', state={self.state})"
    
    def __repr__(self) -> str:
        return self.__str__() 