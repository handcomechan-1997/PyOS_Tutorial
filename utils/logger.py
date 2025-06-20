"""
日志系统 - 提供系统日志记录功能
"""

import logging
import os
import time
from datetime import datetime
from typing import Optional

class Logger:
    """系统日志记录器"""
    
    def __init__(self, name: str = "PyOS", level: int = logging.INFO):
        """初始化日志记录器"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 创建logs目录
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 文件处理器
        log_file = os.path.join(log_dir, f"pyos_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录一般信息"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告信息"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误信息"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """记录严重错误信息"""
        self.logger.critical(message)
    
    def log_system_event(self, event: str, details: Optional[str] = None):
        """记录系统事件"""
        message = f"SYSTEM_EVENT: {event}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def log_process_event(self, pid: int, event: str, details: Optional[str] = None):
        """记录进程事件"""
        message = f"PROCESS[{pid}]: {event}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def log_memory_event(self, event: str, details: Optional[str] = None):
        """记录内存事件"""
        message = f"MEMORY: {event}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def log_file_event(self, event: str, details: Optional[str] = None):
        """记录文件系统事件"""
        message = f"FILESYSTEM: {event}"
        if details:
            message += f" - {details}"
        self.info(message) 