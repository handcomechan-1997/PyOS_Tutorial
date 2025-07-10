"""
日志系统 - 提供系统日志记录功能
"""

import logging
import os
import time
import threading
from datetime import datetime
from typing import Optional

class Logger:
    """系统日志记录器"""
    
    def __init__(self, name: str = "PyOS", level: int = logging.INFO):
        """初始化日志记录器"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self._handlers_initialized = False
        self._init_lock = threading.Lock()
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_console_handler()  # 先只设置控制台处理器
    
    def _setup_console_handler(self):
        """设置控制台处理器"""
        if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) 
                  for h in self.logger.handlers):
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 设置格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            # 添加处理器
            self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """延迟设置文件处理器"""
        with self._init_lock:
            if self._handlers_initialized:
                return
            
            try:
                # 创建logs目录
                log_dir = "logs"
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                # 文件处理器
                log_file = os.path.join(log_dir, f"pyos_{datetime.now().strftime('%Y%m%d')}.log")
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                
                # 设置格式
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(formatter)
                
                # 添加处理器
                self.logger.addHandler(file_handler)
                self._handlers_initialized = True
                
            except Exception as e:
                # 如果文件处理器设置失败，只使用控制台
                pass
    
    def _ensure_file_handler(self):
        """确保文件处理器已初始化"""
        if not self._handlers_initialized:
            self._setup_file_handler()
    
    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录一般信息"""
        self.logger.info(message)
        # 延迟初始化文件处理器
        if not self._handlers_initialized:
            threading.Thread(target=self._setup_file_handler, daemon=True).start()
    
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
        
        # 对于文件系统事件，确保文件处理器已初始化
        self._ensure_file_handler()
        self.info(message) 