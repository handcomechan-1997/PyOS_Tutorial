"""
系统调用模块 - 提供系统调用接口
"""

import threading
from typing import Dict, Any, Callable, Optional
from enum import Enum

from utils.logger import Logger

class SystemCallType(Enum):
    """系统调用类型枚举"""
    # 进程相关
    FORK = "fork"
    EXEC = "exec"
    EXIT = "exit"
    WAIT = "wait"
    GETPID = "getpid"
    
    # 文件相关
    OPEN = "open"
    READ = "read"
    WRITE = "write"
    CLOSE = "close"
    UNLINK = "unlink"
    
    # 内存相关
    BRK = "brk"
    MMAP = "mmap"
    MUNMAP = "munmap"
    
    # 其他
    TIME = "time"
    SLEEP = "sleep"
    GETCWD = "getcwd"
    CHDIR = "chdir"

class SystemCall:
    """系统调用处理器"""
    
    def __init__(self):
        """初始化系统调用处理器"""
        self.logger = Logger()
        self.system_calls: Dict[SystemCallType, Callable] = {}
        self.call_count = 0
        self.lock = threading.Lock()
        
        # 初始化系统调用
        self._init_system_calls()
    
    def _init_system_calls(self):
        """初始化系统调用"""
        # 注册默认的系统调用处理程序
        self.register_system_call(SystemCallType.GETPID, self._getpid)
        self.register_system_call(SystemCallType.TIME, self._time)
        self.register_system_call(SystemCallType.SLEEP, self._sleep)
    
    def register_system_call(self, call_type: SystemCallType, handler: Callable):
        """注册系统调用处理程序"""
        with self.lock:
            self.system_calls[call_type] = handler
            self.logger.info(f"注册系统调用: {call_type.value}")
    
    def call(self, call_type: SystemCallType, *args, **kwargs) -> Any:
        """执行系统调用"""
        with self.lock:
            self.call_count += 1
            
            if call_type in self.system_calls:
                try:
                    result = self.system_calls[call_type](*args, **kwargs)
                    self.logger.log_system_event(f"系统调用成功: {call_type.value}")
                    return result
                except Exception as e:
                    self.logger.error(f"系统调用错误 {call_type.value}: {e}")
                    raise
            else:
                error_msg = f"未实现的系统调用: {call_type.value}"
                self.logger.error(error_msg)
                raise NotImplementedError(error_msg)
    
    def get_call_count(self) -> int:
        """获取系统调用次数"""
        return self.call_count
    
    def get_available_calls(self) -> list:
        """获取可用的系统调用列表"""
        return [call_type.value for call_type in self.system_calls.keys()]
    
    # 默认系统调用实现
    def _getpid(self) -> int:
        """获取当前进程ID"""
        # TODO: 实现获取当前进程ID的逻辑
        return 1
    
    def _time(self) -> float:
        """获取当前时间"""
        import time
        return time.time()
    
    def _sleep(self, seconds: float):
        """进程睡眠"""
        import time
        time.sleep(seconds)

# 系统调用接口函数
def syscall(call_type: SystemCallType, *args, **kwargs) -> Any:
    """系统调用接口函数"""
    # 这里需要获取全局的系统调用处理器实例
    # 在实际实现中，这通常通过全局变量或单例模式实现
    pass

# 便捷的系统调用函数
def sys_fork():
    """创建新进程"""
    return syscall(SystemCallType.FORK)

def sys_exec(path: str, args: list = None):
    """执行程序"""
    return syscall(SystemCallType.EXEC, path, args or [])

def sys_exit(status: int = 0):
    """退出进程"""
    return syscall(SystemCallType.EXIT, status)

def sys_getpid() -> int:
    """获取进程ID"""
    return syscall(SystemCallType.GETPID)

def sys_open(path: str, mode: str = "r"):
    """打开文件"""
    return syscall(SystemCallType.OPEN, path, mode)

def sys_read(fd: int, size: int) -> str:
    """读取文件"""
    return syscall(SystemCallType.READ, fd, size)

def sys_write(fd: int, data: str) -> int:
    """写入文件"""
    return syscall(SystemCallType.WRITE, fd, data)

def sys_close(fd: int):
    """关闭文件"""
    return syscall(SystemCallType.CLOSE, fd)

def sys_time() -> float:
    """获取当前时间"""
    return syscall(SystemCallType.TIME)

def sys_sleep(seconds: float):
    """进程睡眠"""
    return syscall(SystemCallType.SLEEP, seconds) 