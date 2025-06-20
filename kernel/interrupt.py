"""
中断处理模块 - 处理系统中的各种中断
"""

import threading
from typing import Dict, List, Callable, Any
from enum import Enum

from utils.logger import Logger

class InterruptType(Enum):
    """中断类型枚举"""
    TIMER = "timer"
    I_O = "io"
    SYSTEM_CALL = "system_call"
    PAGE_FAULT = "page_fault"
    DIVIDE_BY_ZERO = "divide_by_zero"
    INVALID_OPCODE = "invalid_opcode"

class InterruptHandler:
    """中断处理器"""
    
    def __init__(self):
        """初始化中断处理器"""
        self.logger = Logger()
        self.interrupt_handlers: Dict[InterruptType, List[Callable]] = {}
        self.interrupt_queue = []
        self.interrupt_enabled = True
        self.lock = threading.Lock()
        
        # 初始化中断处理程序
        self._init_default_handlers()
    
    def _init_default_handlers(self):
        """初始化默认中断处理程序"""
        for interrupt_type in InterruptType:
            self.interrupt_handlers[interrupt_type] = []
    
    def register_handler(self, interrupt_type: InterruptType, handler: Callable):
        """注册中断处理程序"""
        with self.lock:
            if interrupt_type not in self.interrupt_handlers:
                self.interrupt_handlers[interrupt_type] = []
            self.interrupt_handlers[interrupt_type].append(handler)
            self.logger.info(f"注册中断处理程序: {interrupt_type.value}")
    
    def raise_interrupt(self, interrupt_type: InterruptType, data: Any = None):
        """触发中断"""
        with self.lock:
            interrupt = {
                'type': interrupt_type,
                'data': data,
                'timestamp': time.time()
            }
            self.interrupt_queue.append(interrupt)
            self.logger.log_system_event(f"中断触发: {interrupt_type.value}")
    
    def handle_interrupts(self):
        """处理中断队列"""
        with self.lock:
            while self.interrupt_queue and self.interrupt_enabled:
                interrupt = self.interrupt_queue.pop(0)
                self._process_interrupt(interrupt)
    
    def _process_interrupt(self, interrupt: Dict):
        """处理单个中断"""
        interrupt_type = interrupt['type']
        data = interrupt['data']
        
        if interrupt_type in self.interrupt_handlers:
            for handler in self.interrupt_handlers[interrupt_type]:
                try:
                    handler(data)
                except Exception as e:
                    self.logger.error(f"中断处理程序错误: {e}")
        else:
            self.logger.warning(f"未找到中断处理程序: {interrupt_type.value}")
    
    def enable_interrupts(self):
        """启用中断"""
        self.interrupt_enabled = True
        self.logger.info("中断已启用")
    
    def disable_interrupts(self):
        """禁用中断"""
        self.interrupt_enabled = False
        self.logger.info("中断已禁用")
    
    def get_interrupt_stats(self) -> Dict[str, int]:
        """获取中断统计信息"""
        stats = {}
        for interrupt_type in InterruptType:
            stats[interrupt_type.value] = len([
                i for i in self.interrupt_queue 
                if i['type'] == interrupt_type
            ])
        return stats

# 默认中断处理程序示例
def default_timer_handler(data):
    """默认定时器中断处理程序"""
    print(f"定时器中断: {data}")

def default_page_fault_handler(data):
    """默认缺页中断处理程序"""
    print(f"缺页中断: 地址 {data}")

def default_io_handler(data):
    """默认I/O中断处理程序"""
    print(f"I/O中断: {data}") 